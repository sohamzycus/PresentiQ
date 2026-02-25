#!/usr/bin/env python3
"""
PresentiQ Web UI — Professional web interface for presentation generation.

Usage:
    python app.py                  # Start on http://localhost:5000
    python app.py --port 8080      # Custom port
"""

import argparse
import json
import logging
import os
import queue
import sys
import threading
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_file, Response

load_dotenv()

# Ensure Playwright finds its browsers reliably across environments.
# Docker sets PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers via env.
# On macOS (local dev), fall back to the standard cache location to avoid
# Cursor sandbox arch mismatches.
if not os.environ.get("PLAYWRIGHT_BROWSERS_PATH"):
    candidates = [
        os.path.join(os.path.expanduser("~"), "Library", "Caches", "ms-playwright"),  # macOS
        os.path.join(os.path.expanduser("~"), ".cache", "ms-playwright"),              # Linux
    ]
    for path in candidates:
        if os.path.isdir(path):
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = path
            break

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

JOBS: dict = {}

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

THEME_GROUPS = {
    "Business & Corporate": [
        "business_pitch", "corporate_professional", "company_intro",
        "project_proposal", "quarterly_review", "fintech_modern", "startup_bold",
    ],
    "Tech & Product": [
        "tech_launch", "product_launch", "blueprint_technical",
        "technical_report", "neon_dark", "data_dashboard_dark",
    ],
    "Creative & Design": [
        "glassmorphism", "gradient_mesh", "3d_modern", "geometric_abstract",
        "flat_illustration", "pop_art", "monochrome_bold", "watercolor_art",
    ],
    "Lifestyle & Aesthetic": [
        "instagram", "magazine", "morandi", "muji_minimal",
        "minimal_luxury", "nordic_clean", "zen_japanese",
    ],
    "Fun & Themed": [
        "cyberpunk", "retro_80s", "doodle", "kawaii_cute",
        "tropical_vibrant", "vintage",
    ],
    "Atmosphere & Mood": [
        "dark_elegance", "pastel_dream", "space_cosmos",
        "storytelling_cinematic",
    ],
    "Domain-Specific": [
        "nature_earth", "healthcare_medical", "education_chalkboard",
        "newspaper_editorial", "school_project",
    ],
    "Academic & Training": ["academic", "academic_paper", "training"],
}


def _emit(job_id: str, event: str, data: dict):
    """Push an SSE event to the job's queue."""
    job = JOBS.get(job_id)
    if job and "queue" in job:
        job["queue"].put({"event": event, "data": data})


def _run_generation(job_id: str, topic: str, num_slides: int, theme: str, persona: str, audience: str):
    """Background thread: runs the full generation pipeline, emitting progress via SSE."""
    from ppt_generator import PPTGenerator
    from ppt_generator.persona_engine import PersonaEngine
    from ppt_generator.template_loader import get_template_presets, register_dynamic_template

    api_key = os.getenv("ANTHROPIC_API_KEY")
    base_url = os.getenv("ANTHROPIC_BASE_URL")
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-global")

    if not api_key:
        _emit(job_id, "error", {"message": "ANTHROPIC_API_KEY not set. Configure your .env file."})
        return

    try:
        persona_context = None
        audience_profile_data = None

        # --- Persona & Audience ---
        if persona or audience:
            _emit(job_id, "progress", {"step": "persona", "message": "Analyzing persona & audience..."})
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

            recommended_theme, llm_guidance = engine.recommend_theme_with_llm(
                topic, resolved_persona, resolved_audience, model=model,
            )

            if not theme:
                theme = recommended_theme

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
            else:
                dynamic_style_overrides = None

            audience_profile_data = engine.build_audience_profile(resolved_persona, resolved_audience)

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

            _emit(job_id, "progress", {
                "step": "persona_done",
                "message": f"Persona: {resolved_persona.get('label', '')} | Audience: {resolved_audience.get('label', '')} | Theme: {theme}",
            })

        # --- Content generation ---
        _emit(job_id, "progress", {"step": "content", "message": "Generating content from your topic..."})

        from anthropic import Anthropic
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        client = Anthropic(**kwargs)

        from presentiq import pick_template_and_expand, TEMPLATE_CATALOG as TC
        plan = pick_template_and_expand(client, topic, num_slides, theme, persona_context=persona_context)

        template = plan.get("template", theme or "business_pitch")
        style = plan.get("style", "Modern, clean, professional")
        audience_desc = plan.get("audience", "general audience")
        reference_text = plan.get("reference_text", topic)

        all_presets = get_template_presets()
        if template not in TC and template not in all_presets:
            template = theme if theme and (theme in TC or theme in all_presets) else "business_pitch"

        _emit(job_id, "progress", {
            "step": "content_done",
            "message": f"Template: {template} | Style: {style[:60]}...",
        })

        # --- Slide rendering ---
        _emit(job_id, "progress", {
            "step": "rendering",
            "message": f"Rendering {num_slides} slides — this takes a few minutes...",
        })

        generator = PPTGenerator(
            api_key=api_key, provider="Claude", base_url=base_url, enable_cache=True,
        )

        safe_name = "".join(c if c.isalnum() or c in " -_" else "" for c in topic)[:50].strip().replace(" ", "_")
        output_dir = f"output/{safe_name}"

        final_audience_profile = audience_profile_data or {"type": audience_desc, "expertise": "general"}

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

        _emit(job_id, "complete", {
            "pptx_file": result["pptx_file"],
            "outline_file": result["outline_file"],
            "total_slides": result["total_slides"],
            "success_slides": result["success_slides"],
            "error_slides": result.get("error_slides", []),
            "template": template,
            "style": style,
        })

    except Exception as e:
        logger.exception("Generation failed")
        _emit(job_id, "error", {"message": str(e)})


# ─── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/options")
def api_options():
    """Return all personas, audiences, and themes for the UI dropdowns."""
    from ppt_generator.persona_engine import PERSONA_PROFILES, AUDIENCE_PROFILES

    personas = [
        {"key": k, "label": v["label"], "tone": v["tone"]}
        for k, v in PERSONA_PROFILES.items()
    ]
    audiences = [
        {"key": k, "label": v["label"], "expectations": v["expectations"]}
        for k, v in AUDIENCE_PROFILES.items()
    ]
    themes = []
    for group_name, keys in THEME_GROUPS.items():
        for k in keys:
            themes.append({"key": k, "label": k.replace("_", " ").title(), "group": group_name, "description": TEMPLATE_CATALOG.get(k, "")})

    return jsonify({"personas": personas, "audiences": audiences, "themes": themes})


@app.route("/api/generate", methods=["POST"])
def api_generate():
    """Start a generation job. Returns a job_id for SSE streaming."""
    data = request.get_json(force=True)
    topic = data.get("topic", "").strip()
    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    num_slides = int(data.get("slides", 10))
    theme = data.get("theme", "").strip() or None
    persona = data.get("persona", "").strip() or None
    audience = data.get("audience", "").strip() or None

    job_id = str(uuid.uuid4())
    JOBS[job_id] = {"status": "running", "queue": queue.Queue()}

    thread = threading.Thread(
        target=_run_generation,
        args=(job_id, topic, num_slides, theme, persona, audience),
        daemon=True,
    )
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/api/stream/<job_id>")
def api_stream(job_id):
    """SSE endpoint — streams progress events for a generation job."""
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    def generate():
        q = job["queue"]
        while True:
            try:
                msg = q.get(timeout=120)
                yield f"event: {msg['event']}\ndata: {json.dumps(msg['data'])}\n\n"
                if msg["event"] in ("complete", "error"):
                    break
            except queue.Empty:
                yield f"event: ping\ndata: {{}}\n\n"

    return Response(generate(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


@app.route("/api/download")
def api_download():
    """Download a generated PPTX file."""
    filepath = request.args.get("path", "")
    if not filepath or not os.path.isfile(filepath):
        return jsonify({"error": "File not found"}), 404
    return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))


# ─── Entry ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="PresentiQ Web UI")
    parser.add_argument("--port", type=int, default=5000, help="Port (default: 5000)")
    parser.add_argument("--host", type=str, default=os.getenv("HOST", "127.0.0.1"),
                        help="Host (default: 127.0.0.1, or HOST env var)")
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()

    print()
    print("  " + "=" * 52)
    print("  PresentiQ Web UI")
    print("  " + "=" * 52)
    print(f"  Open http://{args.host}:{args.port} in your browser")
    print("  " + "=" * 52)
    print()

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
