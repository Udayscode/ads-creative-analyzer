from app.config import HOOK_MAP, CTA_MAP, MOBILE_MAP, TONE_ALIGNMENT_MAP, DEFAULT_ALIGNMENT


def score_breakdown(breakdown: dict) -> dict:
    """
    Pure Python. No LLM call.
    Takes an AdBreakdown dict, returns an AdScore dict.
    """
    hook       = breakdown.get("hook", {})
    offer      = breakdown.get("offer", {})
    trust      = breakdown.get("trust_signals", {})
    visual     = breakdown.get("visual_style", {})
    copy       = breakdown.get("copy", {})

    # 1. Hook strength (0–20)
    s_hook = HOOK_MAP.get(hook.get("hook_strength", "weak"), 4)

    # 2. Offer clarity (0–20) — CTA is the sharpest signal
    s_offer = CTA_MAP.get(offer.get("cta_strength", "absent"), 0)
    if offer.get("price_visible"):
        s_offer = min(s_offer + 4, 20)
    if offer.get("discount_present"):
        s_offer = min(s_offer + 4, 20)

    # 3. Trust signals (0–20) — each signal worth 5, cap at 20
    count = int(trust.get("trust_signal_count", 0))
    # recount from booleans in case count field is wrong
    bool_count = sum([
        bool(trust.get("has_reviews")),
        bool(trust.get("has_ratings")),
        bool(trust.get("has_ugc")),
        bool(trust.get("has_celebrity")),
        bool(trust.get("has_press_logo")),
    ])
    s_trust = min(max(count, bool_count) * 5, 20)

    # 4. Visual–copy alignment (0–20)
    layout = visual.get("layout_type", "product_focused")
    tone   = copy.get("tone", "functional")
    tone_map = TONE_ALIGNMENT_MAP.get(layout, {})
    s_align = tone_map.get(tone, DEFAULT_ALIGNMENT)

    # 5. Mobile legibility (0–20)
    s_mobile = MOBILE_MAP.get(visual.get("mobile_legibility", "medium"), 12)

    total = s_hook + s_offer + s_trust + s_align + s_mobile

    return {
        "ad_id": breakdown.get("ad_id"),
        "total": total,
        "dimensions": {
            "hook_strength":         s_hook,
            "offer_clarity":         s_offer,
            "trust_signals":         s_trust,
            "visual_copy_alignment": s_align,
            "mobile_legibility":     s_mobile,
        },
    }