# PresentiQ

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**PresentiQ** is an AI-powered presentation generator that transforms text into professional slide decks. It uses a single LLM (Claude / GPT / DeepSeek) for **both** intelligent outline generation **and** slide rendering — no separate image-generation API required.

Slides are rendered as pixel-perfect HTML/CSS by the LLM, then screenshotted to PNG via headless Chromium (Playwright). This gives crisp text, exact layouts, and full control over typography and colors — far better than AI image generators for presentation content.

## Key Features

- **Natural Language Input** — Just describe your topic; PresentiQ generates the full presentation
- **Persona & Audience Targeting** — Define who you are and who you're presenting to; PresentiQ adapts theme, tone, content depth, and visuals automatically
- **Auto Theme Detection** — AI picks the best template from 46 presets based on your topic, persona, and audience
- **Dynamic Theme Generation** — When no preset fits perfectly, PresentiQ creates a persona-tuned theme on the fly
- **Two-Stage Outline Generation** — Analyzes document structure first, then generates a precise outline
- **HTML/CSS Slide Rendering** — LLM produces self-contained HTML for each slide; Playwright screenshots it to PNG
- **Style-Anchored Batch Generation** — Generates the title slide first to establish a visual style, then enforces consistency
- **46 Template Presets** — Business, tech, creative, lifestyle, academic, and niche styles
- **Smart Caching** — Caches outlines and images to avoid redundant generation
- **Intelligent Error Handling** — Automatic retries, prompt simplification, and graceful fallbacks
- **Custom Templates** — Create your own via simple YAML files
- **Editable Slides** — Append fully editable text slides (team members, thank you, etc.)

## Quick Start

### 1. Install

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env` with your API key:

```env
ANTHROPIC_API_KEY=your-api-key
ANTHROPIC_BASE_URL=https://api.anthropic.com
ANTHROPIC_MODEL=claude-sonnet-4-5-global
```

### 3. Generate a Presentation

**One-liner — just describe what you want:**

```bash
python presentiq.py "AI in Healthcare" --slides 10
```

**Pick a specific theme:**

```bash
python presentiq.py "Startup pitch for a food delivery app" --slides 8 --theme startup_bold
```

**Define your persona and audience — theme auto-adapts:**

```bash
python presentiq.py "AI in Healthcare" --persona founder --audience investors
python presentiq.py "React vs Vue" --persona engineer --audience technical --slides 8
python presentiq.py "Q4 Results" --persona executive --audience executives --slides 6
python presentiq.py "Photosynthesis" --persona educator --audience students --slides 12
```

**Interactive mode — PresentiQ asks you questions:**

```bash
python presentiq.py
```

**See all options:**

```bash
python presentiq.py --themes      # 46 available themes
python presentiq.py --personas    # 10 presenter personas
python presentiq.py --audiences   # 8 target audiences
```

That's it. No Python code to write. Describe your topic, define who you are and who you're presenting to, and PresentiQ handles the rest — persona-aware content generation, intelligent template selection, slide design, and PPTX export.

### Full Setup (with virtual environment)

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt
playwright install chromium

# Generate a presentation
python presentiq.py "Climate change for kids" --slides 12 --theme school_project
```

### Other Run Options

```bash
# Interactive template picker with sample content
python example.py

# Pre-built school project demo (Ravi's AI story, 15 slides)
python run_ai_citizen_services.py
```

## Programmatic Usage

```python
from ppt_generator import PPTGenerator
import os

generator = PPTGenerator(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    provider="Claude",
    base_url=os.getenv("ANTHROPIC_BASE_URL"),
)

result = generator.generate_ppt(
    reference_text="Your content text...",
    style_requirements="Tech style, blue theme, modern and minimal",
    output_dir="output",
    model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-global"),
    template_preset="business_pitch",
)

print(f"Done: {result['pptx_file']}")
```

### Adding Editable Slides

Append fully editable text slides (team members, thank you, custom) after the generated image slides:

```python
extra_slides = [
    {
        "type": "team_members",
        "title": "Our Team",
        "subtitle": "Project Contributors",
        "items": ["Alice", "Bob", "Charlie"],
        "bg_color": (79, 195, 247),
        "text_color": (255, 255, 255),
    },
    {
        "type": "thank_you",
        "title": "Thank You!",
        "subtitle": "Questions?",
        "bg_color": (102, 187, 106),
        "text_color": (255, 255, 255),
    },
]

result = generator.generate_ppt(
    reference_text=text,
    style_requirements=style,
    template_preset="startup_bold",
    _extra_slides=extra_slides,
)
```

## How It Works

```
1. Check Cache
   +-- Cached outline found -> use it
   +-- Otherwise -> two-stage outline generation

2. Two-Stage Outline Generation
   +-- Stage 1: DocumentAnalyzer -- understand document type, sections, data points
   +-- Stage 2: OutlineGenerator -- produce structured JSON outline from analysis

3. Style-Anchored Slide Rendering
   +-- Generate title slide first -> establish visual style anchor
   +-- Group remaining slides by type
   +-- Generate slides in parallel (configurable concurrency)
       +-- Each slide:
           a. Check image cache
           b. Ask LLM to produce self-contained HTML/CSS
           c. Screenshot with Playwright (headless Chromium) -> PNG

4. Save PPT
   +-- Insert PNG images into slides
   +-- Append editable text slides (if any)
   +-- Save .pptx + outline JSON
```

## Template Library (46 Presets)

### Business & Corporate

| Preset Key | Name | Use Case |
|---|---|---|
| `business_pitch` | Business Pitch | Fundraising decks, investor presentations |
| `corporate_professional` | Corporate Professional | Board meetings, enterprise presentations |
| `company_intro` | Company Introduction | Brand storytelling, recruitment |
| `project_proposal` | Project Proposal | Kickoff, budget approval |
| `quarterly_review` | Quarterly Review | KPI reviews, OKR tracking |
| `fintech_modern` | Fintech Modern | Finance, crypto, banking |
| `startup_bold` | Startup Bold | High-energy startup pitches |

### Tech & Product

| Preset Key | Name | Use Case |
|---|---|---|
| `tech_launch` | Tech Launch | Apple/Google launch event style |
| `product_launch` | Product Launch | Feature demos, release announcements |
| `blueprint_technical` | Blueprint Technical | Engineering, architecture deep-dives |
| `technical_report` | Technical Report | Architecture reviews, post-mortems |
| `neon_dark` | Neon Dark | Developer talks, gaming |
| `data_dashboard_dark` | Data Dashboard Dark | Data-heavy analytics presentations |

### Creative & Design

| Preset Key | Name | Style |
|---|---|---|
| `glassmorphism` | Glassmorphism | Frosted glass, modern UI |
| `gradient_mesh` | Gradient Mesh | Vibrant mesh gradients |
| `3d_modern` | 3D Modern | Dimensional graphics, futuristic |
| `geometric_abstract` | Geometric Abstract | Bold shapes, abstract compositions |
| `flat_illustration` | Flat Illustration | Google/Dropbox style vector art |
| `pop_art` | Pop Art | Warhol/Lichtenstein comic style |
| `monochrome_bold` | Monochrome Bold | High-contrast black & white |
| `watercolor_art` | Watercolor Art | Artistic hand-painted feel |

### Lifestyle & Aesthetic

| Preset Key | Name | Style |
|---|---|---|
| `instagram` | Instagram Style | Premium influencer aesthetic |
| `magazine` | Magazine Style | Fashion editorial layout |
| `morandi` | Morandi | Low-saturation premium grays |
| `muji_minimal` | MUJI Minimal | Japanese natural minimalism |
| `minimal_luxury` | Minimal Luxury | Apple Keynote style |
| `nordic_clean` | Nordic Clean | Scandinavian minimalism |
| `zen_japanese` | Zen Japanese | Wabi-sabi ink wash |

### Fun & Themed

| Preset Key | Name | Style |
|---|---|---|
| `cyberpunk` | Cyberpunk | Neon grids, glitch art |
| `retro_80s` | Retro 80s | Synthwave sunset nostalgia |
| `doodle` | Hand-drawn Doodle | Notebook sketch style |
| `kawaii_cute` | Kawaii Cute | Soft pastel, playful |
| `tropical_vibrant` | Tropical Vibrant | Lush tropical colors |
| `vintage` | Vintage Retro | Aged parchment, retro typography |

### Atmosphere & Mood

| Preset Key | Name | Style |
|---|---|---|
| `dark_elegance` | Dark Elegance | Charcoal + gold luxury |
| `pastel_dream` | Pastel Dream | Soft dreamy pastels |
| `space_cosmos` | Space & Cosmos | Deep space nebula |
| `storytelling_cinematic` | Storytelling Cinematic | Film-strip dramatic |

### Domain-Specific

| Preset Key | Name | Use Case |
|---|---|---|
| `nature_earth` | Nature & Earth | Environment, sustainability |
| `healthcare_medical` | Healthcare & Medical | Medical, pharma, wellness |
| `education_chalkboard` | Education Chalkboard | Classroom blackboard |
| `newspaper_editorial` | Newspaper Editorial | Journalism, editorial |
| `school_project` | School Project | Bright, fun student projects |

### Academic & Training

| Preset Key | Name | Use Case |
|---|---|---|
| `academic` | Academic Presentation | Conferences, thesis defense |
| `academic_paper` | Academic Paper | NotebookLM-style research |
| `training` | Training Course | Workshops, knowledge sharing |

## Persona & Audience System

PresentiQ's persona engine adapts every aspect of the presentation — theme selection, content tone, visual style, and information density — based on who you are and who you're presenting to.

### Presenter Personas (10 built-in)

| Key | Role | Tone |
|---|---|---|
| `founder` | Startup Founder / CEO | Visionary, bold, high-energy |
| `executive` | C-Suite / VP Executive | Authoritative, data-driven, strategic |
| `educator` | Teacher / Professor / Trainer | Clear, engaging, pedagogical |
| `student` | Student (school / college) | Enthusiastic, clear, relatable |
| `marketer` | Marketing / Brand Manager | Persuasive, trendy, visually rich |
| `engineer` | Software Engineer / Architect | Precise, technical, structured |
| `researcher` | Researcher / Scientist | Rigorous, evidence-based, methodical |
| `designer` | Designer / Creative Director | Aesthetic, conceptual, inspiring |
| `sales` | Sales / Business Development | Persuasive, benefit-focused, urgent |
| `consultant` | Consultant / Advisor | Analytical, advisory, structured |

### Target Audiences (8 built-in)

| Key | Audience | Expectations |
|---|---|---|
| `investors` | Investors / VCs | ROI, traction, market size, team credibility |
| `executives` | C-Suite / Board Members | Strategic impact, bottom-line results, risk |
| `technical` | Engineers / Developers | Architecture, implementation details, trade-offs |
| `general` | General / Mixed Audience | Clarity, engagement, takeaways |
| `students` | Students / Learners | Clear explanations, examples, engagement |
| `customers` | Customers / End Users | Benefits, ease of use, social proof |
| `peers` | Industry Peers / Conference | Insights, novelty, credibility |
| `team` | Internal Team / Colleagues | Alignment, action items, context |

### How It Works

1. **Persona resolution** — Maps your role to tone, priorities, and preferred themes
2. **Audience analysis** — Determines content depth, visual preference, and attention span
3. **LLM-powered theme selection** — AI picks the best template considering persona + audience + topic
4. **Dynamic style overrides** — Generates persona-tuned style hints (colors, typography, layout) that overlay the base template
5. **Content adaptation** — Outline generator adjusts language, data density, and narrative structure
6. **Slide rendering** — Each slide prompt includes persona/audience context for consistent tone

You can also pass free-form descriptions instead of predefined keys:

```bash
python presentiq.py "Kubernetes Migration" --persona "DevOps lead at a fintech startup" --audience "VP of Engineering and CTO"
```

## Custom Templates

Add a YAML file under `configs/templates/` to create your own template:

```yaml
# configs/templates/my_template.yaml
name: "My Template"
description: "A custom dark-blue gradient template"
sequence:
  - title
  - toc
  - content
  - content
  - data_dashboard
  - conclusion_cta
narrative: "problem_solution_result"
suggested_slides: 6

style_hints:
  background: "Deep blue gradient background"
  typography: "Modern sans-serif, bold headings"
  colors:
    - "#1a1a2e"
    - "#16213e"
    - "#0f3460"
    - "#e94560"
  layout: "Left text, right image, generous whitespace"
  visual: "Tech icons, data visualizations"
```

Use it:

```python
result = generator.generate_ppt(
    reference_text=your_text,
    style_requirements=your_style,
    template_preset="my_template",  # matches my_template.yaml
)
```

### Available Slide Types

| Type | Description |
|---|---|
| `title` | Title slide |
| `toc` | Table of contents |
| `content` | Standard content slide |
| `problem_solution` | Problem vs. solution comparison |
| `data_dashboard` | Data dashboard with charts |
| `timeline` | Timeline / roadmap |
| `comparison` | Side-by-side comparison |
| `case_study` | Case study |
| `conclusion_cta` | Summary / call to action |
| `transition` | Transition slide |

## Advanced Usage

### List Available Presets

```python
for preset in generator.list_template_presets():
    print(f"{preset['key']}: {preset['name']} - {preset['description']}")
```

### Cache Management

```python
stats = generator.get_cache_stats()
print(f"Outline cache: {stats['outline_count']} entries")
print(f"Image cache: {stats['image_count']} entries")

generator.clear_cache(older_than_days=7)
```

### Hot-Reload Templates

```python
from ppt_generator.template_loader import reload_templates

reload_templates()
```

## Project Structure

```
PresentiQ/
+-- configs/
|   +-- templates/                  # YAML template configs (46 built-in)
+-- ppt_generator/
|   +-- __init__.py                 # Main entry -- PPTGenerator class
|   +-- persona_engine.py           # Persona & audience targeting engine
|   +-- outline_generator.py        # Two-stage outline generation
|   +-- document_analyzer.py        # Document structure analysis
|   +-- html_renderer.py            # LLM -> HTML/CSS -> Playwright -> PNG
|   +-- slide_generator_official.py # Slide generation orchestration
|   +-- batch_generator.py          # Batch generation with style anchoring
|   +-- prompt_templates.py         # Prompt template system
|   +-- template_loader.py          # YAML template loader + dynamic templates
|   +-- cache_manager.py            # Cache management
|   +-- error_handler.py            # Smart error handling & retries
|   +-- claude_client.py            # Unified AI client (Claude / OpenAI / DeepSeek)
+-- presentiq.py                    # CLI entry point (natural language input)
+-- example.py                      # Interactive template picker demo
+-- run_ai_citizen_services.py      # Sample: school project generator
+-- requirements.txt                # Dependencies
+-- .env.example                    # Environment variable template
+-- README.md
```

## Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | Claude (Anthropic) / GPT (OpenAI) / DeepSeek |
| **Slide Rendering** | LLM-generated HTML/CSS -> Playwright (headless Chromium) -> PNG |
| **PPT Assembly** | python-pptx |
| **Async** | asyncio |
| **Validation** | Pydantic |
| **Config** | python-dotenv, PyYAML |

## Roadmap

- [x] 46 template presets across 8 categories
- [x] Custom templates via YAML
- [x] HTML/CSS slide rendering (no image-generation API needed)
- [x] Editable text slides (team members, thank you, custom)
- [x] Persona & audience targeting with dynamic theme generation
- [ ] Reference image style transfer — upload an image, generate slides in that style
- [ ] Live preview during generation
- [ ] Export to PDF and image sequences
- [ ] Auto-generated speaker notes

## License

MIT
