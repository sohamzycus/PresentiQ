"""
PPT slide generator — HTML/CSS rendering via LLM + Playwright.

Each slide is generated as self-contained HTML by the LLM, then
screenshotted to a PNG with headless Chromium.
"""

import json
import logging
import os
from typing import Dict

from .html_renderer import ImageGenerationTool, ImageGenerationParams  # noqa: F401

logger = logging.getLogger(__name__)


class SlideGenerator:
    """
    Generates full-page PPT slide images.

    Uses the HTML-based ImageGenerationTool (LLM → HTML → Playwright → PNG).
    """

    def __init__(self, image_generator: ImageGenerationTool):
        self.image_generator = image_generator
        self.template_styles = self._init_template_styles()

    async def generate_slide_as_image(
        self,
        slide_info: Dict,
        slide_index: int,
        outline_result: dict,
        style_requirements: str,
        output_dir: str,
        style_hints: dict = None,
    ) -> Dict:
        """
        Generate a single slide as a PNG image.

        Args:
            slide_info: Current slide metadata from the outline.
            slide_index: Zero-based slide index.
            outline_result: Full outline dict.
            style_requirements: User-provided style description.
            output_dir: Where to save output files.
            style_hints: Optional preset style hints from the YAML template.

        Returns:
            Dict with ``success``, ``file_path``, ``filename``, etc.
        """
        total_slides = len(outline_result.get("slides", []))
        slide_id = slide_info.get("slide_id", f"slide_{slide_index + 1}")
        logger.info(f"Generating slide {slide_index + 1}/{total_slides} ({slide_id}) …")

        try:
            prompt = self._build_slide_prompt(
                slide_info, slide_index, outline_result, style_requirements, style_hints
            )

            params = ImageGenerationParams(
                prompt=prompt,
                ratio="16:9",
                output_dir=os.path.join(output_dir, "images"),
            )

            result = await self.image_generator(params)

            if result.get("success"):
                slide_info["generated_slide_image"] = {
                    "file_path": result["file_path"],
                    "filename": result["filename"],
                    "mime_type": result.get("mime_type", "image/png"),
                }
            return result

        except Exception as e:
            logger.error(f"Slide {slide_index + 1} generation error: {e}")
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    def _build_slide_prompt(
        self,
        slide_info: Dict,
        slide_index: int,
        outline_result: dict,
        style_requirements: str,
        style_hints: dict = None,
    ) -> str:
        total_slides = len(outline_result.get("slides", []))
        slide_type = slide_info.get("slide_type", "content")
        slide_type_desc = self._get_slide_type_description(slide_type)

        colors = self._extract_color_scheme(outline_result)
        layout = slide_info.get("layout_positions", {})
        key_points = slide_info.get("key_points", [])[:5]

        parts = [
            f"Create a presentation slide ({slide_index + 1} of {total_slides}).",
            "",
            f"SLIDE TYPE: {slide_type_desc}",
            f"TITLE: {slide_info.get('title', '')}",
        ]

        if slide_info.get("content_summary"):
            parts.append(f"SUMMARY: {slide_info['content_summary'][:200]}")

        if key_points:
            parts.append("KEY POINTS:")
            for i, pt in enumerate(key_points, 1):
                parts.append(f"  {i}. {pt}")

        parts.append("")
        parts.append(f"STYLE: {style_requirements or outline_result.get('style_theme', 'professional')}")

        if style_hints:
            parts.append("")
            parts.append("PRESET STYLE (follow strictly):")
            for k in ("background", "typography", "layout", "visual", "special"):
                if style_hints.get(k):
                    parts.append(f"  {k.title()}: {style_hints[k]}")
            if style_hints.get("colors"):
                parts.append(f"  Palette: {', '.join(style_hints['colors'])}")

        if colors and any(colors.values()):
            parts.append("")
            parts.append("COLOR SCHEME:")
            for role, val in colors.items():
                if val:
                    parts.append(f"  {role}: {val}")

        if layout:
            simplified = self._simplify_layout(layout)
            if simplified:
                parts.append("")
                parts.append("LAYOUT POSITIONS:")
                for elem, pos in simplified.items():
                    parts.append(f"  {elem}: {pos}")

        emotional = slide_info.get("emotional_tone", "")
        if emotional:
            parts.append(f"\nMOOD: {emotional}")

        parts.append(f"\nPAGE NUMBER: {slide_index + 1} / {total_slides}")

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _simplify_layout(layout_positions: Dict) -> Dict:
        simplified = {}
        for element, info in layout_positions.items():
            if isinstance(info, dict):
                pos = info.get("position", "")
                size = info.get("size", "")
                if pos:
                    simplified[element] = f"{pos} ({size})" if size else pos
        return simplified

    @staticmethod
    def _extract_color_scheme(outline_result: dict) -> Dict:
        palette = outline_result.get("design_system", {}).get("color_palette", {})
        return {
            "primary": palette.get("primary", ""),
            "secondary": palette.get("secondary", ""),
            "accent": palette.get("accent", ""),
            "background": palette.get("background", ""),
        }

    @staticmethod
    def _get_slide_type_description(slide_type: str) -> str:
        mapping = {
            "title": "Title slide — large centered headline, impactful and professional",
            "toc": "Table of contents — structured list with clear hierarchy",
            "transition": "Section divider — minimal design, chapter transition",
            "conclusion_cta": "Conclusion — summarizing key takeaways with call to action",
            "content": "Content slide — clear layout with visual elements",
            "problem_solution": "Problem vs. solution comparison — split layout",
            "data_dashboard": "Data dashboard — key metrics and charts",
            "timeline": "Timeline / roadmap — horizontal progression",
            "comparison": "Side-by-side comparison",
            "case_study": "Case study — narrative with results",
        }
        for key, desc in mapping.items():
            if key in slide_type.lower():
                return desc
        return "Content slide — clear layout with visual elements"

    @staticmethod
    def _init_template_styles() -> Dict[str, Dict]:
        return {
            "hero_title": {
                "style": "grand opening, impactful hero section",
                "mood": "inspiring, professional, attention-grabbing",
            },
            "two_column_comparison": {
                "style": "balanced dual layout, clear visual separation",
                "mood": "analytical, objective, structured",
            },
            "timeline": {
                "style": "horizontal flow, chronological progression",
                "mood": "progressive, forward-moving, dynamic",
            },
            "data_dashboard": {
                "style": "structured grid, data-centric design",
                "mood": "precise, analytical, trustworthy",
            },
            "case_study": {
                "style": "storytelling layout, narrative composition",
                "mood": "engaging, realistic, practical",
            },
            "standard_content": {
                "style": "versatile layout, content-first",
                "mood": "professional, clear, focused",
            },
        }
