EXTRACTION_PROMPT = """You are a senior performance marketing analyst reviewing ad creatives.

Analyze this ad image and return ONLY a valid JSON object with this exact schema.
Do not include markdown fences, preamble, or explanation — raw JSON only.

{
  "hook": {
    "primary_element": "visual|headline|offer",
    "hook_text": "<exact headline or first visible text, empty string if none>",
    "hook_visual": "<one sentence describing the dominant visual>",
    "pattern_interrupt": true,
    "hook_strength": "strong|moderate|weak"
  },
  "offer": {
    "product": "<product name or category>",
    "value_proposition": "<core value claim in one sentence>",
    "discount_present": true,
    "discount_type": "percentage|flat|none",
    "price_visible": true,
    "cta_text": "<exact CTA text, empty string if absent>",
    "cta_strength": "strong|moderate|weak|absent"
  },
  "trust_signals": {
    "has_reviews": false,
    "has_ratings": false,
    "has_ugc": false,
    "has_celebrity": false,
    "has_press_logo": false,
    "trust_signal_count": 0
  },
  "visual_style": {
    "dominant_colors": ["color1", "color2"],
    "layout_type": "product_focused|lifestyle|testimonial|offer_card|comparison",
    "people_present": false,
    "text_overlay_density": "heavy|moderate|light|none",
    "mobile_legibility": "high|medium|low"
  },
  "copy": {
    "headline": "<full headline text>",
    "body_copy": "<any visible body copy, empty string if none>",
    "tone": "urgent|aspirational|educational|humorous|functional",
    "copy_length": "short|medium|long"
  },
  "format_signals": {
    "apparent_format": "static|carousel|video_thumbnail|story",
    "aspect_ratio": "square|portrait|landscape",
    "has_logo": false
  }
}"""