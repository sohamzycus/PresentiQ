"""
Persona Engine — Audience-aware theme selection and dynamic style generation.

Given a presenter persona and target audience, this engine:
1. Recommends the best existing template OR generates a dynamic one
2. Tailors style hints (colors, typography, layout, tone) to the audience
3. Produces audience-specific content guidance for the outline generator
"""

import json
import logging
from typing import Dict, List, Optional, Tuple

from .template_loader import get_template_presets

logger = logging.getLogger(__name__)

PERSONA_PROFILES = {
    "founder": {
        "label": "Startup Founder / CEO",
        "tone": "visionary, bold, high-energy",
        "priorities": ["traction", "market opportunity", "team", "ask"],
        "preferred_narratives": ["problem_solution_result"],
        "default_themes": ["startup_bold", "business_pitch", "tech_launch"],
    },
    "executive": {
        "label": "C-Suite / VP Executive",
        "tone": "authoritative, data-driven, strategic",
        "priorities": ["ROI", "KPIs", "strategic alignment", "risk mitigation"],
        "preferred_narratives": ["problem_solution_result", "comparison_analysis"],
        "default_themes": ["corporate_professional", "quarterly_review", "minimal_luxury"],
    },
    "educator": {
        "label": "Teacher / Professor / Trainer",
        "tone": "clear, engaging, pedagogical",
        "priorities": ["learning objectives", "examples", "retention", "assessment"],
        "preferred_narratives": ["chronological", "story_driven"],
        "default_themes": ["training", "education_chalkboard", "academic"],
    },
    "student": {
        "label": "Student (school / college)",
        "tone": "enthusiastic, clear, relatable",
        "priorities": ["clarity", "visuals", "engagement", "fun"],
        "preferred_narratives": ["story_driven", "chronological"],
        "default_themes": ["school_project", "flat_illustration", "doodle"],
    },
    "marketer": {
        "label": "Marketing / Brand Manager",
        "tone": "persuasive, trendy, visually rich",
        "priorities": ["brand story", "engagement metrics", "campaign results", "audience insights"],
        "preferred_narratives": ["story_driven", "problem_solution_result"],
        "default_themes": ["instagram", "gradient_mesh", "magazine"],
    },
    "engineer": {
        "label": "Software Engineer / Architect",
        "tone": "precise, technical, structured",
        "priorities": ["architecture", "performance", "trade-offs", "implementation"],
        "preferred_narratives": ["problem_solution_result", "comparison_analysis"],
        "default_themes": ["blueprint_technical", "neon_dark", "technical_report"],
    },
    "researcher": {
        "label": "Researcher / Scientist",
        "tone": "rigorous, evidence-based, methodical",
        "priorities": ["methodology", "findings", "significance", "reproducibility"],
        "preferred_narratives": ["chronological", "comparison_analysis"],
        "default_themes": ["academic", "academic_paper", "nordic_clean"],
    },
    "designer": {
        "label": "Designer / Creative Director",
        "tone": "aesthetic, conceptual, inspiring",
        "priorities": ["visual impact", "brand identity", "user experience", "innovation"],
        "preferred_narratives": ["story_driven"],
        "default_themes": ["glassmorphism", "3d_modern", "geometric_abstract"],
    },
    "sales": {
        "label": "Sales / Business Development",
        "tone": "persuasive, benefit-focused, urgent",
        "priorities": ["value proposition", "social proof", "objection handling", "close"],
        "preferred_narratives": ["problem_solution_result"],
        "default_themes": ["business_pitch", "dark_elegance", "startup_bold"],
    },
    "consultant": {
        "label": "Consultant / Advisor",
        "tone": "analytical, advisory, structured",
        "priorities": ["diagnosis", "recommendations", "implementation roadmap", "expected outcomes"],
        "preferred_narratives": ["problem_solution_result", "comparison_analysis"],
        "default_themes": ["corporate_professional", "minimal_luxury", "monochrome_bold"],
    },
}

AUDIENCE_PROFILES = {
    "investors": {
        "label": "Investors / VCs",
        "expectations": "ROI, traction, market size, team credibility",
        "attention_span": "short",
        "visual_preference": "clean, data-heavy, bold metrics",
        "content_depth": "high-level with drill-down data",
    },
    "executives": {
        "label": "C-Suite / Board Members",
        "expectations": "strategic impact, bottom-line results, risk",
        "attention_span": "very short",
        "visual_preference": "minimal, premium, data-driven",
        "content_depth": "executive summary with key metrics",
    },
    "technical": {
        "label": "Engineers / Developers",
        "expectations": "architecture, implementation details, trade-offs",
        "attention_span": "long (if relevant)",
        "visual_preference": "diagrams, code snippets, dark themes",
        "content_depth": "deep technical detail",
    },
    "general": {
        "label": "General / Mixed Audience",
        "expectations": "clarity, engagement, takeaways",
        "attention_span": "medium",
        "visual_preference": "balanced visuals and text",
        "content_depth": "accessible with supporting detail",
    },
    "students": {
        "label": "Students / Learners",
        "expectations": "clear explanations, examples, engagement",
        "attention_span": "medium",
        "visual_preference": "colorful, illustrative, fun",
        "content_depth": "progressive complexity",
    },
    "customers": {
        "label": "Customers / End Users",
        "expectations": "benefits, ease of use, social proof",
        "attention_span": "short",
        "visual_preference": "polished, brand-consistent, lifestyle",
        "content_depth": "benefit-focused, minimal jargon",
    },
    "peers": {
        "label": "Industry Peers / Conference",
        "expectations": "insights, novelty, credibility",
        "attention_span": "medium-long",
        "visual_preference": "professional, data-supported",
        "content_depth": "detailed with evidence",
    },
    "team": {
        "label": "Internal Team / Colleagues",
        "expectations": "alignment, action items, context",
        "attention_span": "medium",
        "visual_preference": "functional, clear, collaborative",
        "content_depth": "detailed with next steps",
    },
}


class PersonaEngine:
    """
    Analyzes presenter persona + target audience to recommend or dynamically
    generate the optimal theme, style hints, and content guidance.
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    def resolve_persona(self, persona_input: str) -> Dict:
        """
        Resolve a persona string to a profile. Supports both predefined keys
        and free-form descriptions.

        Returns a dict with: key, label, tone, priorities, preferred_narratives, default_themes
        """
        key = persona_input.strip().lower().replace(" ", "_")
        if key in PERSONA_PROFILES:
            return {"key": key, **PERSONA_PROFILES[key]}

        for k, profile in PERSONA_PROFILES.items():
            if k in key or key in profile["label"].lower():
                return {"key": k, **profile}

        return {
            "key": "custom",
            "label": persona_input.strip(),
            "tone": "professional, engaging",
            "priorities": [],
            "preferred_narratives": ["problem_solution_result"],
            "default_themes": ["business_pitch", "minimal_luxury"],
            "custom_description": persona_input.strip(),
        }

    def resolve_audience(self, audience_input: str) -> Dict:
        """
        Resolve an audience string to a profile. Supports predefined keys
        and free-form descriptions.
        """
        key = audience_input.strip().lower().replace(" ", "_")
        if key in AUDIENCE_PROFILES:
            return {"key": key, **AUDIENCE_PROFILES[key]}

        for k, profile in AUDIENCE_PROFILES.items():
            if k in key or key in profile["label"].lower():
                return {"key": k, **profile}

        return {
            "key": "custom",
            "label": audience_input.strip(),
            "expectations": "engagement, clarity",
            "attention_span": "medium",
            "visual_preference": "professional",
            "content_depth": "balanced",
            "custom_description": audience_input.strip(),
        }

    def recommend_theme(
        self,
        topic: str,
        persona: Dict,
        audience: Dict,
        user_theme: str = None,
    ) -> str:
        """
        Recommend the best existing template key given persona + audience + topic.
        If user explicitly set a theme, respect it.
        """
        if user_theme:
            presets = get_template_presets()
            if user_theme in presets:
                return user_theme

        preferred = persona.get("default_themes", [])
        if preferred:
            return preferred[0]

        return "business_pitch"

    def recommend_theme_with_llm(
        self,
        topic: str,
        persona: Dict,
        audience: Dict,
        model: str = "claude-sonnet-4-5-global",
    ) -> Tuple[str, Optional[Dict]]:
        """
        Use the LLM to pick the best template and optionally generate dynamic
        style overrides tailored to persona + audience.

        Returns:
            (template_key, dynamic_style_hints_or_None)
        """
        if not self.llm_client:
            return self.recommend_theme(topic, persona, audience), None

        presets = get_template_presets()
        catalog = "\n".join(
            f"  {k}: {v.get('name', k)} — {v.get('description', '')}"
            for k, v in presets.items()
        )

        prompt = f"""You are PresentiQ's theme advisor. Given the presenter persona, target audience, and topic, pick the BEST template and generate tailored style overrides.

TOPIC: "{topic}"

PRESENTER PERSONA:
  Role: {persona.get('label', 'Professional')}
  Tone: {persona.get('tone', 'professional')}
  Priorities: {', '.join(persona.get('priorities', ['clarity']))}

TARGET AUDIENCE:
  Who: {audience.get('label', 'General')}
  Expectations: {audience.get('expectations', 'clarity')}
  Attention span: {audience.get('attention_span', 'medium')}
  Visual preference: {audience.get('visual_preference', 'professional')}
  Content depth: {audience.get('content_depth', 'balanced')}

AVAILABLE TEMPLATES:
{catalog}

Return a JSON object with:
1. "template": The best template key from the list above.
2. "style_overrides": An object with optional overrides to tailor the template to this persona+audience:
   - "background": override background style (or null to keep default)
   - "typography": override typography (or null)
   - "colors": override color list (or null)
   - "layout": override layout guidance (or null)
   - "visual": override visual elements (or null)
   - "special": any special persona/audience instructions (or null)
3. "content_guidance": A short paragraph telling the outline generator how to structure content for this persona+audience combo.
4. "tone_directive": A one-line tone instruction for slide copy (e.g. "Use bold, action-oriented language with startup energy").

Return ONLY valid JSON. No markdown fences."""

        try:
            result = self.llm_client.generate_structured_response(
                system_prompt="You are a presentation design advisor. Return only valid JSON.",
                user_prompt=prompt,
                expected_structure="json",
                model=model,
                max_tokens=2000,
            )

            if isinstance(result, str):
                result = json.loads(result)

            template_key = result.get("template", "business_pitch")
            if template_key not in presets:
                template_key = self.recommend_theme(topic, persona, audience)

            style_overrides = result.get("style_overrides")
            if style_overrides:
                style_overrides = {
                    k: v for k, v in style_overrides.items() if v is not None
                }

            return template_key, {
                "style_overrides": style_overrides or {},
                "content_guidance": result.get("content_guidance", ""),
                "tone_directive": result.get("tone_directive", ""),
            }

        except Exception as e:
            logger.warning(f"LLM theme recommendation failed, using heuristic: {e}")
            return self.recommend_theme(topic, persona, audience), None

    def build_audience_profile(self, persona: Dict, audience: Dict) -> Dict:
        """
        Build a rich audience_profile dict compatible with PPTGenerator.generate_ppt().
        """
        return {
            "type": audience.get("label", "General Audience"),
            "expertise": self._infer_expertise(audience),
            "interests": audience.get("expectations", "General information"),
            "attention_span": audience.get("attention_span", "medium"),
            "visual_preference": audience.get("visual_preference", "professional"),
            "content_depth": audience.get("content_depth", "balanced"),
            "presenter_persona": persona.get("label", "Professional"),
            "presenter_tone": persona.get("tone", "professional"),
            "presenter_priorities": persona.get("priorities", []),
        }

    def merge_style_hints(
        self,
        base_hints: Optional[Dict],
        overrides: Optional[Dict],
    ) -> Optional[Dict]:
        """
        Merge dynamic style overrides on top of the template's base style_hints.
        Overrides only replace non-null fields.
        """
        if not base_hints and not overrides:
            return None
        if not overrides:
            return base_hints
        if not base_hints:
            return overrides

        merged = dict(base_hints)
        for key, value in overrides.items():
            if value is not None:
                merged[key] = value
        return merged

    def get_persona_list(self) -> List[Dict]:
        """Return all predefined personas for display."""
        return [
            {"key": k, "label": v["label"], "tone": v["tone"]}
            for k, v in PERSONA_PROFILES.items()
        ]

    def get_audience_list(self) -> List[Dict]:
        """Return all predefined audiences for display."""
        return [
            {"key": k, "label": v["label"], "expectations": v["expectations"]}
            for k, v in AUDIENCE_PROFILES.items()
        ]

    def _infer_expertise(self, audience: Dict) -> str:
        key = audience.get("key", "general")
        mapping = {
            "investors": "business",
            "executives": "business",
            "technical": "expert",
            "general": "general",
            "students": "beginner",
            "customers": "general",
            "peers": "expert",
            "team": "intermediate",
        }
        return mapping.get(key, "general")
