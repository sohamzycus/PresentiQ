"""
PresentiQ — Interactive Demo

Features:
- Two-stage outline generation (document analysis -> outline generation)
- Style-anchored batch image generation
- Caching mechanism (outline + images)
- Smart error handling and fallback
- 46 template presets supported
"""

from ppt_generator import PPTGenerator
import os


# ==================== Sample Content Library ====================

SAMPLE_CONTENTS = {
    "ai_tech": {
        "name": "AI Technology Overview",
        "text": """
The Development and Applications of Artificial Intelligence

Artificial Intelligence (AI) is a branch of computer science dedicated to creating machines that can simulate human intelligence.

AI Development Timeline:
1. 1956: Dartmouth Conference, AI concept formally introduced
2. 1960s-1970s: Early AI research, symbolic AI emerges
3. 1980s: Commercialization of expert systems
4. 2010s: Deep learning revolution, AlphaGo defeats world Go champion
5. 2020s: Large language model era, ChatGPT sparks AI boom

Current AI Technology Domains:
- Machine Learning: Supervised, unsupervised, reinforcement learning
- Deep Learning: Neural networks, CNNs, Transformers
- Natural Language Processing: Text understanding, machine translation, dialogue systems
- Computer Vision: Image recognition, object detection, image generation

AI Applications:
1. Healthcare: Disease diagnosis, drug discovery
2. Financial Services: Risk assessment, algorithmic trading
3. Autonomous Driving: Path planning, environment perception
4. Smart Assistants: Voice interaction, task execution

Future Outlook:
- Exploration of Artificial General Intelligence (AGI)
- Deep integration of AI across industries
- AI ethics and safety standards
        """,
        "style": "Tech style, deep blue theme, modern minimalist"
    },

    "business_plan": {
        "name": "Business Plan",
        "text": """
Smart Health Management Platform Business Plan

Project Overview:
We are developing an AI-powered smart health management platform that provides users with personalized health monitoring, disease prevention, and lifestyle recommendations.

Market Analysis:
- Global digital health market continues to grow, projected to reach $65.9B by 2025
- Strong demand for health management, rising user health awareness
- Mobile health app users exceed 400 million, huge market potential

Product Features:
1. Health Data Collection: Smart wearable sync, manual logging
2. AI Health Analysis: ML-based health status assessment
3. Personalized Recommendations: Customized exercise, diet, sleep advice
4. Disease Alerts: Early risk identification and reminders

Competitive Advantages:
- Advanced AI algorithms and big data analytics
- Multi-dimensional health data integration
- High-precision health risk prediction models

Financial Projections:
Year 1: User acquisition and product refinement, $5M investment
Year 2: Break-even, $10M revenue target
Year 3: Growth phase, $30M revenue target

Funding Requirements:
Seeking Series A funding of $10M for product R&D, marketing, and team expansion.
        """,
        "style": "Professional business style, deep blue theme, concise and persuasive"
    },

    "lifestyle": {
        "name": "Lifestyle & Coffee",
        "text": """
The Art of Coffee Living

Coffee is not just a beverage -- it's a lifestyle.

Origins of Coffee:
Legend has it that Ethiopian shepherds discovered their goats became unusually energetic after eating coffee berries, beginning humanity's enduring relationship with coffee.

Coffee Varieties:
- Arabica: Elegant aroma, smooth taste
- Robusta: Bold flavor, high caffeine content
- Liberica: Rare variety, unique character

Brewing Methods:
1. Pour-over: Delicate flavors, full ceremony
2. Espresso: Rich and bold, the classic choice
3. Cold brew: Refreshing and smooth, perfect for summer
4. French press: Simple and convenient, preserves oils

Coffee and Life:
A great cup of coffee makes mornings beautiful,
afternoons full of anticipation, and life full of ritual.
        """,
        "style": "Warm and cozy style, cream white, caramel brown, warm wood tones"
    },

    "product_intro": {
        "name": "Product Launch",
        "text": """
New Smartwatch Launch

Product Highlights:
- 24/7 Health Monitoring: Heart rate, blood oxygen, sleep quality
- Long Battery Life: 14 days on a single charge
- Ultra-lightweight: Only 32g, barely noticeable
- 100+ Watch Faces: Customize and switch at will

Core Features:
1. Accurate Activity Tracking: 100+ sport modes
2. Smart Notifications: Calls, messages, app alerts
3. NFC Payments: Pay with a wrist raise
4. Voice Assistant: Get things done with a single command

Technical Specs:
- Display: 1.5-inch AMOLED, 466x466 resolution
- Water Resistance: 5ATM, swim-ready
- Sensors: PPG heart rate, accelerometer, gyroscope, barometer
- Connectivity: Bluetooth 5.0, NFC, GPS

Price: Starting at $199
        """,
        "style": "Tech launch style, dark background, product-focused"
    },

    "academic": {
        "name": "Academic Research",
        "text": """
Deep Learning-Based Image Recognition Research

Research Background:
Computer vision is a key branch of AI. Image recognition is widely used in medical diagnosis, autonomous driving, and security surveillance.

Methodology:
1. Datasets: ImageNet, COCO, custom medical imaging datasets
2. Model Architectures: ResNet, EfficientNet, Vision Transformer
3. Training Strategies: Data augmentation, transfer learning, knowledge distillation

Experimental Results:
- Top-1 Accuracy: 92.3% (ImageNet)
- mAP: 78.5% (COCO object detection)
- Inference Speed: 15ms/image (RTX 3090)

Key Findings:
- Vision Transformer excels on large-scale datasets
- Knowledge distillation effectively compresses model size
- Multi-scale feature fusion improves small object detection

Future Work:
- Explore more efficient attention mechanisms
- Study few-shot learning methods
- Optimize edge device deployment
        """,
        "style": "Academic style, clean and concise, formulas and charts, professional and rigorous"
    }
}


# ==================== Template Preset Categories ====================

PRESET_CATEGORIES = {
    "business": {
        "name": "Business & Corporate",
        "presets": ["business_pitch", "corporate_professional", "company_intro",
                   "project_proposal", "quarterly_review", "fintech_modern", "startup_bold"]
    },
    "tech": {
        "name": "Tech & Product",
        "presets": ["tech_launch", "product_launch", "blueprint_technical",
                   "technical_report", "neon_dark", "data_dashboard_dark"]
    },
    "creative": {
        "name": "Creative & Design",
        "presets": ["glassmorphism", "gradient_mesh", "3d_modern", "geometric_abstract",
                   "flat_illustration", "pop_art", "monochrome_bold", "watercolor_art"]
    },
    "lifestyle": {
        "name": "Lifestyle & Aesthetic",
        "presets": ["instagram", "magazine", "morandi", "muji_minimal",
                   "minimal_luxury", "nordic_clean", "zen_japanese"]
    },
    "themed": {
        "name": "Fun & Themed",
        "presets": ["cyberpunk", "retro_80s", "doodle", "kawaii_cute",
                   "tropical_vibrant", "vintage"]
    },
    "atmosphere": {
        "name": "Atmosphere & Mood",
        "presets": ["dark_elegance", "pastel_dream", "space_cosmos",
                   "storytelling_cinematic"]
    },
    "domain": {
        "name": "Domain-Specific",
        "presets": ["nature_earth", "healthcare_medical", "education_chalkboard",
                   "newspaper_editorial", "school_project"]
    },
    "academic": {
        "name": "Academic & Training",
        "presets": ["academic", "academic_paper", "training"]
    }
}


def create_generator():
    """Create a PresentiQ generator instance using configured LLM provider."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    base_url = os.getenv("ANTHROPIC_BASE_URL")

    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        print("Example: export ANTHROPIC_API_KEY=your-api-key")
        exit(1)

    return PPTGenerator(
        api_key=api_key,
        provider="Claude",
        base_url=base_url,
        enable_cache=True
    )


def display_all_presets(generator):
    """Display all available template presets."""
    all_presets = generator.list_template_presets()
    preset_dict = {p['key']: p for p in all_presets}

    print("\n" + "=" * 60)
    print("  PresentiQ — Template Library (46 themes)")
    print("=" * 60)

    idx = 1
    preset_list = []

    for category_key, category in PRESET_CATEGORIES.items():
        print(f"\n  [{category['name']}]")
        for preset_key in category['presets']:
            if preset_key in preset_dict:
                p = preset_dict[preset_key]
                print(f"    {idx:2d}. {preset_key:<26} {p['name']}")
                preset_list.append(preset_key)
                idx += 1

    return preset_list


def display_sample_contents():
    """Display sample content options."""
    print("\n" + "-" * 40)
    print("  Select Sample Content:")
    print("-" * 40)

    content_list = list(SAMPLE_CONTENTS.keys())
    for i, key in enumerate(content_list, 1):
        print(f"    {i}. {SAMPLE_CONTENTS[key]['name']}")

    return content_list


def generate_with_preset(generator, preset_key: str, content_key: str):
    """Generate PPT using specified preset and content."""
    content = SAMPLE_CONTENTS[content_key]
    preset_info = generator.get_template_preset_info(preset_key)

    if not preset_info:
        print(f"  Preset not found: {preset_key}")
        return None

    print("\n" + "=" * 60)
    print(f"  Generating Presentation")
    print("=" * 60)
    print(f"   Template: {preset_info['name']} ({preset_key})")
    print(f"   Content:  {content['name']}")
    print(f"   Sequence: {' -> '.join(preset_info['sequence'])}")

    if 'style_hints' in preset_info:
        hints = preset_info['style_hints']
        print(f"\n   Style:")
        print(f"     Background: {hints.get('background', 'N/A')}")
        print(f"     Colors:     {', '.join(hints.get('colors', []))}")
        print(f"     Visual:     {hints.get('visual', 'N/A')}")

    print("\n   Generating...")
    print("     - Two-stage outline generation")
    print("     - Style-anchored batch generation")

    try:
        result = generator.generate_ppt(
            reference_text=content['text'],
            style_requirements=content['style'],
            output_dir=f"examples/{preset_key}_{content_key}",
            template_preset=preset_key,
            use_cache=True
        )

        print("\n   Done!")
        print(f"   Total slides:      {result['total_slides']}")
        print(f"   Successful slides: {result['success_slides']}")
        print(f"   PPTX file:         {result['pptx_file']}")

        gen_info = result.get('generation_info', {})
        print(f"\n   Generation info:")
        print(f"     Two-stage:      {'Yes' if gen_info.get('two_stage', False) else 'No'}")
        print(f"     Style-anchored: {'Yes' if gen_info.get('style_anchored', False) else 'No'}")
        print(f"     Cache hit:      {'Yes' if gen_info.get('cache_used', False) else 'No'}")

        if result.get('cache_hits'):
            print(f"     Image cache hits: {result['cache_hits']}")

        return result

    except Exception as e:
        print(f"\n   Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Interactive main program."""
    print("=" * 60)
    print("  PresentiQ v2.0 — AI Presentation Generator")
    print("=" * 60)

    generator = create_generator()

    while True:
        preset_list = display_all_presets(generator)

        print("\n" + "-" * 40)
        choice = input("  Select template number (q to quit): ").strip()

        if choice.lower() == 'q':
            print("\n  Goodbye!")
            break

        try:
            preset_idx = int(choice) - 1
            if preset_idx < 0 or preset_idx >= len(preset_list):
                print("  Invalid number")
                continue
            preset_key = preset_list[preset_idx]
        except ValueError:
            print("  Please enter a number")
            continue

        content_list = display_sample_contents()

        content_choice = input("  Select sample content number: ").strip()
        try:
            content_idx = int(content_choice) - 1
            if content_idx < 0 or content_idx >= len(content_list):
                print("  Invalid number")
                continue
            content_key = content_list[content_idx]
        except ValueError:
            print("  Please enter a number")
            continue

        generate_with_preset(generator, preset_key, content_key)

        stats = generator.get_cache_stats()
        if stats:
            print(f"\n  Cache stats:")
            print(f"    Outline cache: {stats['outline_count']} items")
            print(f"    Image cache:   {stats['image_count']} items")
            print(f"    Total size:    {stats['total_size_mb']} MB")

        print("\n" + "-" * 40)
        again = input("  Generate again? (y/n): ").strip().lower()
        if again != 'y':
            print("\n  Goodbye!")
            break


if __name__ == "__main__":
    main()
