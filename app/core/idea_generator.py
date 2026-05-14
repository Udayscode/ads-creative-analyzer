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
from app.prompts.ideas import IDEAS_PROMPT

# client = genai.Client(api_key=GEMINI_API_KEY)

groq_client = Groq(api_key=GROQ_API_KEY)

def _clean_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text)
    text = re.sub(r"```$", "", text)
    return text.strip()


def generate_ideas(pattern_report: dict, brand: str) -> list[dict]:
    """
    Takes a PatternReport dict, returns list of 5 TestIdea dicts.
    """
    winning = json.dumps(pattern_report.get("winning_patterns", []), indent=2)
    gap     = pattern_report.get("biggest_gap", "")
    sig     = pattern_report.get("brand_creative_signature", "")

    prompt = IDEAS_PROMPT.format(
        brand=brand,
        winning_patterns=winning,
        biggest_gap=gap,
        signature=sig,
    )

    try:
        response = groq_client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
        )
        response_text = response.choices[0].message.content
    except Exception as e:
        raise ValueError(f"Groq API call failed: {e}")

    cleaned = _clean_json(response_text)
    try:
        ideas = json.loads(cleaned)
        return ideas if isinstance(ideas, list) else []
    except json.JSONDecodeError as e:
        raise ValueError(f"Ideas JSON parse failed: {e}\nRaw:\n{response_text}")