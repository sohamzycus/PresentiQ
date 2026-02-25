"""
PPT Prompt Template System - Inspired by NotebookLM and Nano Banana Pro best practices

Provides structured prompt templates for high-quality, style-consistent PPT slides.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass

from .template_loader import get_template_presets


@dataclass
class SlideTemplate:
    """Slide template"""
    type_name: str
    structure: str
    visual_hierarchy: str
    emotional_tone: str
    layout_zones: Dict[str, str]
    design_rules: List[str]


class PromptTemplateSystem:
    """Structured prompt template system"""

    def __init__(self):
        self.templates = self._init_templates()
        self.narrative_structures = self._init_narrative_structures()
        self.style_modifiers = self._init_style_modifiers()
        self.text_rendering_rules = self._init_text_rendering_rules()
        self.page_number_style = self._init_page_number_style()

    def _init_templates(self) -> Dict[str, SlideTemplate]:
        """Initialize slide type templates"""
        return {
            # Title slide - Hero Title
            "title": SlideTemplate(
                type_name="Hero Title Slide",
                structure="Problem Statement - Create curiosity gap, grab attention in 3 seconds",
                visual_hierarchy="60% main title (centered) + 20% subtitle + 20% background visual",
                emotional_tone="inspiring, confident, forward-looking, prestigious",
                layout_zones={
                    "title": "middle-center, large bold text",
                    "subtitle": "below title, medium text",
                    "background": "sophisticated gradient or abstract pattern",
                    "decoration": "subtle particle effects or geometric shapes"
                },
                design_rules=[
                    "Title max 12 characters",
                    "Subtitle max 20 characters for supplementary info",
                    "Background: dark gradient or abstract pattern",
                    "Generous whitespace to highlight title"
                ]
            ),

            # TOC slide - Table of Contents
            "toc": SlideTemplate(
                type_name="Table of Contents",
                structure="Clear roadmap, reduce cognitive load",
                visual_hierarchy="20% title + 70% TOC items + 10% page number",
                emotional_tone="clear, organized, professional",
                layout_zones={
                    "title": "top-left or top-center",
                    "items": "middle area, 3-5 items with icons",
                    "current_indicator": "highlight current section",
                    "page_number": "bottom-right"
                },
                design_rules=[
                    "3-5 TOC items ideal",
                    "Icon per item for recognition",
                    "Highlight current section",
                    "Maintain visual balance"
                ]
            ),

            # Problem-Solution slide
            "problem_solution": SlideTemplate(
                type_name="Problem-Solution Comparison",
                structure="Left: pain point visualization -> Center: transition arrow -> Right: solution display",
                visual_hierarchy="45% problem area + 10% transition + 45% solution area",
                emotional_tone="empathetic, hopeful, transformative",
                layout_zones={
                    "problem": "left side, pain point with red/orange accent",
                    "transition": "center, arrow or transformation symbol",
                    "solution": "right side, benefit with green/blue accent",
                    "title": "top-center spanning both sides"
                },
                design_rules=[
                    "Problem: warm tones (red/orange)",
                    "Solution: cool tones (blue/green)",
                    "Clear center transition element",
                    "Concise text, icon-led"
                ]
            ),

            # Data Dashboard
            "data_dashboard": SlideTemplate(
                type_name="Data Dashboard",
                structure="Key metric (large number centered) + supporting data (around) + insight text",
                visual_hierarchy="40% key data + 40% supporting charts + 20% explanation",
                emotional_tone="authoritative, clear, data-driven",
                layout_zones={
                    "key_metric": "center-top, large bold number",
                    "supporting_charts": "middle area, 2-3 small charts",
                    "insight": "bottom, brief insight text",
                    "labels": "clear data labels on all elements"
                },
                design_rules=[
                    "Key data in extra-large font",
                    "Charts simple, no 3D effects",
                    "Consistent color coding",
                    "Clear readable data labels"
                ]
            ),

            # Timeline
            "timeline": SlideTemplate(
                type_name="Timeline / Process Flow",
                structure="3-5 milestones horizontal, current position highlighted",
                visual_hierarchy="15% title + 70% timeline + 15% explanation",
                emotional_tone="progressive, forward-moving, structured",
                layout_zones={
                    "title": "top-left or top-center",
                    "timeline": "middle, horizontal flow left-to-right",
                    "milestones": "3-5 nodes with icons and labels",
                    "current": "highlighted current position"
                },
                design_rules=[
                    "3-5 milestones optimal",
                    "Connecting lines for flow",
                    "Current stage visually prominent",
                    "Short label per node"
                ]
            ),

            # Comparison slide
            "comparison": SlideTemplate(
                type_name="Two-Column Comparison",
                structure="Left-right comparison, clear pros/cons display",
                visual_hierarchy="10% title + 45% left + 45% right",
                emotional_tone="objective, analytical, decisive",
                layout_zones={
                    "title": "top-center",
                    "left_column": "left 45%, with header",
                    "right_column": "right 45%, with header",
                    "vs_indicator": "center divider or VS symbol"
                },
                design_rules=[
                    "Symmetric two-column structure",
                    "Contrast colors for distinction",
                    "Equal number of points",
                    "Clear center divider"
                ]
            ),

            # Case Study
            "case_study": SlideTemplate(
                type_name="Case Study / Success Story",
                structure="Client background + challenge + solution + results",
                visual_hierarchy="30% case image + 50% content + 20% result data",
                emotional_tone="credible, inspiring, results-focused",
                layout_zones={
                    "image": "left or top, case visual",
                    "content": "right or bottom, story elements",
                    "metrics": "highlighted success metrics",
                    "quote": "optional customer quote"
                },
                design_rules=[
                    "Real case images for credibility",
                    "Quantify results with data",
                    "Customer quote adds value",
                    "Clear story line"
                ]
            ),

            # Conclusion CTA
            "conclusion_cta": SlideTemplate(
                type_name="Conclusion with Call-to-Action",
                structure="3 key points recap + clear CTA + contact info",
                visual_hierarchy="30% takeaways + 40% CTA + 30% contact info",
                emotional_tone="confident, memorable, actionable",
                layout_zones={
                    "takeaways": "top or left, 3 key points",
                    "cta": "center, clear call-to-action",
                    "contact": "bottom, contact information",
                    "next_steps": "what to do next"
                },
                design_rules=[
                    "Max 3 key points",
                    "CTA verb-led, clear and specific",
                    "Complete contact info",
                    "Powerful design"
                ]
            ),

            # Standard Content slide
            "content": SlideTemplate(
                type_name="Standard Content Slide",
                structure="Title + 3-5 key points + supporting visual",
                visual_hierarchy="20% title + 50% content + 30% visual",
                emotional_tone="clear, informative, professional",
                layout_zones={
                    "title": "top-left, clear heading",
                    "content": "left or center, bullet points",
                    "visual": "right or bottom, supporting image/icon",
                    "page_number": "bottom-right"
                },
                design_rules=[
                    "One theme per slide",
                    "3-5 key points",
                    "Max 15 chars per point",
                    "Images to enhance understanding"
                ]
            ),

            # Transition slide
            "transition": SlideTemplate(
                type_name="Section Transition",
                structure="Section title + brief intro",
                visual_hierarchy="70% section title + 30% background",
                emotional_tone="transitional, refreshing, preparatory",
                layout_zones={
                    "section_title": "center, large text",
                    "subtitle": "below title, brief intro",
                    "background": "distinct from content slides"
                },
                design_rules=[
                    "Echo title slide style",
                    "Bridge previous and next",
                    "Visual \"breathing\" space",
                    "Avoid information overload"
                ]
            )
        }

    def _init_narrative_structures(self) -> Dict[str, List[str]]:
        """Initialize narrative structure templates"""
        return {
            # Problem-Solution-Result (most common)
            "problem_solution_result": [
                "title",          # Opening: pose problem or vision
                "toc",            # Roadmap
                "content",        # Problem/status analysis
                "problem_solution",  # Solution comparison
                "content",        # Solution details
                "data_dashboard", # Data support
                "case_study",     # Case validation
                "conclusion_cta"  # Summary and action
            ],

            # Chronological narrative
            "chronological": [
                "title",
                "toc",
                "timeline",
                "content",
                "content",
                "content",
                "conclusion_cta"
            ],

            # Comparison analysis
            "comparison_analysis": [
                "title",
                "toc",
                "comparison",
                "data_dashboard",
                "content",
                "conclusion_cta"
            ],

            # Story-driven
            "story_driven": [
                "title",
                "content",        # Background setup
                "problem_solution",  # Conflict
                "timeline",       # Development
                "data_dashboard", # Climax (results)
                "conclusion_cta"  # Conclusion
            ]
        }

    def _init_style_modifiers(self) -> Dict[str, Dict[str, str]]:
        """Initialize style modifiers"""
        return {
            "corporate": {
                "colors": "navy blue, white, subtle gold accents",
                "fonts": "clean sans-serif, professional",
                "mood": "trustworthy, established, premium",
                "background": "subtle gradients, geometric patterns"
            },
            "tech": {
                "colors": "dark backgrounds, neon accents, gradients",
                "fonts": "modern, geometric, tech-forward",
                "mood": "innovative, cutting-edge, futuristic",
                "background": "circuit patterns, abstract tech visuals"
            },
            "creative": {
                "colors": "vibrant, bold color combinations",
                "fonts": "expressive, varied weights",
                "mood": "dynamic, inspiring, unconventional",
                "background": "artistic, textured, unique"
            },
            "minimal": {
                "colors": "black, white, single accent color",
                "fonts": "thin, elegant, lots of whitespace",
                "mood": "sophisticated, clean, focused",
                "background": "solid colors, minimal decoration"
            },
            "academic": {
                "colors": "muted, professional, conservative",
                "fonts": "serif or classic sans-serif",
                "mood": "credible, scholarly, structured",
                "background": "clean, distraction-free"
            }
        }

    def get_template(self, slide_type: str) -> SlideTemplate:
        """Get template for specified type"""
        # Map common type names to keys (supports both English and legacy names)
        type_mapping = {
            "title": "title",
            "toc": "toc",
            "content": "content",
            "data_dashboard": "data_dashboard",
            "timeline": "timeline",
            "comparison": "comparison",
            "case_study": "case_study",
            "conclusion_cta": "conclusion_cta",
            "transition": "transition",
            "problem_solution": "problem_solution"
        }

        # Try direct match or mapping
        key = type_mapping.get(slide_type, slide_type.lower().replace(" ", "_"))
        return self.templates.get(key, self.templates["content"])

    def build_image_prompt(
        self,
        slide_info: Dict,
        slide_index: int,
        total_slides: int,
        style_requirements: str,
        brand_colors: Dict = None,
        style_hints: Dict = None,
        persona_context: Dict = None,
    ) -> str:
        """
        Build enhanced image generation prompt

        Args:
            slide_info: Slide info
            slide_index: Current slide index
            total_slides: Total slide count
            style_requirements: Style requirements
            brand_colors: Brand colors (optional)
            style_hints: Template preset style hints (optional)
            persona_context: Persona/audience context (optional)

        Returns:
            Structured image generation prompt
        """
        slide_type = slide_info.get("slide_type", "content")
        template = self.get_template(slide_type)

        # Determine narrative position
        narrative_position = self._determine_narrative_position(slide_index, total_slides)

        # Get style modifier
        style_modifier = self._match_style_modifier(style_requirements)

        # Build structured prompt
        prompt_parts = [
            f"Create a professional PPT slide image (16:9 aspect ratio).",
        ]

        # [CRITICAL] Put template preset style hints first, highest priority
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
                "⚠️ Do NOT deviate from these visual requirements!",
                "=" * 60,
            ])

        # Persona/audience context for tone and content adaptation
        if persona_context:
            prompt_parts.extend([
                "",
                "[PERSONA & AUDIENCE CONTEXT]",
            ])
            if persona_context.get("presenter_persona"):
                prompt_parts.append(f"  Presenter: {persona_context['presenter_persona']}")
            if persona_context.get("presenter_tone"):
                prompt_parts.append(f"  Tone: {persona_context['presenter_tone']}")
            if persona_context.get("audience_label"):
                prompt_parts.append(f"  Audience: {persona_context['audience_label']}")
            if persona_context.get("tone_directive"):
                prompt_parts.append(f"  Directive: {persona_context['tone_directive']}")
            prompt_parts.append("  Adapt text tone, visual density, and language to match the above.")

        prompt_parts.extend([
            "",
            f"[SLIDE TYPE] {template.type_name}",
            f"[PAGE] {slide_index + 1} of {total_slides}",
            f"[NARRATIVE ROLE] {narrative_position}",
            "",
            f"[STRUCTURE]",
            f"{template.structure}",
            "",
            f"[VISUAL HIERARCHY]",
            f"{template.visual_hierarchy}",
            "",
            f"[LAYOUT ZONES]"
        ])

        for zone, desc in template.layout_zones.items():
            prompt_parts.append(f"  - {zone}: {desc}")

        prompt_parts.extend([
            "",
            f"[CONTENT]",
            f"  Title: {slide_info.get('title', '')}",
        ])

        # Add key points (limit count)
        key_points = slide_info.get("key_points", [])[:3]
        if key_points:
            prompt_parts.append(f"  Key Points:")
            for i, point in enumerate(key_points, 1):
                prompt_parts.append(f"    {i}. {point}")

        prompt_parts.extend([
            "",
            f"[STYLE]",
            f"  Theme: {style_requirements}",
            f"  Mood: {template.emotional_tone}"
        ])

        if style_modifier:
            prompt_parts.extend([
                f"  Colors: {style_modifier['colors']}",
                f"  Fonts: {style_modifier['fonts']}",
                f"  Background: {style_modifier['background']}"
            ])

        # style_hints already added at prompt start, just reinforce here
        if style_hints:
            prompt_parts.extend([
                "",
                "[STYLE REMINDER - REFER TO TOP SECTION]",
                "Apply the preset style defined at the beginning of this prompt!"
            ])

        if brand_colors:
            prompt_parts.extend([
                "",
                f"[BRAND COLORS]",
                f"  Primary: {brand_colors.get('primary', '#1e3c72')}",
                f"  Secondary: {brand_colors.get('secondary', '#2196F3')}",
                f"  Accent: {brand_colors.get('accent', '#FF9800')}"
            ])

        prompt_parts.extend([
            "",
            f"[DESIGN RULES]"
        ])
        for rule in template.design_rules:
            prompt_parts.append(f"  - {rule}")

        # Add text rendering requirements
        prompt_parts.extend([
            "",
            f"[TEXT RENDERING - CRITICAL]",
            f"  Font: {self.text_rendering_rules['font_requirements']['style']}",
            "  Requirements:",
            "  - All text MUST be crisp, clear, and highly legible",
            "  - Use proper anti-aliasing for smooth text edges",
            "  - High contrast between text and background",
            "  - Consistent font weight: bold for titles, medium for body",
            "  - Proper character spacing (not cramped)",
            "  - Line height 1.5-1.8x for readability",
            "  - NO blurry, distorted, or low-quality text"
        ])

        # Add consistent page number style
        prompt_parts.extend([
            "",
            f"[PAGE NUMBER - MUST BE CONSISTENT]",
            f"  Position: {self.page_number_style['position']}",
            f"  Format: {slide_index + 1} / {total_slides}",
            "  Style:",
            f"  - Small font (10-12pt), regular weight",
            f"  - Subtle gray color (#666666) or theme-matched",
            f"  - 70-80% opacity",
            f"  - 8-12px padding from slide edges",
            "  CRITICAL: Use EXACT same style on EVERY slide - no variation!"
        ])

        prompt_parts.extend([
            "",
            f"[AVOID]",
            "  - Cluttered layouts with too many elements",
            "  - Excessive text that's hard to read",
            "  - Inconsistent styling or colors",
            "  - Low-quality or pixelated graphics",
            "  - 3D effects on charts or elements",
            "  - Blurry or illegible text",
            "  - Inconsistent page number placement or style"
        ])

        return "\n".join(prompt_parts)

    def _determine_narrative_position(self, slide_index: int, total_slides: int) -> str:
        """Determine current slide position in narrative structure"""
        position_ratio = slide_index / max(total_slides - 1, 1)

        if slide_index == 0:
            return "Opening - Grab attention, build anticipation"
        elif position_ratio < 0.3:
            return "Setup - Set background, define problem"
        elif position_ratio < 0.7:
            return "Development - Expand argument, provide evidence"
        elif slide_index == total_slides - 1:
            return "Closing - Summarize key points, call to action"
        else:
            return "Climax - Core argument, key turning point"

    def _match_style_modifier(self, style_requirements: str) -> Optional[Dict]:
        """Match modifier based on style requirements"""
        style_lower = style_requirements.lower()

        for style_name, modifier in self.style_modifiers.items():
            if style_name in style_lower:
                return modifier

        # Keyword matching
        if any(kw in style_lower for kw in ["corporate", "business", "company"]):
            return self.style_modifiers["corporate"]
        elif any(kw in style_lower for kw in ["tech", "ai", "internet"]):
            return self.style_modifiers["tech"]
        elif any(kw in style_lower for kw in ["creative", "art", "design"]):
            return self.style_modifiers["creative"]
        elif any(kw in style_lower for kw in ["minimal", "simple"]):
            return self.style_modifiers["minimal"]
        elif any(kw in style_lower for kw in ["academic", "research"]):
            return self.style_modifiers["academic"]

        return self.style_modifiers["corporate"]  # Default corporate style

    def _init_text_rendering_rules(self) -> Dict:
        """Initialize text rendering rules for high-quality slide output."""
        return {
            "font_requirements": {
                "primary": "Inter, Noto Sans, Helvetica Neue",
                "fallback": "Arial, sans-serif",
                "style": "clean, modern, highly legible font"
            },
            "text_rendering": {
                "anti_aliasing": "smooth, no jagged edges",
                "contrast": "high contrast between text and background",
                "weight": "medium weight for body, bold for titles",
                "spacing": "proper character spacing (not too tight)"
            },
            "layout_rules": {
                "line_height": "1.5x to 1.8x for text",
                "paragraph_spacing": "generous spacing between blocks",
                "margins": "adequate margins to prevent text crowding"
            },
            "quality_checks": [
                "Text must be crisp and clear",
                "No blurry or distorted text",
                "Consistent font style throughout",
                "Proper punctuation rendering",
                "No character overlap or collision"
            ]
        }

    def _init_page_number_style(self) -> Dict:
        """Initialize unified page number style spec"""
        return {
            "position": "bottom-right corner",
            "format": "{current} / {total}",
            "style": {
                "font_size": "small, 10-12pt equivalent",
                "font_weight": "regular",
                "color": "subtle gray (#666666) or match theme accent",
                "opacity": "70-80% for subtlety"
            },
            "container": {
                "background": "none or very subtle rounded rectangle",
                "padding": "8-12px from edges",
                "alignment": "right-aligned"
            },
            "consistency_rules": [
                "EXACT same position on every slide",
                "EXACT same font size and style",
                "EXACT same color and opacity",
                "NO variation in format or placement",
                "Visible but not distracting"
            ]
        }

    def suggest_narrative_structure(self, doc_analysis: Dict) -> List[str]:
        """Recommend narrative structure from document analysis"""
        doc_type = doc_analysis.get("document_type", "").lower()
        suggested = doc_analysis.get("suggested_narrative", "").lower()

        if "chronological" in suggested or "history" in suggested or "development" in suggested:
            return self.narrative_structures["chronological"]
        elif "comparison" in suggested or "compare" in suggested:
            return self.narrative_structures["comparison_analysis"]
        elif "story" in suggested or "case" in suggested:
            return self.narrative_structures["story_driven"]
        else:
            return self.narrative_structures["problem_solution_result"]

    # ==================== Preset template combinations ====================

    def get_preset(self, preset_name: str) -> Optional[Dict]:
        """
        Get preset template combination

        Args:
            preset_name: Preset name

        Returns:
            Preset config dict with name, description, sequence, narrative
        """
        return get_template_presets().get(preset_name)

    def list_presets(self) -> List[Dict]:
        """
        List all available presets

        Returns:
            Preset list, each with key, name, description
        """
        return [
            {
                "key": key,
                "name": preset.get("name", key),
                "description": preset.get("description", "")
            }
            for key, preset in get_template_presets().items()
        ]

    def get_preset_sequence(self, preset_name: str) -> List[str]:
        """
        Get preset template sequence

        Args:
            preset_name: Preset name

        Returns:
            Template type sequence list
        """
        preset = self.get_preset(preset_name)
        return preset.get("sequence", []) if preset else []

    def get_preset_narrative(self, preset_name: str) -> str:
        """
        Get preset recommended narrative structure

        Args:
            preset_name: Preset name

        Returns:
            Narrative structure name
        """
        preset = self.get_preset(preset_name)
        return preset.get("narrative", "problem_solution_result") if preset else "problem_solution_result"
