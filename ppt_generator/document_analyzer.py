"""
Document Analyzer - Inspired by NotebookLM's Source-Grounded approach

Phase 1: Deep understanding of document structure for high-quality outline generation.
"""

import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DocumentAnalyzer:
    """
    Document Analyzer - Phase 1: Understanding document structure

    Inspired by NotebookLM's core principles:
    1. Source-Grounded: Analyze only based on user-provided content
    2. Deep structure parsing: Extract implicit pyramid structure
    3. Narrative suggestions: Recommend optimal presentation approach
    """

    def __init__(self, llm_client):
        """
        Initialize document analyzer

        Args:
            llm_client: LLM client instance
        """
        self.llm_client = llm_client

    def analyze_document(
        self,
        reference_text: str,
        context_hints: Dict = None,
        model: str = "gpt-4"
    ) -> Dict:
        """
        Deep analyze document and extract structured information

        Args:
            reference_text: Reference document text
            context_hints: Additional context hints (optional)
            model: Model to use

        Returns:
            Dict: Document analysis result
                - document_type: Document type
                - main_theme: Core theme
                - key_sections: Key sections list
                - data_points: Data points list
                - entities: Key entities
                - emotional_arc: Emotional arc
                - suggested_narrative: Suggested narrative structure
                - target_audience: Inferred target audience
                - complexity_level: Complexity level
        """
        system_prompt = self._get_analysis_system_prompt()
        user_prompt = self._build_analysis_user_prompt(reference_text, context_hints)

        try:
            result = self.llm_client.generate_structured_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                expected_structure="json",
                model=model,
                max_tokens=4000
            )

            # Validate and enhance result
            result = self._validate_and_enhance(result, reference_text)

            logger.info(f"Document analysis complete: type={result.get('document_type')}, "
                       f"theme={result.get('main_theme')}, "
                       f"sections={len(result.get('key_sections', []))}")

            return result

        except Exception as e:
            logger.error(f"Document analysis failed: {e}")
            return self._get_fallback_analysis(reference_text)

    def _get_analysis_system_prompt(self) -> str:
        """Get analysis system prompt"""
        return """You are a professional document analysis expert, skilled at extracting structured information from complex documents.

[Core Principle: Source-Grounded]
- Analyze only based on user-provided content
- Do not add information not present in the document
- Mark uncertain content as "inferred"
- Maintain an objective and neutral analytical perspective

[Analysis Dimensions]

1. Document Type Identification
   - Business: Business plans, market analysis, product intro, company intro
   - Technical: Technical proposals, architecture design, API docs, R&D reports
   - Academic: Research papers, academic presentations, course content, research reports
   - Creative: Creative proposals, design plans, marketing campaigns, brand stories

2. Pyramid Structure Parsing
   - Identify core argument (top layer)
   - Extract supporting evidence (middle layer)
   - Discover specific details (bottom layer)

3. Information Density Assessment
   - High-density information needs to be split for display
   - Low-density information can be merged for presentation

4. Narrative Structure Suggestions
   - Problem -> Solution -> Result
   - Chronological (time order)
   - Comparison (comparative analysis)
   - Story-driven

5. Audience Inference
   - Technical audience: Emphasize details and logic
   - Business audience: Emphasize value and ROI
   - General audience: Balance information density

[Output Requirements]
Return pure JSON format with the following structure:
{
    "document_type": "document type",
    "main_theme": "core theme (one sentence summary)",
    "key_sections": [
        {
            "title": "section title",
            "content_summary": "content summary",
            "importance": 1-10,
            "suggested_slides": 1-3
        }
    ],
    "data_points": [
        {
            "value": "data value",
            "context": "data meaning",
            "visualization": "suggested visualization method"
        }
    ],
    "entities": ["key entity 1", "key entity 2"],
    "emotional_arc": "emotional arc description",
    "suggested_narrative": "recommended narrative structure",
    "target_audience": "inferred target audience",
    "complexity_level": "simple/medium/complex",
    "key_message": "key takeaway in one sentence"
}"""

    def _build_analysis_user_prompt(
        self,
        reference_text: str,
        context_hints: Dict = None
    ) -> str:
        """Build analysis user prompt"""
        prompt_parts = [
            "Please deeply analyze the following document and extract structured information:",
            "",
            "[Document Content]",
            reference_text,
            ""
        ]

        if context_hints:
            prompt_parts.extend([
                "[Additional Context]"
            ])
            if context_hints.get("purpose"):
                prompt_parts.append(f"- Presentation purpose: {context_hints['purpose']}")
            if context_hints.get("audience"):
                prompt_parts.append(f"- Target audience: {context_hints['audience']}")
            if context_hints.get("duration"):
                prompt_parts.append(f"- Presentation duration: {context_hints['duration']} minutes")
            prompt_parts.append("")

        prompt_parts.extend([
            "Please return JSON format analysis result including:",
            "1. document_type - Document type",
            "2. main_theme - Core theme",
            "3. key_sections - Key sections (with importance score and suggested slide count)",
            "4. data_points - Data points (with visualization suggestions)",
            "5. entities - Key entities",
            "6. emotional_arc - Emotional arc",
            "7. suggested_narrative - Narrative structure suggestion",
            "8. target_audience - Inferred target audience",
            "9. complexity_level - Complexity",
            "10. key_message - Key takeaway"
        ])

        return "\n".join(prompt_parts)

    def _validate_and_enhance(self, result: Dict, reference_text: str) -> Dict:
        """Validate and enhance analysis result"""
        # Ensure required fields exist
        defaults = {
            "document_type": "General Document",
            "main_theme": self._extract_main_theme(reference_text),
            "key_sections": [],
            "data_points": [],
            "entities": [],
            "emotional_arc": "neutral",
            "suggested_narrative": "problem_solution_result",
            "target_audience": "General Audience",
            "complexity_level": "medium",
            "key_message": ""
        }

        for key, default_value in defaults.items():
            if key not in result or not result[key]:
                result[key] = default_value

        # Ensure key_sections has content
        if not result["key_sections"]:
            result["key_sections"] = self._auto_extract_sections(reference_text)

        # Calculate suggested total slide count
        total_slides = sum(
            section.get("suggested_slides", 1)
            for section in result["key_sections"]
        )
        result["suggested_total_slides"] = min(max(total_slides + 2, 5), 15)  # Add title and summary slides

        return result

    def _extract_main_theme(self, text: str) -> str:
        """Extract main theme from text (simple implementation)"""
        # Use first 100 characters as theme hint
        clean_text = text.strip()[:100]
        if len(clean_text) < len(text.strip()):
            clean_text += "..."
        return clean_text

    def _auto_extract_sections(self, text: str) -> List[Dict]:
        """Auto-extract sections (simple implementation)"""
        sections = []
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        for i, para in enumerate(paragraphs[:5]):  # Max 5 sections
            sections.append({
                "title": f"Section {i + 1}",
                "content_summary": para[:100] + "..." if len(para) > 100 else para,
                "importance": 5,
                "suggested_slides": 1
            })

        return sections

    def _get_fallback_analysis(self, reference_text: str) -> Dict:
        """Get fallback analysis result"""
        return {
            "document_type": "General Document",
            "main_theme": self._extract_main_theme(reference_text),
            "key_sections": self._auto_extract_sections(reference_text),
            "data_points": [],
            "entities": [],
            "emotional_arc": "neutral",
            "suggested_narrative": "problem_solution_result",
            "target_audience": "General Audience",
            "complexity_level": "medium",
            "key_message": "",
            "suggested_total_slides": 8
        }

    def extract_brand_elements(self, text: str) -> Dict:
        """
        Extract brand elements from text

        Args:
            text: Document text

        Returns:
            Dict: Brand elements
                - company_name: Company name
                - product_names: Product names list
                - brand_keywords: Brand keywords
        """
        # Simple implementation: can be enhanced with NER later
        return {
            "company_name": None,
            "product_names": [],
            "brand_keywords": []
        }

    def estimate_presentation_duration(self, analysis: Dict) -> Dict:
        """
        Estimate presentation duration

        Args:
            analysis: Document analysis result

        Returns:
            Dict: Duration estimate
                - total_minutes: Total duration (minutes)
                - per_slide_seconds: Average seconds per slide
                - time_allocation: Time allocation suggestions
        """
        total_slides = analysis.get("suggested_total_slides", 8)
        complexity = analysis.get("complexity_level", "medium")

        # Adjust time per slide based on complexity
        seconds_per_slide = {
            "simple": 45,
            "medium": 60,
            "complex": 90
        }.get(complexity, 60)

        total_seconds = total_slides * seconds_per_slide
        total_minutes = total_seconds / 60

        # 30-50-20 time allocation
        return {
            "total_minutes": round(total_minutes, 1),
            "per_slide_seconds": seconds_per_slide,
            "time_allocation": {
                "opening": f"{round(total_minutes * 0.3, 1)} minutes",
                "main_content": f"{round(total_minutes * 0.5, 1)} minutes",
                "closing": f"{round(total_minutes * 0.2, 1)} minutes"
            }
        }
