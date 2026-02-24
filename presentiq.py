#!/usr/bin/env python3
"""
PresentiQ — Generate presentations from natural language.

Usage:
    python presentiq.py
    python presentiq.py "AI in Healthcare" --slides 10
    python presentiq.py "Startup pitch for a food delivery app" --slides 8 --theme startup_bold
    python presentiq.py "Climate change for kids" --slides 12 --theme school_project
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


def pick_template_and_expand(client, topic: str, num_slides: int, theme: str = None):
    """Use the LLM to pick the best template and generate rich reference content."""
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-global")

    template_list = "\n".join(
        f"  {k}: {v}" for k, v in TEMPLATE_CATALOG.items()
    )

    prompt = f"""You are PresentiQ, an AI presentation assistant.

The user wants a presentation on this topic:
"{topic}"

Number of slides requested: {num_slides}
{"User-requested theme: " + theme if theme else "No theme specified — pick the best one."}

AVAILABLE TEMPLATES:
{template_list}

YOUR TASK — return a JSON object with these exact keys:

1. "template": The best template key from the list above (string).
   {"Use '" + theme + "' since the user requested it." if theme else "Pick the template that best matches the topic."}

2. "style": A 2-3 sentence style description for the slides. Be specific about colors, mood, and visual feel.

3. "audience": A short audience description (e.g. "business executives", "college students", "general public").

4. "reference_text": A detailed, well-structured reference document (1500-2500 words) that covers the topic thoroughly.
   This will be used to generate {num_slides} slides, so include:
   - A clear title and subtitle
   - An introduction
   - 4-8 main sections with bullet points, examples, and data
   - Statistics or key numbers where relevant
   - A conclusion
   - Make the content engaging, informative, and well-organized.

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


def interactive_mode():
    """Run PresentiQ in interactive conversational mode."""
    print()
    print("  " + "=" * 56)
    print("  PresentiQ — AI Presentation Generator")
    print("  " + "=" * 56)
    print()
    print("  Just describe what you want. PresentiQ will handle the rest.")
    print("  Type 'themes' to see all 46 available themes.")
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

        slides_input = input("  How many slides? (default: 10): ").strip()
        num_slides = int(slides_input) if slides_input.isdigit() else 10

        theme_input = input("  Theme? (press Enter for auto-pick, or type 'themes' to see list): ").strip()
        if theme_input.lower() == "themes":
            show_themes()
            theme_input = input("  Theme? (press Enter for auto-pick): ").strip()

        theme = theme_input if theme_input and theme_input.lower() not in ("", "auto", "none") else None

        if theme and theme not in TEMPLATE_CATALOG:
            print(f"  Unknown theme '{theme}'. Type 'themes' to see the list.")
            continue

        run_generation(topic, num_slides, theme)

        print()
        again = input("  Generate another? (y/n): ").strip().lower()
        if again != "y":
            print("\n  Goodbye!\n")
            break


def run_generation(topic: str, num_slides: int, theme: str = None):
    """Core generation pipeline: topic -> content -> slides -> PPTX."""
    from ppt_generator import PPTGenerator

    print()
    print("  " + "=" * 56)
    print(f"  Topic:  {topic}")
    print(f"  Slides: {num_slides}")
    print(f"  Theme:  {theme or 'auto-detect'}")
    print("  " + "=" * 56)
    print()

    client = get_client()
    plan = pick_template_and_expand(client, topic, num_slides, theme)

    template = plan.get("template", "business_pitch")
    style = plan.get("style", "Modern, clean, professional")
    audience = plan.get("audience", "general audience")
    reference_text = plan.get("reference_text", topic)

    if template not in TEMPLATE_CATALOG:
        template = "business_pitch"

    print(f"  Template:  {template}")
    print(f"  Audience:  {audience}")
    print(f"  Style:     {style[:80]}...")
    print()
    print(f"  Rendering {num_slides} slides — this takes a few minutes...")
    print()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    base_url = os.getenv("ANTHROPIC_BASE_URL")
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-global")

    generator = PPTGenerator(
        api_key=api_key,
        provider="Claude",
        base_url=base_url,
        enable_cache=True,
    )

    safe_name = "".join(c if c.isalnum() or c in " -_" else "" for c in topic)[:50].strip().replace(" ", "_")
    output_dir = f"output/{safe_name}"

    result = generator.generate_ppt(
        reference_text=reference_text,
        style_requirements=style,
        output_dir=output_dir,
        model=model,
        template_preset=template,
        audience_profile={
            "type": audience,
            "expertise": "general",
        },
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
               '  python presentiq.py "Climate change" --slides 12 --theme nature_earth\n',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("topic", nargs="?", default=None,
                        help="Presentation topic in natural language")
    parser.add_argument("--slides", "-n", type=int, default=10,
                        help="Number of slides (default: 10)")
    parser.add_argument("--theme", "-t", type=str, default=None,
                        help="Template theme (default: auto-detect from topic)")
    parser.add_argument("--themes", action="store_true",
                        help="List all available themes and exit")

    args = parser.parse_args()

    if args.themes:
        show_themes()
        return

    if args.topic:
        run_generation(args.topic, args.slides, args.theme)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
