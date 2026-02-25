#!/usr/bin/env python3
"""
PresentiQ — Generate presentations from natural language.

Usage:
    python presentiq.py
    python presentiq.py "AI in Healthcare" --slides 10
    python presentiq.py "Startup pitch for a food delivery app" --slides 8 --theme startup_bold
    python presentiq.py "Climate change for kids" --slides 12 --theme school_project
    python presentiq.py "AI in Healthcare" --persona founder --audience investors
    python presentiq.py "React vs Vue" --persona engineer --audience technical --slides 8
    python presentiq.py --personas   # list all personas
    python presentiq.py --audiences  # list all audiences
"""

import argparse
import os
import sys
import json
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


TEMPLATE_CATALOG = {
    "business_pitch": "Fundraising decks, investor presentations",
    "corporate_professional": "Board meetings, enterprise presentations",
    "company_intro": "Brand storytelling, recruitment",
    "project_proposal": "Project kickoff, budget approval",
    "quarterly_review": "KPI reviews, OKR tracking",
    "fintech_modern": "Finance, crypto, banking",
    "startup_bold": "High-energy startup pitches",
    "tech_launch": "Apple/Google launch event style",
    "product_launch": "Feature demos, release announcements",
    "blueprint_technical": "Engineering, architecture deep-dives",
    "technical_report": "Architecture reviews, post-mortems",
    "neon_dark": "Developer talks, gaming",
    "data_dashboard_dark": "Data-heavy analytics presentations",
    "glassmorphism": "Frosted glass, modern UI",
    "gradient_mesh": "Vibrant mesh gradients, creative agencies",
    "3d_modern": "Dimensional graphics, futuristic",
    "geometric_abstract": "Bold shapes, abstract compositions",
    "flat_illustration": "Google/Dropbox style vector art",
    "pop_art": "Warhol/Lichtenstein comic style",
    "monochrome_bold": "High-contrast black & white",
    "watercolor_art": "Artistic hand-painted feel",
    "instagram": "Premium influencer aesthetic",
    "magazine": "Fashion editorial layout",
    "morandi": "Low-saturation premium grays",
    "muji_minimal": "Japanese natural minimalism",
    "minimal_luxury": "Apple Keynote style",
    "nordic_clean": "Scandinavian minimalism",
    "zen_japanese": "Wabi-sabi ink wash",
    "cyberpunk": "Neon grids, glitch art",
    "retro_80s": "Synthwave sunset nostalgia",
    "doodle": "Hand-drawn notebook style",
    "kawaii_cute": "Soft pastel, playful",
    "tropical_vibrant": "Lush tropical colors",
    "vintage": "Aged parchment, retro typography",
    "dark_elegance": "Charcoal + gold luxury",
    "pastel_dream": "Soft dreamy pastels",
    "space_cosmos": "Deep space nebula",
    "storytelling_cinematic": "Film-strip dramatic",
    "nature_earth": "Environment, sustainability",
    "healthcare_medical": "Medical, pharma, wellness",
    "education_chalkboard": "Classroom blackboard",
    "newspaper_editorial": "Journalism, editorial",
    "school_project": "Bright, fun student projects",
    "academic": "Conferences, thesis defense",
    "academic_paper": "NotebookLM-style research",
    "training": "Workshops, knowledge sharing",
}


def get_client():
    """Initialize the Anthropic client for content generation."""
    from anthropic import Anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    base_url = os.getenv("ANTHROPIC_BASE_URL")
    if not api_key:
        print("\n  Error: ANTHROPIC_API_KEY not set in .env")
        print("  Run: cp .env.example .env  and add your key\n")
        sys.exit(1)

    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return Anthropic(**kwargs)


def pick_template_and_expand(
    client,
    topic: str,
    num_slides: int,
    theme: str = None,
    persona_context: dict = None,
):
    """Use the LLM to pick the best template and generate rich reference content.

    Args:
        client: Anthropic client
        topic: Presentation topic
        num_slides: Number of slides
        theme: Explicit theme override (optional)
        persona_context: Dict with persona/audience guidance from PersonaEngine (optional)
    """
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-global")

    template_list = "\n".join(
        f"  {k}: {v}" for k, v in TEMPLATE_CATALOG.items()
    )

    persona_block = ""
    if persona_context:
        persona_block = "\nPERSONA & AUDIENCE CONTEXT:\n"
        if persona_context.get("presenter_persona"):
            persona_block += f"  Presenter: {persona_context['presenter_persona']}\n"
        if persona_context.get("presenter_tone"):
            persona_block += f"  Tone: {persona_context['presenter_tone']}\n"
        if persona_context.get("audience_label"):
            persona_block += f"  Target audience: {persona_context['audience_label']}\n"
        if persona_context.get("audience_expectations"):
            persona_block += f"  Audience expects: {persona_context['audience_expectations']}\n"
        if persona_context.get("content_depth"):
            persona_block += f"  Content depth: {persona_context['content_depth']}\n"
        if persona_context.get("content_guidance"):
            persona_block += f"  Content guidance: {persona_context['content_guidance']}\n"
        if persona_context.get("tone_directive"):
            persona_block += f"  Tone directive: {persona_context['tone_directive']}\n"

    prompt = f"""You are PresentiQ, an AI presentation assistant.

The user wants a presentation on this topic:
"{topic}"

Number of slides requested: {num_slides}
{"User-requested theme: " + theme if theme else "No theme specified — pick the best one."}
{persona_block}
AVAILABLE TEMPLATES:
{template_list}

YOUR TASK — return a JSON object with these exact keys:

1. "template": The best template key from the list above (string).
   {"Use '" + theme + "' since the user requested it." if theme else "Pick the template that best matches the topic and persona/audience."}

2. "style": A 2-3 sentence style description for the slides. Be specific about colors, mood, and visual feel.{' Tailor the style to the persona and audience described above.' if persona_context else ''}

3. "audience": A short audience description (e.g. "business executives", "college students", "general public").

4. "reference_text": A detailed, well-structured reference document (1500-2500 words) that covers the topic thoroughly.
   This will be used to generate {num_slides} slides, so include:
   - A clear title and subtitle
   - An introduction
   - 4-8 main sections with bullet points, examples, and data
   - Statistics or key numbers where relevant
   - A conclusion
   - Make the content engaging, informative, and well-organized.
   {"- IMPORTANT: Tailor the content tone, depth, and language to the persona and audience described above." if persona_context else ""}

Return ONLY valid JSON. No markdown fences, no explanation."""

    print("  Generating content from your topic...")

    response = client.messages.create(
        model=model,
        max_tokens=4000,
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.content[0].text.strip()

    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        raise


def show_themes():
    """Print all available themes grouped nicely."""
    groups = {
        "Business & Corporate": ["business_pitch", "corporate_professional", "company_intro",
                                  "project_proposal", "quarterly_review", "fintech_modern", "startup_bold"],
        "Tech & Product": ["tech_launch", "product_launch", "blueprint_technical",
                           "technical_report", "neon_dark", "data_dashboard_dark"],
        "Creative & Design": ["glassmorphism", "gradient_mesh", "3d_modern", "geometric_abstract",
                              "flat_illustration", "pop_art", "monochrome_bold", "watercolor_art"],
        "Lifestyle & Aesthetic": ["instagram", "magazine", "morandi", "muji_minimal",
                                  "minimal_luxury", "nordic_clean", "zen_japanese"],
        "Fun & Themed": ["cyberpunk", "retro_80s", "doodle", "kawaii_cute",
                         "tropical_vibrant", "vintage"],
        "Atmosphere & Mood": ["dark_elegance", "pastel_dream", "space_cosmos",
                              "storytelling_cinematic"],
        "Domain-Specific": ["nature_earth", "healthcare_medical", "education_chalkboard",
                            "newspaper_editorial", "school_project"],
        "Academic & Training": ["academic", "academic_paper", "training"],
    }

    print("\n  Available Themes (46):")
    print("  " + "-" * 56)
    for group_name, keys in groups.items():
        print(f"\n  [{group_name}]")
        for k in keys:
            desc = TEMPLATE_CATALOG.get(k, "")
            print(f"    {k:<28} {desc}")
    print()


def show_personas():
    """Print all available presenter personas."""
    from ppt_generator.persona_engine import PERSONA_PROFILES
    print("\n  Available Personas:")
    print("  " + "-" * 56)
    for key, p in PERSONA_PROFILES.items():
        print(f"    {key:<16} {p['label']:<32} ({p['tone']})")
    print()


def show_audiences():
    """Print all available target audiences."""
    from ppt_generator.persona_engine import AUDIENCE_PROFILES
    print("\n  Available Audiences:")
    print("  " + "-" * 56)
    for key, a in AUDIENCE_PROFILES.items():
        print(f"    {key:<16} {a['label']:<32} ({a['expectations'][:40]})")
    print()


def interactive_mode():
    """Run PresentiQ in interactive conversational mode."""
    print()
    print("  " + "=" * 56)
    print("  PresentiQ — AI Presentation Generator")
    print("  " + "=" * 56)
    print()
    print("  Just describe what you want. PresentiQ will handle the rest.")
    print("  Type 'themes' to see all 46 available themes.")
    print("  Type 'personas' to see presenter personas.")
    print("  Type 'audiences' to see target audiences.")
    print("  Type 'quit' to exit.")
    print()

    while True:
        print("  " + "-" * 56)
        topic = input("  What's your presentation about?\n  > ").strip()

        if not topic:
            continue
        if topic.lower() in ("quit", "exit", "q"):
            print("\n  Goodbye!\n")
            break
        if topic.lower() == "themes":
            show_themes()
            continue
        if topic.lower() == "personas":
            show_personas()
            continue
        if topic.lower() == "audiences":
            show_audiences()
            continue

        slides_input = input("  How many slides? (default: 10): ").strip()
        num_slides = int(slides_input) if slides_input.isdigit() else 10

        persona_input = input("  Your persona? (e.g. founder, engineer, educator — Enter to skip, 'personas' for list): ").strip()
        if persona_input.lower() == "personas":
            show_personas()
            persona_input = input("  Your persona? (Enter to skip): ").strip()
        persona = persona_input if persona_input and persona_input.lower() not in ("", "skip", "none") else None

        audience_input = input("  Target audience? (e.g. investors, technical, students — Enter to skip, 'audiences' for list): ").strip()
        if audience_input.lower() == "audiences":
            show_audiences()
            audience_input = input("  Target audience? (Enter to skip): ").strip()
        audience = audience_input if audience_input and audience_input.lower() not in ("", "skip", "none") else None

        theme_input = input("  Theme? (Enter for auto-pick, 'themes' for list): ").strip()
        if theme_input.lower() == "themes":
            show_themes()
            theme_input = input("  Theme? (Enter for auto-pick): ").strip()

        theme = theme_input if theme_input and theme_input.lower() not in ("", "auto", "none") else None

        if theme and theme not in TEMPLATE_CATALOG:
            print(f"  Unknown theme '{theme}'. Type 'themes' to see the list.")
            continue

        run_generation(topic, num_slides, theme, persona=persona, audience=audience)

        print()
        again = input("  Generate another? (y/n): ").strip().lower()
        if again != "y":
            print("\n  Goodbye!\n")
            break


def run_generation(topic: str, num_slides: int, theme: str = None, persona: str = None, audience: str = None):
    """Core generation pipeline: topic -> content -> slides -> PPTX.

    Args:
        topic: Presentation topic
        num_slides: Number of slides
        theme: Template theme key (optional, auto-detected if None)
        persona: Presenter persona key or free-form description (optional)
        audience: Target audience key or free-form description (optional)
    """
    from ppt_generator import PPTGenerator
    from ppt_generator.persona_engine import PersonaEngine
    from ppt_generator.template_loader import get_template_presets, register_dynamic_template

    print()
    print("  " + "=" * 56)
    print(f"  Topic:    {topic}")
    print(f"  Slides:   {num_slides}")
    print(f"  Persona:  {persona or 'default'}")
    print(f"  Audience: {audience or 'auto-detect'}")
    print(f"  Theme:    {theme or 'auto-detect'}")
    print("  " + "=" * 56)
    print()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    base_url = os.getenv("ANTHROPIC_BASE_URL")
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-global")

    # --- Persona & Audience resolution ---
    persona_context = None
    audience_profile_data = None
    dynamic_style_overrides = None

    if persona or audience:
        from ppt_generator.claude_client import ClaudeClient
        llm_for_persona = ClaudeClient(api_key)
        engine = PersonaEngine(llm_client=llm_for_persona)

        resolved_persona = engine.resolve_persona(persona) if persona else {
            "key": "default", "label": "Professional", "tone": "professional, engaging",
            "priorities": [], "preferred_narratives": ["problem_solution_result"],
            "default_themes": ["business_pitch"],
        }
        resolved_audience = engine.resolve_audience(audience) if audience else {
            "key": "general", "label": "General Audience", "expectations": "clarity, engagement",
            "attention_span": "medium", "visual_preference": "professional",
            "content_depth": "balanced",
        }

        print(f"  Persona:   {resolved_persona.get('label', persona)}")
        print(f"  Audience:  {resolved_audience.get('label', audience)}")

        # LLM-powered theme recommendation + style overrides
        print("  Analyzing persona & audience for optimal theme...")
        recommended_theme, llm_guidance = engine.recommend_theme_with_llm(
            topic, resolved_persona, resolved_audience, model=model,
        )

        if not theme:
            theme = recommended_theme
            print(f"  Auto-selected theme: {theme}")

        # Build persona context for content generation
        persona_context = {
            "presenter_persona": resolved_persona.get("label", ""),
            "presenter_tone": resolved_persona.get("tone", ""),
            "audience_label": resolved_audience.get("label", ""),
            "audience_expectations": resolved_audience.get("expectations", ""),
            "content_depth": resolved_audience.get("content_depth", "balanced"),
        }
        if llm_guidance:
            persona_context["content_guidance"] = llm_guidance.get("content_guidance", "")
            persona_context["tone_directive"] = llm_guidance.get("tone_directive", "")
            dynamic_style_overrides = llm_guidance.get("style_overrides")

        audience_profile_data = engine.build_audience_profile(resolved_persona, resolved_audience)

        # If LLM produced style overrides, merge them into the template's style_hints
        if dynamic_style_overrides:
            presets = get_template_presets()
            base_preset = presets.get(theme, {})
            base_hints = base_preset.get("style_hints", {})
            merged_hints = engine.merge_style_hints(base_hints, dynamic_style_overrides)
            if merged_hints and merged_hints != base_hints:
                dynamic_key = f"{theme}_persona"
                dynamic_template = dict(base_preset)
                dynamic_template["name"] = f"{base_preset.get('name', theme)} (Persona-tuned)"
                dynamic_template["style_hints"] = merged_hints
                register_dynamic_template(dynamic_key, dynamic_template)
                theme = dynamic_key
                print(f"  Created persona-tuned theme: {theme}")

        print()

    client = get_client()
    plan = pick_template_and_expand(client, topic, num_slides, theme, persona_context=persona_context)

    template = plan.get("template", theme or "business_pitch")
    style = plan.get("style", "Modern, clean, professional")
    audience_desc = plan.get("audience", "general audience")
    reference_text = plan.get("reference_text", topic)

    # Validate template — allow dynamic persona keys
    all_presets = get_template_presets()
    if template not in TEMPLATE_CATALOG and template not in all_presets:
        template = theme if theme and (theme in TEMPLATE_CATALOG or theme in all_presets) else "business_pitch"

    print(f"  Template:  {template}")
    print(f"  Audience:  {audience_desc}")
    print(f"  Style:     {style[:80]}...")
    print()
    print(f"  Rendering {num_slides} slides — this takes a few minutes...")
    print()

    generator = PPTGenerator(
        api_key=api_key,
        provider="Claude",
        base_url=base_url,
        enable_cache=True,
    )

    safe_name = "".join(c if c.isalnum() or c in " -_" else "" for c in topic)[:50].strip().replace(" ", "_")
    output_dir = f"output/{safe_name}"

    final_audience_profile = audience_profile_data or {
        "type": audience_desc,
        "expertise": "general",
    }

    result = generator.generate_ppt(
        reference_text=reference_text,
        style_requirements=style,
        output_dir=output_dir,
        model=model,
        template_preset=template,
        audience_profile=final_audience_profile,
        persona_context=persona_context,
        use_cache=False,
    )

    print()
    print("  " + "=" * 56)
    print("  Done!")
    print("  " + "=" * 56)
    print(f"  Slides:    {result['success_slides']}/{result['total_slides']}")
    print(f"  PPTX:      {result['pptx_file']}")
    print(f"  Outline:   {result['outline_file']}")

    if result.get("error_slides"):
        print(f"\n  Failed slides:")
        for err in result["error_slides"]:
            print(f"    Slide {err['page']}: {err['error'][:80]}")

    print()
    return result


def main():
    parser = argparse.ArgumentParser(
        prog="presentiq",
        description="PresentiQ — Generate presentations from natural language",
        epilog="Examples:\n"
               "  python presentiq.py\n"
               '  python presentiq.py "AI in Healthcare"\n'
               '  python presentiq.py "Startup pitch for food delivery" --slides 8 --theme startup_bold\n'
               '  python presentiq.py "AI in Healthcare" --persona founder --audience investors\n'
               '  python presentiq.py "React vs Vue" --persona engineer --audience technical --slides 8\n'
               '  python presentiq.py "Climate change" --slides 12 --theme nature_earth\n',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("topic", nargs="?", default=None,
                        help="Presentation topic in natural language")
    parser.add_argument("--slides", "-n", type=int, default=10,
                        help="Number of slides (default: 10)")
    parser.add_argument("--theme", "-t", type=str, default=None,
                        help="Template theme (default: auto-detect from topic)")
    parser.add_argument("--persona", "-p", type=str, default=None,
                        help="Presenter persona (e.g. founder, engineer, educator, marketer)")
    parser.add_argument("--audience", "-a", type=str, default=None,
                        help="Target audience (e.g. investors, technical, students, executives)")
    parser.add_argument("--themes", action="store_true",
                        help="List all available themes and exit")
    parser.add_argument("--personas", action="store_true",
                        help="List all available personas and exit")
    parser.add_argument("--audiences", action="store_true",
                        help="List all available target audiences and exit")

    args = parser.parse_args()

    if args.themes:
        show_themes()
        return
    if args.personas:
        show_personas()
        return
    if args.audiences:
        show_audiences()
        return

    if args.topic:
        run_generation(args.topic, args.slides, args.theme, persona=args.persona, audience=args.audience)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
