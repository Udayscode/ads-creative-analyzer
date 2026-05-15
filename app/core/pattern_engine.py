import json
import re
import time
try:
    from tqdm import tqdm
except ImportError:
    tqdm = lambda x, **k: x

from google import genai
from groq import Groq

from app.config import GEMINI_API_KEY, GROQ_API_KEY, TEXT_MODEL
from app.prompts.pattern import PATTERN_PROMPT

# client = genai.Client(api_key=GEMINI_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)


def _clean_json(text: str) -> str:
    text = text.strip()
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    return text


def detect_patterns(breakdowns: list[dict], scores: list[dict], brand: str) -> dict:
    """
    breakdowns: list of AdBreakdown dicts
    scores:     list of AdScore dicts (same order)
    Returns PatternReport dict.
    """
    sorted_scores = sorted(scores, key=lambda s: s["total"], reverse=True)
    top_ids    = [s["ad_id"] for s in sorted_scores[:3]]
    bottom_ids = [s["ad_id"] for s in sorted_scores[-3:]]

    # strip image_path before sending to LLM (not useful, wastes tokens)
    clean_breakdowns = [
        {k: v for k, v in b.items() if k != "image_path"}
        for b in breakdowns
    ]

    prompt = PATTERN_PROMPT.format(
        n=len(breakdowns),
        brand=brand,
        top_ids=", ".join(top_ids),
        bottom_ids=", ".join(bottom_ids),
        breakdowns_json=json.dumps(clean_breakdowns, indent=2),
    )

    try:
        response = groq_client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"},
            max_tokens=4000,
        )
        response_text = response.choices[0].message.content
    except Exception as e:
        raise ValueError(f"Groq API call failed: {e}")

    cleaned = _clean_json(response_text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        # Graceful fallback instead of crashing the Streamlit app
        return {
            "winning_patterns": [{"pattern": "Incomplete Data", "description": "Analysis truncated.", "evidence": [], "confidence": "low"}],
            "losing_patterns": [],
            "brand_creative_signature": "Could not complete analysis due to API constraints.",
            "biggest_gap": "N/A"
        }