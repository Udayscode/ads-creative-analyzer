import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

VISION_MODEL = "gemini-3.1-flash-lite"
TEXT_MODEL = "llama-3.3-70b-versatile"

# Scoring weights (sum = 100)
SCORE_WEIGHTS = {
    "hook_strength":         20,
    "offer_clarity":         20,
    "trust_signals":         20,
    "visual_copy_alignment": 20,
    "mobile_legibility":     20,
}

# Attribute → points mapping (each dimension max = 20)
HOOK_MAP = {
    "strong":   20,
    "moderate": 12,
    "weak":      4,
}

CTA_MAP = {
    "strong":   20,
    "moderate": 12,
    "weak":      6,
    "absent":    0,
}

MOBILE_MAP = {
    "high":   20,
    "medium": 12,
    "low":     4,
}

TONE_ALIGNMENT_MAP = {
    # layout_type → compatible tones → bonus points
    "lifestyle":    {"aspirational": 20, "urgent": 14, "functional": 10},
    "offer_card":   {"urgent": 20, "functional": 16, "aspirational": 10},
    "testimonial":  {"aspirational": 20, "educational": 16, "functional": 12},
    "comparison":   {"educational": 20, "functional": 16, "urgent": 12},
    "product_focused": {"functional": 20, "urgent": 14, "aspirational": 12},
}
DEFAULT_ALIGNMENT = 10