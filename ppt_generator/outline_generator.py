"""
PPT Outline Generator - Generates structured PPT outlines

Inspired by NotebookLM's two-stage generation approach:
1. Phase 1: Document analysis (understand structure)
2. Phase 2: Outline generation (based on analysis)
"""

import json
import logging
from typing import Dict, List, Optional

from .document_analyzer import DocumentAnalyzer
from .template_loader import get_template_presets

logger = logging.getLogger(__name__)


class OutlineGenerator:
    """
    PPT Outline Generator

    Supports two generation modes:
    1. Single-stage (backward compatible): Generate outline directly from text
    2. Two-stage (recommended): Analyze document first, then generate outline
    """

    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.slide_templates = self._init_slide_templates()
        self.document_analyzer = DocumentAnalyzer(llm_client)

    def generate_outline(
        self,
        reference_text: str,
        style_requirements: str,
        model: str = "gpt-4",
        template_preset: str = None
    ) -> Dict:
        """
        Generate PPT outline

        Args:
            reference_text: Reference text content
            style_requirements: Style requirements
            model: Model to use
            template_preset: Template preset name (optional)

        Returns:
            Dict: Structured PPT outline
        """
        system_prompt = self._get_system_prompt(template_preset)
        user_prompt = self._build_user_prompt(reference_text, style_requirements, template_preset)

        result = self.llm_client.generate_structured_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            expected_structure="json",
            model=model,
            max_tokens=8000
        )

        # Validate and fix result
        result = self._validate_and_fix_result(result, reference_text, style_requirements)

        # Post-process: add inferred relations and suggestions
        result = self._post_process(result)

        return result

    def generate_outline_two_stage(
        self,
        reference_text: str,
        style_requirements: str,
        audience_profile: Dict = None,
        brand_guidelines: Dict = None,
        context_hints: Dict = None,
        model: str = "gpt-4",
        template_preset: str = None,
        persona_context: Dict = None,
    ) -> Dict:
        """
        Two-stage outline generation (recommended) - Inspired by NotebookLM

        Stage 1: Document analysis - Deep understanding of document structure
        Stage 2: Outline generation - Generate high-quality outline from analysis

        Args:
            reference_text: Reference text content
            style_requirements: Style requirements
            audience_profile: Target audience info (optional)
            brand_guidelines: Brand guidelines (optional)
            context_hints: Additional context hints (optional)
            model: Model to use
            template_preset: Template preset name (optional)
            persona_context: Persona/audience context from PersonaEngine (optional)

        Returns:
            Dict: Structured PPT outline
        """
        if template_preset:
            logger.info(f"Using template preset: {template_preset}")
        if persona_context:
            logger.info(f"Using persona context: {persona_context.get('presenter_persona', 'N/A')} -> {persona_context.get('audience_label', 'N/A')}")
        logger.info("Starting two-stage outline generation...")

        # ===== Stage 1: Document analysis =====
        logger.info("Stage 1: Document analysis...")
        doc_analysis = self.document_analyzer.analyze_document(
            reference_text,
            context_hints=context_hints,
            model=model
        )
        logger.info(f"Document analysis complete: type={doc_analysis.get('document_type')}, "
                   f"theme={doc_analysis.get('main_theme')}")

        # ===== Stage 2: Generate outline from analysis =====
        logger.info("Stage 2: Generating outline from analysis...")
        system_prompt = self._get_two_stage_system_prompt(template_preset, persona_context)
        user_prompt = self._build_two_stage_user_prompt(
            doc_analysis,
            style_requirements,
            audience_profile,
            brand_guidelines,
            template_preset,
            persona_context,
        )

        result = self.llm_client.generate_structured_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            expected_structure="json",
            model=model,
            max_tokens=8000
        )

        # Validate and fix result
        result = self._validate_and_fix_result(result, reference_text, style_requirements)

        # Post-process
        result = self._post_process(result)

        # Attach analysis result
        result["_document_analysis"] = doc_analysis

        logger.info(f"Two-stage outline generation complete: {len(result.get('slides', []))} slides")
        return result

    def _get_two_stage_system_prompt(self, template_preset: str = None, persona_context: Dict = None) -> str:
        """Get two-stage generation system prompt"""
        base_prompt = """You are a PPT design architect, designing a PPT outline based on pre-analyzed document structure.

[Your Advantage]
You have received deep document analysis including:
- Document type and core theme
- Key sections with importance scores
- Data points and visualization suggestions
- Narrative structure recommendation
- Inferred target audience

[Design Principles - Problem -> Solution -> Result]

1. Opening (30% of slides)
   - Attention-grabbing title slide
   - Clear table of contents/roadmap
   - Problem/background setup

2. Core content (50% of slides)
   - Key sections ordered by importance
   - Data support slides
   - Case study/evidence slides

3. Closing (20% of slides)
   - Solution summary
   - Call to action
   - Contact info/next steps

[Slide Allocation Strategy]
- Allocate slides based on key_sections importance score
- importance >= 8: 2-3 slides
- importance 5-7: 1-2 slides
- importance < 5: Merge or omit

[Output Requirements]
Return pure JSON format, same structure as standard outline.
Ensure each slide contains:
- slide_number, slide_type, title
- content_summary, key_points[]
- layout_positions{}, visual_elements{}
- emotional_tone, template_suggestion"""

        if persona_context:
            persona_block = "\n\n[PERSONA & AUDIENCE ADAPTATION]"
            if persona_context.get("presenter_persona"):
                persona_block += f"\nPresenter role: {persona_context['presenter_persona']}"
            if persona_context.get("presenter_tone"):
                persona_block += f"\nTone: {persona_context['presenter_tone']}"
            if persona_context.get("audience_label"):
                persona_block += f"\nTarget audience: {persona_context['audience_label']}"
            if persona_context.get("content_guidance"):
                persona_block += f"\nContent guidance: {persona_context['content_guidance']}"
            if persona_context.get("tone_directive"):
                persona_block += f"\nTone directive: {persona_context['tone_directive']}"
            persona_block += "\n\nIMPORTANT: Adapt slide titles, content depth, language complexity, and emotional tone to match the presenter persona and target audience above."
            base_prompt += persona_block

        # If template preset specified, add constraints
        template_presets = get_template_presets()
        if template_preset and template_preset in template_presets:
            preset = template_presets[template_preset]
            preset_constraint = f"""

[Template Preset Constraint - {preset.get('name', template_preset)}]
You MUST strictly follow this template sequence:
Slide type sequence: {preset.get('sequence', [])}
Total slides: {preset.get('suggested_slides', 5)}
Narrative structure: {preset.get('narrative', 'problem_solution_result')}

Important:
- Each slide's slide_type must exactly match the sequence type
- Do not add or remove slides
- Adjust content organization based on template types in sequence"""
            return base_prompt + preset_constraint

        return base_prompt

    def _build_two_stage_user_prompt(
        self,
        doc_analysis: Dict,
        style_requirements: str,
        audience_profile: Dict = None,
        brand_guidelines: Dict = None,
        template_preset: str = None,
        persona_context: Dict = None,
    ) -> str:
        """Build two-stage generation user prompt"""
        prompt_parts = [
            "[Document Analysis Result]",
            f"Document type: {doc_analysis.get('document_type', 'General')}",
            f"Core theme: {doc_analysis.get('main_theme', '')}",
            f"Complexity: {doc_analysis.get('complexity_level', 'medium')}",
            f"Recommended narrative: {doc_analysis.get('suggested_narrative', 'problem_solution_result')}",
            f"Suggested total slides: {doc_analysis.get('suggested_total_slides', 8)}",
            "",
            "[Key Sections]"
        ]

        for section in doc_analysis.get("key_sections", []):
            prompt_parts.append(
                f"- {section.get('title', 'Untitled')} "
                f"(Importance: {section.get('importance', 5)}/10, "
                f"Suggested slides: {section.get('suggested_slides', 1)})"
            )
            prompt_parts.append(f"  Summary: {section.get('content_summary', '')[:100]}")

        if doc_analysis.get("data_points"):
            prompt_parts.extend(["", "[Data Points]"])
            for dp in doc_analysis.get("data_points", [])[:5]:
                prompt_parts.append(
                    f"- {dp.get('value', '')}: {dp.get('context', '')} "
                    f"(Visualization: {dp.get('visualization', 'chart')})"
                )

        if doc_analysis.get("key_message"):
            prompt_parts.extend([
                "",
                "[Key Takeaway]",
                doc_analysis.get("key_message", "")
            ])

        prompt_parts.extend([
            "",
            "[Style Requirements]",
            style_requirements or "Professional and concise"
        ])

        if audience_profile:
            prompt_parts.extend([
                "",
                "[Target Audience]",
                f"Type: {audience_profile.get('type', 'General')}",
                f"Expertise: {audience_profile.get('expertise', 'Medium')}",
                f"Interests: {audience_profile.get('interests', 'General information')}"
            ])
            if audience_profile.get("attention_span"):
                prompt_parts.append(f"Attention span: {audience_profile['attention_span']}")
            if audience_profile.get("visual_preference"):
                prompt_parts.append(f"Visual preference: {audience_profile['visual_preference']}")
            if audience_profile.get("content_depth"):
                prompt_parts.append(f"Content depth: {audience_profile['content_depth']}")
        elif doc_analysis.get("target_audience"):
            prompt_parts.extend([
                "",
                "[Inferred Target Audience]",
                doc_analysis.get("target_audience", "General Audience")
            ])

        if persona_context:
            prompt_parts.extend([
                "",
                "[PRESENTER PERSONA]",
                f"Role: {persona_context.get('presenter_persona', 'Professional')}",
                f"Tone: {persona_context.get('presenter_tone', 'professional')}",
            ])
            if persona_context.get("content_guidance"):
                prompt_parts.append(f"Content guidance: {persona_context['content_guidance']}")
            if persona_context.get("tone_directive"):
                prompt_parts.append(f"Tone directive: {persona_context['tone_directive']}")
            prompt_parts.append("Adapt all slide content to match this presenter's voice and audience expectations.")

        if brand_guidelines:
            prompt_parts.extend([
                "",
                "[Brand Guidelines]",
                f"Primary color: {brand_guidelines.get('primary_color', '#1e3c72')}",
                f"Secondary color: {brand_guidelines.get('secondary_color', '#2196F3')}",
                f"Style: {brand_guidelines.get('style', 'Professional')}"
            ])

        # If template preset, add constraint prompt
        template_presets = get_template_presets()
        if template_preset and template_preset in template_presets:
            preset = template_presets[template_preset]
            prompt_parts.extend([
                "",
                f"[Template Preset] Use '{preset.get('name', template_preset)}' preset",
                f"Slide sequence: {' -> '.join(preset.get('sequence', []))}",
                f"Total slides: {preset.get('suggested_slides', 5)}",
                "Strictly follow this template sequence; each slide's slide_type must match the sequence type."
            ])

        prompt_parts.extend([
            "",
            "Based on the above analysis, generate a structured PPT outline.",
            "Return JSON format with title, subtitle, total_slides, style_theme, slides[]."
        ])

        return "\n".join(prompt_parts)

    def _get_system_prompt(self, template_preset: str = None) -> str:
        """Get system prompt"""
        base_prompt = """You are a senior PPT designer with 10 years of presentation design experience.

[Core Capabilities]
1. Information architecture: Pyramid principle, top-down, clear hierarchy
2. Visual storytelling: Tell stories with visuals, not text blocks
3. Emotional design: Convey emotion through color and layout

[Design Principles]
1. One theme per slide: Each slide conveys one core message
2. 30-50-20 rule: 30% opening + 50% core + 20% conclusion
3. 7±2 rule: Keep 7±2 information units per slide
4. Visual hierarchy: 40% main visual + 30% support + 30% whitespace

[Slide Types]
- Title slide: Impactful opening, grab attention in 3 seconds
- TOC slide: Clear roadmap, reduce cognitive load
- Content slide: Combine text and images, data visualization
- Transition slide: Bridge sections, maintain rhythm
- Conclusion slide: Reinforce memory, call to action

[Output Requirements]
Return pure JSON format, no extra explanatory text.
Must include: title, subtitle, total_slides, style_theme, slides[]
Each slide must include: slide_number, slide_type, title, content_summary, key_points[], layout_positions{}, visual_elements{}, emotional_tone"""

        # If template preset specified, add constraints
        template_presets = get_template_presets()
        if template_preset and template_preset in template_presets:
            preset = template_presets[template_preset]
            preset_constraint = f"""

[Template Preset Constraint - {preset.get('name', template_preset)}]
You MUST strictly follow this template sequence:
Slide type sequence: {preset.get('sequence', [])}
Total slides: {preset.get('suggested_slides', 5)}

Important:
- Each slide's slide_type must exactly match the sequence type
- Do not add or remove slides
- Adjust content organization based on template types in sequence"""
            return base_prompt + preset_constraint

        return base_prompt

    def _build_user_prompt(self, reference_text: str, style_requirements: str, template_preset: str = None) -> str:
        """Build user prompt"""
        base_prompt = f"""[Reference Content]
{reference_text}

[Style Requirements]
{style_requirements}

[Layout Guide] (16:9 ratio, 9-grid)
- Positions: top-left/center/right, middle-left/center/right, bottom-left/center/right
- Title usually at top-center or top-left
- Main content at middle-center or middle-left
- Page number at bottom-right
"""

        # If template preset, add constraints
        template_presets = get_template_presets()
        if template_preset and template_preset in template_presets:
            preset = template_presets[template_preset]
            base_prompt += f"""
[Template Preset] Use '{preset.get('name', template_preset)}' preset
Slide sequence: {' -> '.join(preset.get('sequence', []))}
Total slides: {preset.get('suggested_slides', 5)}
Strictly follow this template sequence; each slide's slide_type must match the sequence type.
"""

        base_prompt += """
Generate PPT outline, return JSON format:
{
    "title": "Presentation Title",
    "subtitle": "Subtitle",
    "total_slides": 8,
    "style_theme": "Style theme",
    "slides": [
        {
            "slide_number": 1,
            "slide_type": "title",
            "title": "Title",
            "content_summary": "Overview",
            "key_points": ["Point 1", "Point 2"],
            "layout_positions": {
                "title": {"position": "middle-center", "size": "large"},
                "subtitle": {"position": "middle-center", "size": "medium"}
            },
            "visual_elements": {
                "main_visual": "Background description",
                "supporting_graphics": "Decorative elements"
            },
            "emotional_tone": "Professional, engaging"
        }
    ]
}"""
        return base_prompt

    def _validate_and_fix_result(self, result, reference_text: str, style_requirements: str) -> Dict:
        """Validate and fix result"""
        # If not dict, try to parse
        if not isinstance(result, dict):
            logger.warning(f"LLM returned non-dict: {type(result)}")
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    logger.error("Failed to parse LLM response string as JSON")
                    return self._get_default_outline(reference_text, style_requirements)

        # Check for error response
        if 'error' in result:
            logger.error(f"JSON parse failed: {result.get('error')}")
            if 'raw_response' in result:
                result = self._try_extract_json(result['raw_response'])
                if result is None:
                    return self._get_default_outline(reference_text, style_requirements)
            else:
                return self._get_default_outline(reference_text, style_requirements)

        # Ensure slides field exists
        if 'slides' not in result:
            logger.warning("Outline missing 'slides' field")
            return self._get_default_outline(reference_text, style_requirements)

        return result

    def _try_extract_json(self, raw: str) -> Dict:
        """Try to extract JSON from raw response"""
        try:
            # Clean markdown code blocks
            if '```json' in raw:
                start = raw.find('```json') + 7
                end = raw.rfind('```')
                if end > start:
                    raw = raw[start:end].strip()
            elif '```' in raw:
                start = raw.find('```') + 3
                end = raw.rfind('```')
                if end > start:
                    raw = raw[start:end].strip()

            # Find JSON portion
            start_idx = raw.find('{')
            end_idx = raw.rfind('}') + 1
            if start_idx != -1 and end_idx > 0:
                json_str = raw[start_idx:end_idx]
                result = json.loads(json_str)
                logger.info("Successfully recovered JSON from raw response")
                return result
        except Exception as e:
            logger.error(f"Failed to recover JSON from raw response: {e}")

        return None

    def _post_process(self, outline: Dict) -> Dict:
        """Post-process outline"""
        # Add slide relation inference
        if "slide_relations" not in outline:
            outline["slide_relations"] = self._infer_slide_relations(outline.get("slides", []))

        # Add template suggestions
        for slide in outline.get("slides", []):
            if "template_suggestion" not in slide:
                slide["template_suggestion"] = self._suggest_template(slide)

        # Add presentation flow suggestions
        if "presentation_flow" not in outline:
            outline["presentation_flow"] = self._generate_flow_suggestions(outline)

        # Add design system defaults
        if "design_system" not in outline:
            outline["design_system"] = self._get_default_design_system()

        return outline

    def _infer_slide_relations(self, slides: List[Dict]) -> List[Dict]:
        """Infer relations between slides"""
        relations = []

        for i in range(len(slides) - 1):
            current = slides[i]
            next_slide = slides[i + 1]

            current_type = current.get("slide_type", "").lower()
            next_type = next_slide.get("slide_type", "").lower()

            if "title" in current_type and ("toc" in next_type or "table of contents" in next_type):
                relation_type = "introduction_to_overview"
            elif "problem" in current.get("title", "").lower() and "solution" in next_slide.get("title", "").lower():
                relation_type = "problem_to_solution"
            elif "data" in current_type or "data" in next_type:
                relation_type = "data_support"
            else:
                relation_type = "sequential"

            relations.append({
                "from_slide": i + 1,
                "to_slide": i + 2,
                "relation_type": relation_type
            })

        return relations

    def _suggest_template(self, slide: Dict) -> str:
        """Suggest template based on slide content"""
        slide_type = slide.get("slide_type", "").lower()
        title = slide.get("title", "").lower()

        if "title" in slide_type:
            return "hero_title"
        elif "comparison" in title or "vs" in title or "compare" in title:
            return "two_column_comparison"
        elif "timeline" in title or "history" in title or "development" in title:
            return "timeline"
        elif "data" in slide_type or "stat" in title:
            return "data_dashboard"
        elif "case" in slide_type or "case" in title:
            return "case_study"
        else:
            return "standard_content"

    def _generate_flow_suggestions(self, outline: Dict) -> Dict:
        """Generate presentation flow suggestions"""
        total_slides = len(outline.get("slides", []))
        standard_path = list(range(1, total_slides + 1))

        quick_path = [1]
        for i, slide in enumerate(outline.get("slides", [])[1:], 2):
            slide_type = slide.get("slide_type", "").lower()
            if any(key in slide_type for key in ["summary", "conclusion", "toc", "core"]) or i == total_slides:
                quick_path.append(i)

        if len(quick_path) < 5 and total_slides > 5:
            step = total_slides // 5
            quick_path = list(range(1, total_slides + 1, step))
            if total_slides not in quick_path:
                quick_path.append(total_slides)

        return {
            "standard_path": standard_path,
            "quick_path": sorted(list(set(quick_path))),
            "detailed_path": "all_slides_with_appendix"
        }

    def _init_slide_templates(self) -> Dict:
        """Initialize slide template library"""
        return {
            "hero_title": {
                "name": "Hero Title Slide",
                "layout": "Center layout, large title",
                "best_for": "Opening slide, section divider"
            },
            "two_column_comparison": {
                "name": "Two-Column Comparison",
                "layout": "Equal left-right split",
                "best_for": "Comparison analysis, pros/cons"
            },
            "timeline": {
                "name": "Timeline",
                "layout": "Horizontal timeline",
                "best_for": "History, plans, process flow"
            },
            "data_dashboard": {
                "name": "Data Dashboard",
                "layout": "Grid data display",
                "best_for": "Data summary, KPI display"
            },
            "case_study": {
                "name": "Case Study",
                "layout": "Mixed text and image",
                "best_for": "Specific cases, success stories"
            }
        }

    def _get_default_design_system(self) -> Dict:
        """Get default design system"""
        return {
            "color_palette": {
                "primary": "#1e3c72",
                "secondary": "#2196F3",
                "accent": "#FF9800",
                "background": "#FFFFFF",
                "text": {
                    "primary": "#333333",
                    "secondary": "#666666",
                    "inverse": "#FFFFFF"
                }
            },
            "typography": {
                "heading_font": "Microsoft YaHei, sans-serif",
                "body_font": "PingFang SC, Arial, sans-serif",
                "font_sizes": {
                    "h1": "72px",
                    "h2": "48px",
                    "h3": "36px",
                    "body": "24px",
                    "small": "18px"
                }
            },
            "spacing": {
                "unit": "8px",
                "page_margin": "40px",
                "element_gap": "24px"
            }
        }

    def _get_default_outline(self, reference_text: str, style_requirements: str) -> Dict:
        """Get default outline structure"""
        return {
            "title": "Presentation",
            "subtitle": "Auto-generated presentation",
            "total_slides": 3,
            "target_audience": "General Audience",
            "presentation_goal": "Information delivery",
            "style_theme": style_requirements or "Professional and concise",
            "design_system": self._get_default_design_system(),
            "slides": [
                {
                    "slide_number": 1,
                    "slide_id": "title_slide",
                    "slide_type": "title",
                    "template_suggestion": "hero_title",
                    "title": "Title Slide",
                    "subtitle": "Subtitle",
                    "content_summary": "Opening introduction",
                    "key_points": ["Theme introduction"],
                    "visual_elements": {
                        "main_visual": "Gradient background",
                        "supporting_graphics": "Decorative elements"
                    },
                    "speaker_notes": "Opening remarks",
                    "emotional_tone": "Professional, engaging",
                    "background_image": "Tech gradient background"
                },
                {
                    "slide_number": 2,
                    "slide_id": "content_1",
                    "slide_type": "content",
                    "template_suggestion": "standard_content",
                    "title": "Main Content",
                    "content_summary": reference_text[:200] + "..." if len(reference_text) > 200 else reference_text,
                    "key_points": ["Point 1", "Point 2"],
                    "visual_elements": {
                        "main_visual": "Clean background",
                        "supporting_graphics": "Icons"
                    },
                    "speaker_notes": "Detailed explanation",
                    "emotional_tone": "Clear, professional",
                    "background_image": "Clean business background"
                },
                {
                    "slide_number": 3,
                    "slide_id": "summary",
                    "slide_type": "conclusion",
                    "template_suggestion": "standard_content",
                    "title": "Summary",
                    "content_summary": "Key points recap",
                    "key_points": ["Summary points"],
                    "visual_elements": {
                        "main_visual": "Summary background",
                        "supporting_graphics": "Charts"
                    },
                    "speaker_notes": "Closing remarks",
                    "emotional_tone": "Conclusive, impactful",
                    "background_image": "Professional summary background"
                }
            ]
        }
