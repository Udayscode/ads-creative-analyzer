import json
import re
import time
try:
    from tqdm import tqdm
except ImportError:
    tqdm = lambda x, **k: x

from google import genai

from app.config import GEMINI_API_KEY, TEXT_MODEL
from app.prompts.ideas import IDEAS_PROMPT

client = genai.Client(api_key=GEMINI_API_KEY)


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

    for attempt in range(5):
        try:
            response = client.models.generate_content(
                model=TEXT_MODEL,
                contents=prompt,
                config={"temperature": 0.4},
            )
            break
        except Exception as e:
            if ("429" in str(e) or "503" in str(e)) and attempt < 4:
                error_str = str(e)
                delay = 15
                match = re.search(r"retry in ([\d\.]+)s", error_str)
                if match:
                    delay = int(float(match.group(1))) + 5
                print(f"[IdeaGenerator] API paused. Sleeping for {delay}s...")
                for _ in tqdm(range(delay), desc="Retrying Ideas in", leave=False):
                    time.sleep(1)
            else:
                raise

    cleaned = _clean_json(response.text)
    try:
        ideas = json.loads(cleaned)
        return ideas if isinstance(ideas, list) else []
    except json.JSONDecodeError as e:
        raise ValueError(f"Ideas JSON parse failed: {e}\nRaw:\n{response.text}")