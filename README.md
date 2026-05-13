# Ads Creative Analyzer

Upload 10–15 ad images from any brand. Get a structured breakdown of each, a ranked performance score, cross-ad pattern analysis, and 3–5 concrete ideas to test next.

**[Live Demo →](https://your-link.streamlit.app)**

---

## How it works

```
images → Gemini Vision (extract structure per ad)
       → heuristic scorer (0–100 across 5 dimensions)
       → Gemini Text (detect patterns across all ads)
       → Gemini Text (generate test ideas from the gaps)
       → Streamlit UI (charts, cards, export)
```

**Scoring rubric** (20 pts each, no LLM involved):
- Hook strength — does it stop a scroll?
- Offer clarity — is the value prop obvious in 2 seconds?
- Trust signals — reviews, ratings, UGC, press logos
- Visual-copy alignment — does the tone match the layout?
- Mobile legibility — readable on a phone screen?

---

## Architecture

```
┌────────────────────────────────────────────────────────┐
│                    User (Browser)                      │
│              Streamlit UI — localhost:8501             │
└───────────────────────┬────────────────────────────────┘
                        │ uploads images + triggers analysis
                        ▼
┌────────────────────────────────────────────────────────┐
│                   Streamlit App                        │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Upload Panel│  │  Score Chart │  │  Ideas Panel │   │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                │                 │           │
│         └────────────────┴─────────────────┘           │
│                          │                             │
│              ┌───────────▼──────────┐                  │
│              │   Orchestrator       │                  │
│              │   (main.py)          │                  │
│              └───────────┬──────────┘                  │
└──────────────────────────┼─────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   ┌─────────────┐  ┌────────────┐  ┌─────────────────┐
   │  Analyzer   │  │  Scorer    │  │  Pattern Engine │
   │ (per ad)    │  │ (per ad)   │  │  + Idea Gen     │
   └──────┬──────┘  └─────┬──────┘  └────────┬────────┘
          │               │                  │
          └───────────────┴──────────────────┘
                          │
                          ▼
          ┌───────────────────────────────┐
          │            Gemini             │
          │  Vision + Text completions    │
          └───────────────────────────────┘
```

**Data flow:**
1. User uploads 12–15 ad images (PNG/JPG)
         │
         ▼
2. image_utils.py → resize to ≤1024px, base64 encode
         │
         ▼
3. FOR EACH IMAGE:
   analyzer.py → sends image + extraction prompt to Claude Vision
   → returns AdBreakdown (structured dict)
         │
         ▼
4. scorer.py → applies rubric to each AdBreakdown
   → returns AdScore (0–100, with sub-scores per dimension)
         │
         ▼
5. All breakdowns + scores passed to pattern_engine.py
   → sends all structured data (no images) to Claude Text
   → returns PatternReport (what winning ads share)
         │
         ▼
6. idea_generator.py → sends pattern report to Claude
   → returns 3–5 TestIdeas (concrete, grounded)
         │
         ▼
7. Streamlit UI renders everything:
   - Ranked score chart
   - Per-ad breakdown cards
   - Pattern report
   - Test ideas
   - Export button (JSON / Markdown)
---

## Setup

**With uv (recommended):**
```bash
git clone https://github.com/Udayscode/ads-creative-analyzer
cd ads-creative-analyzer
uv venv && uv pip install -r requirements.txt
echo 'GEMINI_API_KEY="your-key"' > .env
uv run streamlit run main.py
```

**With pip:**
```bash
pip install -r requirements.txt
echo 'GEMINI_API_KEY="your-key"' > .env
streamlit run main.py
```

Get a free API key at [aistudio.google.com](https://aistudio.google.com).

---

## Running it

Drop 10–15 ad images into `data/sample_ads/` or use the in-app uploader, enter a brand name, and hit **Run Analysis**.

A ~15s cooldown bar appears between images — this is intentional rate-limit handling for the free API tier, not a bug. Full analysis for 15 ads takes about 4–5 minutes.

---

## Tradeoffs

- Scoring is deterministic (rubric-based), not LLM-generated — more auditable, less hallucination.
- API calls are serialised with a cooldown to survive free-tier quotas. With a paid key and `asyncio`, this drops to ~15 seconds total.
- Streamlit over React — for a 4-hour build.

**Next:** Meta Ad Library API for automated ingestion, async parallel calls on paid tier, ROAS-trained scoring once labelled data exists.
