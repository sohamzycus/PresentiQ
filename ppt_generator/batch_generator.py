"""
Batch Image Generator - Inspired by Nano Banana Pro batch generation

Main features:
1. Style anchoring - Generate title slide first as style anchor, subsequent slides reference it
2. Group by type for batch generation - Same-type slides generated together for consistency
3. Reference image context - Support brand manual and other reference images
"""

import asyncio
import logging
import base64
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from .prompt_templates import PromptTemplateSystem
from .error_handler import SmartErrorHandler, ErrorAnalysis, RecoveryAction

logger = logging.getLogger(__name__)


@dataclass
class BatchGenerationResult:
    """Batch generation result"""
    slide_index: int
    success: bool
    file_path: Optional[str]
    error: Optional[str]
    from_cache: bool = False
    retries: int = 0


class BatchImageGenerator:
    """
    Batch image generator

    Inspired by Nano Banana Pro capabilities:
    1. Style anchoring mechanism
    2. Batch generation
    3. Reference image context (max 14 images)
    """

    def __init__(self, image_tool, cache_manager=None):
        """
        Initialize batch generator

        Args:
            image_tool: Image generation tool instance
            cache_manager: Cache manager (optional)
        """
        self.image_tool = image_tool
        self.cache_manager = cache_manager
        self.prompt_system = PromptTemplateSystem()
        self.error_handler = SmartErrorHandler()

        # Style anchoring
        self.style_anchor: Optional[Dict] = None
        self.style_anchor_image: Optional[str] = None

    async def generate_with_style_consistency(
        self,
        slides: List[Dict],
        outline_result: Dict,
        style_requirements: str,
        output_dir: str,
        brand_references: List[str] = None,
        max_concurrent: int = 4,
        style_hints: Dict = None,
        persona_context: Dict = None,
    ) -> List[BatchGenerationResult]:
        """
        Batch generate style-consistent slide images

        Args:
            slides: Slide info list
            outline_result: Full outline result
            style_requirements: Style requirements
            output_dir: Output directory
            brand_references: Brand reference image paths (max 14)
            max_concurrent: Max concurrency
            style_hints: Template preset style hints (optional)
            persona_context: Persona/audience context (optional)

        Returns:
            List[BatchGenerationResult]: Generation result list
        """
        self.style_hints = style_hints  # Save style hints
        self.persona_context = persona_context  # Save persona context
        total_slides = len(slides)
        logger.info(f"Starting batch generation of {total_slides} slides, concurrency: {max_concurrent}")
        if style_hints:
            logger.info(f"Using style hints: {style_hints.get('background', '')}")

        results: List[BatchGenerationResult] = []

        # ===== Step 1: Generate style anchor image =====
        anchor_slide = self._find_anchor_slide(slides)
        anchor_index = slides.index(anchor_slide)

        logger.info(f"Generating style anchor (slide {anchor_index + 1})...")
        anchor_result = await self._generate_anchor(
            anchor_slide,
            anchor_index,
            outline_result,
            style_requirements,
            output_dir,
            brand_references
        )

        if anchor_result.success:
            self.style_anchor = self._extract_style_description(anchor_slide, style_requirements)
            self.style_anchor_image = anchor_result.file_path
            logger.info("Style anchor generated successfully")
        else:
            logger.warning("Style anchor generation failed, continuing with standalone mode")

        results.append(anchor_result)

        # ===== Step 2: Group by type and batch generate remaining slides =====
        remaining_slides = [
            (i, slide) for i, slide in enumerate(slides)
            if i != anchor_index
        ]

        # Group by type
        slide_groups = self._group_slides_by_type(remaining_slides)

        # Concurrent generation per group
        semaphore = asyncio.Semaphore(max_concurrent)

        async def generate_slide_with_semaphore(
            index: int,
            slide: Dict
        ) -> BatchGenerationResult:
            async with semaphore:
                return await self._generate_single_slide(
                    slide,
                    index,
                    outline_result,
                    style_requirements,
                    output_dir,
                    brand_references
                )

        # Create all tasks
        tasks = []
        for slide_type, group in slide_groups.items():
            logger.info(f"Processing {slide_type} type slides, {len(group)} total")
            for index, slide in group:
                tasks.append(generate_slide_with_semaphore(index, slide))

        # Execute concurrently
        group_results = await asyncio.gather(*tasks)
        results.extend(group_results)

        # Sort by index
        results.sort(key=lambda x: x.slide_index)

        # Statistics
        success_count = sum(1 for r in results if r.success)
        cache_count = sum(1 for r in results if r.from_cache)
        logger.info(f"Batch generation complete: {success_count}/{total_slides} success, "
                   f"{cache_count} from cache")

        return results

    def _find_anchor_slide(self, slides: List[Dict]) -> Dict:
        """
        Find slide to use as style anchor

        Priority:
        1. Title slide
        2. First slide
        """
        for slide in slides:
            slide_type = slide.get('slide_type', '').lower()
            if 'title' in slide_type:
                return slide

        return slides[0] if slides else {}

    async def _generate_anchor(
        self,
        slide: Dict,
        index: int,
        outline_result: Dict,
        style_requirements: str,
        output_dir: str,
        brand_references: List[str] = None
    ) -> BatchGenerationResult:
        """Generate style anchor image"""
        # Build enhanced anchor prompt
        prompt = self._build_anchor_prompt(
            slide,
            index,
            outline_result,
            style_requirements,
            brand_references
        )

        try:
            from .slide_generator_official import ImageGenerationParams

            params = ImageGenerationParams(
                prompt=prompt,
                ratio="16:9",
                output_dir=os.path.join(output_dir, "images")
            )

            result = await self.image_tool.gemini_generate(params)

            if result.get("success"):
                return BatchGenerationResult(
                    slide_index=index,
                    success=True,
                    file_path=result.get("file_path"),
                    error=None
                )
            else:
                return BatchGenerationResult(
                    slide_index=index,
                    success=False,
                    file_path=None,
                    error=result.get("error", "Unknown error")
                )

        except Exception as e:
            logger.error(f"Anchor slide generation failed: {e}")
            return BatchGenerationResult(
                slide_index=index,
                success=False,
                file_path=None,
                error=str(e)
            )

    async def _generate_single_slide(
        self,
        slide: Dict,
        index: int,
        outline_result: Dict,
        style_requirements: str,
        output_dir: str,
        brand_references: List[str] = None
    ) -> BatchGenerationResult:
        """Generate single slide"""
        total_slides = len(outline_result.get('slides', []))

        # Check cache
        if self.cache_manager:
            cache_key = self.cache_manager.get_image_prompt_hash(
                f"{slide.get('title')}_{slide.get('slide_type')}_{str(slide.get('key_points', []))}"
            )
            cached_path = self.cache_manager.get_cached_image(cache_key)
            if cached_path:
                return BatchGenerationResult(
                    slide_index=index,
                    success=True,
                    file_path=cached_path,
                    error=None,
                    from_cache=True
                )

        # Build prompt
        prompt = self._build_slide_prompt(
            slide,
            index,
            total_slides,
            style_requirements,
            brand_references
        )

        # Generation with error recovery
        max_retries = 3
        for attempt in range(max_retries):
            try:
                from .slide_generator_official import ImageGenerationParams

                params = ImageGenerationParams(
                    prompt=prompt,
                    ratio="16:9",
                    output_dir=os.path.join(output_dir, "images")
                )

                result = await self.image_tool.gemini_generate(params)

                if result.get("success"):
                    file_path = result.get("file_path")

                    # Cache successful image
                    if self.cache_manager and file_path:
                        self.cache_manager.cache_image(prompt, file_path)

                    return BatchGenerationResult(
                        slide_index=index,
                        success=True,
                        file_path=file_path,
                        error=None,
                        retries=attempt
                    )

                # Error handling
                error_analysis = self.error_handler.analyze_error(
                    result,
                    prompt,
                    attempt
                )

                if error_analysis.should_retry and error_analysis.modified_prompt:
                    prompt = error_analysis.modified_prompt
                    logger.info(f"Slide {index + 1}: {error_analysis.message}")
                    await asyncio.sleep(error_analysis.retry_delay)
                else:
                    return BatchGenerationResult(
                        slide_index=index,
                        success=False,
                        file_path=None,
                        error=error_analysis.message,
                        retries=attempt
                    )

            except Exception as e:
                logger.error(f"Slide {index + 1} generation exception: {e}")
                if attempt == max_retries - 1:
                    return BatchGenerationResult(
                        slide_index=index,
                        success=False,
                        file_path=None,
                        error=str(e),
                        retries=attempt
                    )
                await asyncio.sleep(2)

        return BatchGenerationResult(
            slide_index=index,
            success=False,
            file_path=None,
            error="Max retries exceeded",
            retries=max_retries
        )

    def _build_anchor_prompt(
        self,
        slide: Dict,
        index: int,
        outline_result: Dict,
        style_requirements: str,
        brand_references: List[str] = None
    ) -> str:
        """Build style anchor prompt"""
        total_slides = len(outline_result.get('slides', []))

        prompt_parts = [
            "Create a hero title slide that establishes the visual style for an entire presentation.",
        ]

        # [CRITICAL] Put template preset style hints first, highest priority
        style_hints = getattr(self, 'style_hints', None)
        if style_hints:
            prompt_parts.extend([
                "",
                "=" * 60,
                "[CRITICAL - PRESET STYLE - HIGHEST PRIORITY]",
                "=" * 60,
                "You MUST follow these style requirements EXACTLY:",
                f"  ★ Background: {style_hints.get('background', '')}",
                f"  ★ Typography: {style_hints.get('typography', '')}",
                f"  ★ Color Palette: {', '.join(style_hints.get('colors', []))}",
                f"  ★ Layout Style: {style_hints.get('layout', '')}",
                f"  ★ Visual Elements: {style_hints.get('visual', '')}"
            ])
            if style_hints.get('special'):
                prompt_parts.append(f"  ★ Special: {style_hints.get('special')}")
            prompt_parts.extend([
                "",
                "⚠️ WARNING: The above style MUST be strictly followed!",
                "⚠️ This is the FOUNDATION style for the ENTIRE presentation!",
                "⚠️ Do NOT deviate from these visual requirements!",
                "=" * 60,
            ])

        prompt_parts.extend([
            "",
            "[ROLE] This is the STYLE ANCHOR slide - all subsequent slides will match this style.",
            "",
            f"[SLIDE INFO]",
            f"Title: {slide.get('title', 'Untitled')}",
            f"Type: {slide.get('slide_type', 'Title')}",
            f"Total Presentation: {total_slides} slides",
            "",
            f"[STYLE REQUIREMENTS]",
            f"{style_requirements}",
            "",
            "[DESIGN SPECIFICATIONS]",
            "- Establish a clear visual language",
            "- Define color palette through usage",
            "- Set typography hierarchy",
            "- Create memorable visual identity",
            "- 16:9 aspect ratio",
            "",
            "[TEXT RENDERING - CRITICAL]",
            "- All text MUST be crisp, clear, highly legible",
            "- Use modern sans-serif fonts (Inter, Noto Sans, Helvetica Neue)",
            "- Bold weight for title, proper anti-aliasing",
            "- High contrast between text and background",
            "- NO blurry or distorted characters",
            "",
            "[PAGE NUMBER TEMPLATE - DEFINE FOR ALL SLIDES]",
            f"- Position: bottom-right corner, exactly 12px from edges",
            f"- Format: 1/{total_slides}",
            "- Style: small (10pt), gray (#666666), 75% opacity",
            "- This EXACT style must be used on ALL subsequent slides",
            "",
            "[QUALITY]",
            "- Professional, premium quality",
            "- Clean, modern design",
            "- High visual impact"
        ])

        if brand_references:
            prompt_parts.extend([
                "",
                "[BRAND REFERENCES]",
                f"Follow visual style from {min(len(brand_references), 14)} reference images"
            ])

        # Reinforce style at end
        if style_hints:
            prompt_parts.extend([
                "",
                "[FINAL REMINDER]",
                "Remember: Apply the PRESET STYLE defined at the beginning!",
                f"Key visual: {style_hints.get('visual', '')}",
                f"Key colors: {', '.join(style_hints.get('colors', []))}"
            ])

        return "\n".join(prompt_parts)

    def _build_slide_prompt(
        self,
        slide: Dict,
        index: int,
        total_slides: int,
        style_requirements: str,
        brand_references: List[str] = None
    ) -> str:
        """Build single slide prompt"""
        # Use PromptTemplateSystem to build, pass style_hints and persona_context
        prompt = self.prompt_system.build_image_prompt(
            slide_info=slide,
            slide_index=index,
            total_slides=total_slides,
            style_requirements=style_requirements,
            style_hints=getattr(self, 'style_hints', None),
            persona_context=getattr(self, 'persona_context', None),
        )

        # If style anchor exists, add style consistency instructions
        if self.style_anchor:
            prompt = f"""[STYLE CONSISTENCY - CRITICAL]
Match the visual style of the anchor slide EXACTLY:
{self.style_anchor.get('description', '')}

[CONSISTENT ELEMENTS - MUST MATCH ANCHOR]
1. Color palette: Use SAME colors as anchor slide
2. Typography: Use SAME font style and weights
3. Page number: EXACT same position (bottom-right, 12px from edge), size (10pt), color (#666666)
4. Layout spacing: Match margins and padding
5. Text: Same crisp, clear rendering quality

---

{prompt}"""

        return prompt

    def _group_slides_by_type(
        self,
        slides: List[Tuple[int, Dict]]
    ) -> Dict[str, List[Tuple[int, Dict]]]:
        """Group slides by type"""
        groups: Dict[str, List[Tuple[int, Dict]]] = {}

        for index, slide in slides:
            slide_type = slide.get('slide_type', 'content').lower()

            # Normalize type name
            if 'title' in slide_type:
                type_key = 'title'
            elif 'toc' in slide_type or 'table of contents' in slide_type:
                type_key = 'toc'
            elif 'data' in slide_type:
                type_key = 'data'
            elif 'timeline' in slide_type:
                type_key = 'timeline'
            elif 'conclusion' in slide_type or 'summary' in slide_type:
                type_key = 'conclusion'
            else:
                type_key = 'content'

            if type_key not in groups:
                groups[type_key] = []
            groups[type_key].append((index, slide))

        return groups

    def _extract_style_description(
        self,
        slide: Dict,
        style_requirements: str
    ) -> Dict:
        """Extract style description from anchor slide"""
        style_info = {
            "description": f"Style based on: {style_requirements}",
            "slide_type": slide.get('slide_type', ''),
            "colors": slide.get('visual_elements', {}).get('colors', []),
            "mood": slide.get('emotional_tone', '')
        }

        # Save full style_hints for subsequent slides
        style_hints = getattr(self, 'style_hints', None)
        if style_hints:
            style_info["style_hints"] = style_hints
            # Enhance description
            style_parts = []
            if style_hints.get('background'):
                style_parts.append(f"Background: {style_hints['background']}")
            if style_hints.get('typography'):
                style_parts.append(f"Typography: {style_hints['typography']}")
            if style_hints.get('colors'):
                style_parts.append(f"Colors: {', '.join(style_hints['colors'])}")
            if style_hints.get('layout'):
                style_parts.append(f"Layout: {style_hints['layout']}")
            if style_hints.get('visual'):
                style_parts.append(f"Visual: {style_hints['visual']}")

            if style_parts:
                style_info["description"] = " | ".join(style_parts)

        return style_info

    def _encode_reference_image(self, image_path: str) -> Optional[str]:
        """Encode reference image to base64"""
        try:
            if not os.path.exists(image_path):
                return None

            with open(image_path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')

        except Exception as e:
            logger.warning(f"Failed to encode reference image: {image_path}, {e}")
            return None

    def reset_style_anchor(self):
        """Reset style anchor"""
        self.style_anchor = None
        self.style_anchor_image = None
