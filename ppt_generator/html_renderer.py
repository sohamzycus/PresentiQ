"""
HTML-to-Image slide renderer.

Uses an LLM (Claude) to generate self-contained HTML/CSS for each slide,
then screenshots it with Playwright to produce a PNG.
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    logger.warning("playwright not installed — run: pip install playwright && playwright install chromium")


SLIDE_WIDTH = 1920
SLIDE_HEIGHT = 1080


HTML_SYSTEM_PROMPT = """You are an expert presentation designer who produces pixel-perfect HTML/CSS slides.

TASK: Generate a single, self-contained HTML file that renders as a 1920×1080 presentation slide.

HARD RULES — violating any of these is a failure:
1. Output ONLY the raw HTML. No markdown fences, no explanation, no commentary.
2. The <body> must be exactly 1920px × 1080px with overflow:hidden.
3. All styles must be inlined in a <style> tag — no external resources.
4. Use web-safe fonts: "Inter", "Helvetica Neue", Arial, sans-serif.
   Load Inter from Google Fonts: <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
   For multilingual support, also load Noto Sans: <link href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@300;400;500;700;900&display=swap" rel="stylesheet">
5. No JavaScript. No images via URL (use CSS gradients, shapes, SVG inline instead).
6. Text must be crisp and highly legible — large font sizes, strong contrast.
7. The design must look like a premium, professionally designed presentation slide — not a web page.
8. Use generous whitespace, clear visual hierarchy, and modern design principles.
9. For icons/visuals, use inline SVG or CSS shapes/gradients — make them look polished.
10. Page number must appear at bottom-right: small, subtle, gray (#999), format "N / M".

DESIGN QUALITY EXPECTATIONS:
- Think Apple Keynote / high-end consulting deck quality
- Bold typography with clear hierarchy (title 48-72px, subtitle 24-36px, body 18-24px)
- Sophisticated color usage — gradients, accent colors, not flat boring backgrounds
- Visual elements: decorative shapes, subtle patterns, accent lines, icon grids
- Professional spacing: generous padding (60-100px from edges), balanced layout
- Modern design trends: glassmorphism, subtle shadows, rounded corners, gradient accents"""


class ImageGenerationParams(BaseModel):
    """Kept for API compatibility with the rest of the codebase."""
    prompt: str = Field(description="Slide content/style description for the LLM")
    ratio: str = Field(default="16:9", description="Aspect ratio")
    output_dir: str = Field(default="output/images", description="Output directory")
    context_variables: Dict = Field(default_factory=dict, exclude=True)


class ImageGenerationTool:
    """
    Drop-in replacement for the Gemini-based ImageGenerationTool.

    Generates slide images by:
      1. Asking Claude to produce self-contained HTML/CSS
      2. Rendering the HTML with Playwright (headless Chromium) → PNG
    """

    def __init__(self, llm_client=None):
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Install playwright: pip install playwright && playwright install chromium")
        self.llm_client = llm_client
        self._browser = None
        self._playwright = None

    async def _ensure_browser(self):
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)

    async def close(self):
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    # ------------------------------------------------------------------
    # Public API — matches the old Gemini-based interface
    # ------------------------------------------------------------------

    async def gemini_generate(self, params: ImageGenerationParams) -> Dict[str, Any]:
        """Main entry point — called by SlideGenerator and BatchImageGenerator."""
        return await self._generate(params)

    async def __call__(self, params: ImageGenerationParams) -> Dict[str, Any]:
        logger.info(f"Generating slide image via HTML renderer …")
        return await self._generate(params)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _generate(self, params: ImageGenerationParams) -> Dict[str, Any]:
        if self.llm_client is None:
            return {"success": False, "error": "No LLM client configured for HTML slide generation"}

        try:
            html = await self._generate_html(params.prompt)
            if not html:
                return {"success": False, "error": "LLM returned empty HTML"}

            save_result = await self._render_and_save(html, params.output_dir)
            if save_result is None:
                return {"success": False, "error": "Playwright screenshot failed"}

            if params.context_variables is not None:
                image_key = f"image_{uuid.uuid4().hex[:8]}"
                params.context_variables[image_key] = {
                    "file_path": save_result["file_path"],
                    "filename": save_result["filename"],
                    "rephraser_result": params.prompt,
                    "aspect_ratio": params.ratio,
                    "mime_type": "image/png",
                    "file_size": save_result["size"],
                }

            return {
                "success": True,
                "file_path": save_result["file_path"],
                "filename": save_result["filename"],
                "mime_type": "image/png",
                "size": save_result["size"],
                "prompt_used": params.prompt[:200],
                "model": "html_renderer",
                "aspect_ratio": params.ratio,
            }

        except Exception as e:
            logger.error(f"HTML slide generation failed: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_html(self, slide_prompt: str) -> Optional[str]:
        """Ask the LLM to produce self-contained HTML for the slide."""
        model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-global")

        response = await asyncio.to_thread(
            self.llm_client.chat_completions_create,
            model=model,
            messages=[
                {"role": "system", "content": HTML_SYSTEM_PROMPT},
                {"role": "user", "content": slide_prompt},
            ],
            temperature=0.7,
            max_tokens=8000,
        )

        content = response["choices"][0]["message"]["content"]

        # Strip markdown fences if the LLM wrapped its output
        content = content.strip()
        if content.startswith("```"):
            first_newline = content.index("\n")
            content = content[first_newline + 1:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        if not content.lower().startswith("<!doctype") and not content.lower().startswith("<html"):
            html_start = content.lower().find("<!doctype")
            if html_start == -1:
                html_start = content.lower().find("<html")
            if html_start != -1:
                content = content[html_start:]

        return content if content else None

    async def _render_and_save(
        self, html: str, output_dir: str, key_prefix: str = "ppt_bg"
    ) -> Optional[Dict]:
        """Render HTML in headless Chromium and save a screenshot."""
        try:
            await self._ensure_browser()
            page = await self._browser.new_page(
                viewport={"width": SLIDE_WIDTH, "height": SLIDE_HEIGHT},
                device_scale_factor=1,
            )

            await page.set_content(html, wait_until="networkidle", timeout=15000)
            # Small extra wait for fonts to settle
            await page.wait_for_timeout(500)

            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            filename = f"{key_prefix}_{timestamp}_{unique_id}.png"
            filepath = os.path.join(output_dir, filename)

            await page.screenshot(path=filepath, full_page=False)
            await page.close()

            file_size = os.path.getsize(filepath)
            logger.info(f"Slide image saved: {filepath} ({file_size} bytes)")

            return {"file_path": filepath, "filename": filename, "size": file_size}

        except Exception as e:
            logger.error(f"Render/save failed: {e}")
            return None
