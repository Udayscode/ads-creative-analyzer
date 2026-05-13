PATTERN_PROMPT = """You are a performance marketing strategist.

Below are structured breakdowns of {n} ads from the brand "{brand}".

Top performers (by score): {top_ids}
Bottom performers (by score): {bottom_ids}

Ad breakdowns (JSON):
{breakdowns_json}

Identify what top performers share that bottom performers lack. Be specific.
Reference actual field values from the breakdowns. No generic advice.

Return ONLY a valid JSON object — no markdown fences, no preamble:

{{
  "winning_patterns": [
    {{
      "pattern": "<short name>",
      "description": "<what top ads do that bottom ads don't — cite specific fields>",
      "evidence": ["<ad_id>"],
      "confidence": "high|medium|low"
    }}
  ],
  "losing_patterns": [
    {{
      "pattern": "<short name>",
      "description": "<what bottom ads consistently do wrong>",
      "evidence": ["<ad_id>"],
      "confidence": "high|medium|low"
    }}
  ],
  "brand_creative_signature": "<2-sentence description of this brand's current creative style>",
  "biggest_gap": "<single highest-leverage thing this brand is not doing>"
}}"""