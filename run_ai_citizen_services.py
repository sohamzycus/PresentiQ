"""PresentiQ — Generate a 15-slide PPT on 'AI in Citizen Services' for a Class 6 student.

Story-driven: follows Ravi (age 11) whose father needed a birth certificate
and discovered how AI is transforming government services.
"""

import os
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

from ppt_generator import PPTGenerator

REFERENCE_TEXT = """
AI in Citizen Services — How Artificial Intelligence is Helping People Every Day
A Story-Driven Exploration by Ravi, Class 6 (Age 11)

=== RAVI'S STORY (use as the narrative thread across ALL slides) ===

Meet Ravi. He is 11 years old and studies in Class 6. One evening, Ravi's father came home
looking worried. He needed a birth certificate urgently for a new job application — but the
last time he tried to get one, it took 3 weeks of standing in queues, filling paper forms,
and visiting the municipal office five times! Ravi's father was dreading the whole process.

But this time, something amazing happened. Ravi's father opened his phone, visited the
government's new AI-powered portal, typed in his details, and a smart chatbot guided him
step-by-step. The AI verified his documents instantly using OCR (Optical Character Recognition),
cross-checked his identity with the Aadhaar database, and within 48 hours — a verified digital
birth certificate appeared in his DigiLocker! No queues. No middlemen. No stress.

Ravi was amazed. "How did the computer do all that, Papa?" he asked.
His father smiled: "It's called Artificial Intelligence, beta. And it's changing everything."

That night, Ravi couldn't sleep. He started researching AI and citizen services for his
school project. Here's what he found...

=== WHAT IS AI? (Slide: make it super simple and visual) ===

Artificial Intelligence (AI) is when computers learn to think, understand, and make decisions
— almost like a human brain, but much faster! AI can:
- Recognize your face in a photo
- Understand what you say (even in Hindi or Tamil!)
- Read thousands of documents in seconds
- Predict what might happen next (like weather forecasts)

Think of AI as a super-smart helper that never gets tired and never takes a lunch break!

=== WHAT ARE CITIZEN SERVICES? (Slide: relatable examples) ===

Citizen services = things the government does to help YOU and your family:
- Getting a birth certificate (like Ravi's father!)
- Making a passport for a family vacation
- Paying electricity bills and property taxes
- Reporting a pothole on your street
- Getting help during floods or earthquakes
- Going to a government hospital
- Riding the metro or public bus
- Enrolling in school

Before AI: Long queues, confusing forms, weeks of waiting, "come back tomorrow" syndrome
After AI: Quick, digital, available 24/7 on your phone!

=== HOW AI HELPS — 7 SUPER COOL WAYS ===

1. Smart Chatbots — Your 24/7 Government Friend
   - AI chatbots on government websites answer questions instantly
   - No more waiting on hold for hours!
   - They speak multiple languages — Hindi, English, Tamil, Bengali...
   - Examples: India's MyGov chatbot, USA's Ask IRS bot
   - Ravi's father used one to get his birth certificate!

2. Lightning-Fast Document Processing
   - AI reads handwritten forms using OCR technology
   - Verifies your identity by matching photos and fingerprints
   - Processes thousands of applications per hour (humans can do maybe 20!)
   - Ravi's father's birth certificate: AI verified it in minutes, not weeks
   - Passport applications now take days instead of months

3. Smart Traffic That Thinks
   - AI cameras watch traffic in real time from above
   - Traffic lights change automatically — green for the busiest road!
   - Ambulances get a "green wave" — all lights turn green for them
   - Reduces your car ride time by 20-25%
   - Example: Bangalore's Intelligent Traffic Management System
   - Imagine: Ravi's school bus reaching on time every day!

4. AI Doctor's Assistant
   - AI helps doctors spot diseases in X-rays that human eyes might miss
   - Predicts disease outbreaks so hospitals stock up on medicines early
   - Telemedicine: a doctor on your phone, even in a remote village
   - Example: India's eSanjeevani — 100+ million video consultations!
   - Ravi's grandmother in the village got a doctor's advice without traveling 50 km

5. Smarter Schools with AI
   - AI tutors that adapt to YOUR learning speed
   - Struggling with fractions? The AI gives you extra practice
   - Already great at science? It gives you harder challenges
   - Automatic grading means teachers have more time to actually teach
   - Example: DIKSHA platform by Government of India
   - Ravi uses an AI tutor app for his math homework!

6. Keeping Cities Safe
   - AI-powered cameras detect suspicious activity automatically
   - Facial recognition helps find missing children within hours
   - AI weather models predict cyclones 5 days in advance
   - Example: Safe City projects in Hyderabad and Lucknow
   - During last year's floods, AI alerts saved thousands of families

7. Digital Wallet for Your Documents
   - DigiLocker: 150+ million Indians store documents on their phones
   - Birth certificate, school marksheet, Aadhaar — all in one app
   - AI verifies documents are real (catches fakes instantly)
   - Ravi's father now has his birth certificate safe in DigiLocker forever!

=== RAVI'S FATHER'S JOURNEY — BEFORE vs AFTER AI (dedicated comparison slide) ===

BEFORE AI (The Old Way):
- Visit municipal office → told to "come tomorrow"
- Fill 3 paper forms by hand → one had a spelling mistake → start over
- Wait in queue for 2 hours → counter closes for lunch
- Come back next week → file "misplaced" → start the whole process again
- Total time: 3 weeks, 5 visits, lots of frustration

AFTER AI (The New Way):
- Open government portal on phone at 9 PM from the couch
- AI chatbot guides through the application in 10 minutes
- Upload photo of old documents → AI reads them with OCR
- AI cross-checks with Aadhaar database → identity verified instantly
- Digital birth certificate in DigiLocker within 48 hours
- Total time: 10 minutes of effort, zero office visits!

=== MIND-BLOWING NUMBERS (data/statistics slide — make it visual!) ===

- 150+ million DigiLocker users in India
- 10 million+ citizen queries handled by AI chatbots every month
- 100+ million teleconsultations on eSanjeevani
- 20-25% less travel time in smart-traffic pilot cities
- 48 hours to get a birth certificate (vs 3 weeks before!)
- AI processes documents 50x faster than humans
- Government saves ₹1000+ crores per year using AI automation

=== CHALLENGES — IT'S NOT ALL PERFECT (keep it honest and balanced) ===

- Digital Divide: Not everyone has a smartphone or internet (especially in villages)
- Privacy Worries: Who sees our personal data? Is it safe?
- AI Mistakes: Sometimes AI gets confused — it's smart but not perfect
- Training Needed: Government employees need to learn these new tools
- Language Gaps: AI needs to work in ALL Indian languages, not just English and Hindi
- Power Cuts: Digital services need electricity and internet — what about remote areas?

=== THE FUTURE — WHAT'S COMING NEXT (exciting, forward-looking) ===

- Voice AI in every language: "Hey AI, renew my passport" — in Marathi, Kannada, or Assamese!
- Predictive government: AI notices your child turned 5 → auto-sends school enrollment form
- One-tap services: Every government service available in one super-app
- AI for disaster response: Drones + AI deliver medicines during floods
- Your personal government assistant: Like having a helpful friend who knows every rule

Ravi's dream: "One day, nobody will have to stand in a queue ever again.
The government will come to YOU — through your phone!"

=== WHAT CAN WE DO? (call to action for students) ===

As Class 6 students, here's how WE can be part of the AI revolution:
- Learn coding and logical thinking (start with Scratch or Python!)
- Help our parents and grandparents use digital government services
- Stay curious — ask "how does this work?" about everything
- Dream big — maybe YOU will build the next great AI for India!
- Remember: Understanding AI today means being ready for tomorrow

Prepared by: Ravi and friends, Class 6 (Age 11)
School Project — February 2026
"""

STYLE = (
    "Bright, colorful, and fun school-project style with a STORY-DRIVEN feel. "
    "Sky blue and green gradients, large bold text, friendly icons, "
    "simple language suitable for a Class 6 student (age 11) audience. "
    "Weave Ravi's story visually — use speech bubbles, before/after comparisons, "
    "character silhouettes, and timeline graphics. "
    "Clean modern design with rounded shapes and soft shadows. "
    "Make data slides use big bold numbers with colorful icons. "
    "Every slide should feel exciting and relatable to an 11-year-old."
)

EXTRA_SLIDES = [
    {
        "type": "team_members",
        "title": "Our Team",
        "subtitle": "Class 6 — School Project, February 2026",
        "items": [
            "[ Student Name 1 ]",
            "[ Student Name 2 ]",
            "[ Student Name 3 ]",
            "[ Student Name 4 ]",
            "[ Add more names here... ]",
        ],
        "bg_color": (79, 195, 247),
        "text_color": (255, 255, 255),
        "accent_color": (225, 245, 254),
    },
    {
        "type": "thank_you",
        "title": "Thank You!",
        "subtitle": "We hope you enjoyed Ravi's journey into AI and Citizen Services",
        "items": [],
        "bg_color": (102, 187, 106),
        "text_color": (255, 255, 255),
        "accent_color": (232, 245, 233),
    },
]


def main():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    base_url = os.getenv("ANTHROPIC_BASE_URL")
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-global")

    if not api_key:
        print("Error: Set ANTHROPIC_API_KEY in .env")
        return

    print("=" * 60)
    print("  AI in Citizen Services — Ravi's Story")
    print("  For and by Class 6 Students (Age 11)")
    print("=" * 60)

    generator = PPTGenerator(
        api_key=api_key,
        provider="Claude",
        base_url=base_url,
        enable_cache=True,
    )

    print("\nGenerating 15-slide presentation...")
    print("  13 AI-rendered content slides")
    print("   + Team Members slide (editable)")
    print("   + Thank You slide (editable)")
    print("  Template: school_project (story-driven)")
    print(f"  Model: {model}")
    print("  This will take a few minutes — each slide is rendered individually.\n")

    result = generator.generate_ppt(
        reference_text=REFERENCE_TEXT,
        style_requirements=STYLE,
        output_dir="output/ai_citizen_services",
        model=model,
        template_preset="school_project",
        audience_profile={
            "type": "Class 6 students (age 11)",
            "expertise": "beginner",
            "interests": "technology, school project, simple explanations, storytelling",
        },
        use_cache=False,
        _extra_slides=EXTRA_SLIDES,
    )

    print("\n" + "=" * 60)
    print("  DONE!")
    print("=" * 60)
    print(f"  Total slides:   {result['total_slides']}")
    print(f"  Successful:     {result['success_slides']}")
    print(f"  PPTX file:      {result['pptx_file']}")
    print(f"  Outline file:   {result['outline_file']}")

    if result.get("error_slides"):
        print(f"\n  Failed slides:")
        for err in result["error_slides"]:
            print(f"    Page {err['page']}: {err['error'][:80]}")

    gen_info = result.get("generation_info", {})
    print(f"\n  Two-stage outline: {'Yes' if gen_info.get('two_stage') else 'No'}")
    print(f"  Style anchored:    {'Yes' if gen_info.get('style_anchored') else 'No'}")
    print(f"  Cache used:        {'Yes' if gen_info.get('cache_used') else 'No'}")


if __name__ == "__main__":
    main()
