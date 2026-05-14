import json
import re
from google import genai
import time
try:
    from tqdm import tqdm
except ImportError:
    tqdm = lambda x, **k: x

from app.config import GEMINI_API_KEY, VISION_MODEL
from app.prompts.extraction import EXTRACTION_PROMPT
from app.utils.image_utils import prepare_for_gemini

client = genai.Client(api_key=GEMINI_API_KEY)


def _clean_json(text: str) -> str:
    """Strip markdown fences if the model wraps the response anyway."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text)
    text = re.sub(r"```$", "", text)
    return text.strip()


def extract_breakdown(image_path: str, ad_id: str, progress_callback=None) -> dict:
    """
    Send one ad image to Gemini Vision.
    Returns an AdBreakdown dict with an added 'ad_id' key.
    Raises ValueError if JSON cannot be parsed.
    """
    image_part = prepare_for_gemini(image_path)
    
    start_time = time.time()

    for attempt in range(5):
        try:
            response = client.models.generate_content(
                model=VISION_MODEL,
                contents=[
                    {"parts": [image_part, {"text": EXTRACTION_PROMPT}]}
                ],
            )
            break
        except Exception as e:
            if ("429" in str(e) or "503" in str(e)) and attempt < 4:
                error_str = str(e)
                delay = 10
                match = re.search(r"retry in ([\d\.]+)s", error_str)
                if match:
                    delay = int(float(match.group(1))) + 5
                print(f"[{ad_id}] API paused. Sleeping for {delay}s before retry...")
                for i in tqdm(range(delay), desc=f"Retrying {ad_id} in", leave=False):
                    if progress_callback:
                        progress_callback(i / delay, f"⏳ Rate limit pause: retrying {ad_id} in {delay - i}s")
                    time.sleep(1)
            else:
                raise

    raw = response.text
    cleaned = _clean_json(raw)

    try:
        breakdown = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"[{ad_id}] JSON parse failed: {e}\nRaw response:\n{raw}")

    # Dynamic sleep to maintain 15 RPM (1 request every 4 seconds) for Gemini 3.1 Flash Lite free tier
    elapsed = time.time() - start_time
    sleep_time = max(0, 4.0 - elapsed)
    
    if sleep_time > 0:
        sleep_secs = int(sleep_time) + 1
        for i in tqdm(range(sleep_secs), desc=f"Cooldown after {ad_id}", leave=False):
            if progress_callback:
                progress_callback(i / float(sleep_secs), f"⏳ Cooldown after {ad_id}: {sleep_secs - i}s remaining")
            time.sleep(1)

    breakdown["ad_id"] = ad_id
    breakdown["image_path"] = image_path
    return breakdown