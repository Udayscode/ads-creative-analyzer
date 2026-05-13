import os
import glob
import json
import streamlit as st
import plotly.graph_objects as go
from PIL import Image
from tqdm import tqdm

from app.core.analyzer import extract_breakdown
from app.core.scorer import score_breakdown
from app.core.pattern_engine import detect_patterns
from app.core.idea_generator import generate_ideas

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Ads Creative Analyzer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Minimal CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
.card { background:#1e1e2e; border-radius:12px; padding:16px; margin-bottom:12px; }
.score-badge { font-size:2rem; font-weight:700; color:#a6e3a1; }
.dim-label { font-size:0.75rem; color:#cdd6f4; margin-bottom:2px; }
.pattern-win { border-left:4px solid #a6e3a1; padding-left:12px; margin-bottom:10px; }
.pattern-lose { border-left:4px solid #f38ba8; padding-left:12px; margin-bottom:10px; }
.idea-card { background:#181825; border-radius:10px; padding:14px; margin-bottom:14px; }
.priority-high { color:#a6e3a1; font-weight:600; }
.priority-medium { color:#fab387; font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🎯 Ads Creative Analyzer")
    st.caption("Powered by Gemini 2.5 Flash")
    st.divider()

    brand = st.text_input("Brand name", value="Lenskart")

    mode = st.radio("Ad source", ["Use sample ads", "Upload my own"])

    uploaded_files = []
    if mode == "Upload my own":
        uploaded_files = st.file_uploader(
            "Upload ad images", type=["png", "jpg", "jpeg"],
            accept_multiple_files=True
        )

    run = st.button("▶ Run Analysis", type="primary", use_container_width=True)
    st.divider()
    st.caption("Scoring rubric: Hook · Offer · Trust · Alignment · Mobile (20 pts each)")

# ── Helpers ───────────────────────────────────────────────────────────────────
SAMPLE_DIR = "data/sample_ads"

def get_image_paths():
    if mode == "Upload my own" and uploaded_files:
        paths = []
        os.makedirs("/tmp/ad_uploads", exist_ok=True)
        for f in uploaded_files:
            p = f"/tmp/ad_uploads/{f.name}"
            with open(p, "wb") as out:
                out.write(f.read())
            paths.append(p)
        return paths
    return sorted(glob.glob(f"{SAMPLE_DIR}/*.png") + glob.glob(f"{SAMPLE_DIR}/*.jpg"))


def run_analysis(paths, brand_name):
    breakdowns, scores = [], []
    
    status_msg = st.empty()
    bar = st.progress(0, text="Starting analysis…")
    cooldown_container = st.empty()
    
    def update_cooldown(pct, text):
        cooldown_container.progress(pct, text=text)
    
    for i, p in enumerate(paths):
        ad_id = os.path.splitext(os.path.basename(p))[0]
        status_msg.info(f"⏳ **Analyzing image {i+1} of {len(paths)}:** `{ad_id}`")
        
        bd = extract_breakdown(p, ad_id, progress_callback=update_cooldown)
        cooldown_container.empty()
        
        sc = score_breakdown(bd)
        breakdowns.append(bd)
        scores.append(sc)
        bar.progress((i + 1) / len(paths), text=f"Extracted {i+1}/{len(paths)}")

    status_msg.info("🧠 **Detecting patterns across all ads...**")
    bar.progress(1.0, text="Detecting patterns…")
    patterns = detect_patterns(breakdowns, scores, brand_name)

    status_msg.info("💡 **Generating creative test ideas...**")
    bar.progress(1.0, text="Generating ideas…")
    ideas = generate_ideas(patterns, brand_name)

    bar.empty()
    status_msg.empty()
    return breakdowns, scores, patterns, ideas


def score_bar_chart(scores):
    sorted_s = sorted(scores, key=lambda x: x["total"], reverse=True)
    ids   = [s["ad_id"] for s in sorted_s]
    totals = [s["total"] for s in sorted_s]
    colors = ["#a6e3a1" if t >= 75 else "#fab387" if t >= 55 else "#f38ba8" for t in totals]

    fig = go.Figure(go.Bar(
        x=totals, y=ids, orientation="h",
        marker_color=colors,
        text=[f"{t}/100" for t in totals],
        textposition="outside",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#cdd6f4",
        xaxis=dict(range=[0, 110], showgrid=False),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=0, r=40, t=10, b=10),
        height=max(250, len(scores) * 38),
    )
    return fig


def dimension_bars(dims):
    labels = list(dims.keys())
    vals   = list(dims.values())
    colors = ["#a6e3a1" if v >= 16 else "#fab387" if v >= 10 else "#f38ba8" for v in vals]
    fig = go.Figure(go.Bar(
        x=vals, y=[l.replace("_", " ").title() for l in labels],
        orientation="h", marker_color=colors,
        text=vals, textposition="outside",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#cdd6f4",
        xaxis=dict(range=[0, 25], showgrid=False),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=0, r=30, t=0, b=0),
        height=180,
    )
    return fig


def export_markdown(brand_name, breakdowns, scores, patterns, ideas):
    lines = [f"# Ads Creative Analysis — {brand_name}\n"]

    lines.append("## Scores\n")
    for s in sorted(scores, key=lambda x: x["total"], reverse=True):
        lines.append(f"- **{s['ad_id']}**: {s['total']}/100")
    lines.append("")

    lines.append("## Winning Patterns\n")
    for p in patterns.get("winning_patterns", []):
        lines.append(f"### {p['pattern']} ({p['confidence']} confidence)")
        lines.append(p["description"])
        lines.append(f"*Evidence: {', '.join(p['evidence'])}*\n")

    lines.append("## Losing Patterns\n")
    for p in patterns.get("losing_patterns", []):
        lines.append(f"### {p['pattern']} ({p['confidence']} confidence)")
        lines.append(p["description"])
        lines.append(f"*Evidence: {', '.join(p['evidence'])}*\n")

    lines.append(f"## Brand Signature\n{patterns.get('brand_creative_signature', '')}\n")
    lines.append(f"## Biggest Gap\n{patterns.get('biggest_gap', '')}\n")

    lines.append("## Test Ideas\n")
    for i, idea in enumerate(ideas, 1):
        lines.append(f"### {i}. {idea['idea_title']} [{idea['priority'].upper()}]")
        lines.append(f"**Format:** {idea['format']}")
        lines.append(f"**Hook:** {idea['hook_concept']}")
        lines.append(f"**Headline:** {idea['headline_draft']}")
        lines.append(f"**Visual brief:** {idea['visual_brief']}")
        lines.append(f"**Hypothesis:** {idea['hypothesis']}\n")

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────
if run:
    paths = get_image_paths()
    if not paths:
        st.error("No images found. Add sample ads to data/sample_ads/ or upload your own.")
        st.stop()

    with st.spinner("Running analysis…"):
        breakdowns, scores, patterns, ideas = run_analysis(paths, brand)

    st.session_state["results"] = {
        "breakdowns": breakdowns,
        "scores": scores,
        "patterns": patterns,
        "ideas": ideas,
        "brand": brand,
        "paths": paths,
    }

if "results" not in st.session_state:
    st.markdown("## 👈 Configure and click **Run Analysis** to start")
    st.caption("Add your Lenskart (or any brand) ad screenshots to `data/sample_ads/` first.")
    st.stop()

R = st.session_state["results"]
breakdowns = R["breakdowns"]
scores     = R["scores"]
patterns   = R["patterns"]
ideas      = R["ideas"]
brand      = R["brand"]
paths      = R["paths"]

score_map     = {s["ad_id"]: s for s in scores}
breakdown_map = {b["ad_id"]: b for b in breakdowns}
path_map      = {os.path.splitext(os.path.basename(p))[0]: p for p in paths}

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Scores & Breakdown", "🔍 Pattern Analysis", "💡 Test Ideas"])

# ── TAB 1 ─────────────────────────────────────────────────────────────────────
with tab1:
    st.subheader(f"Ad Performance Ranking — {brand}")
    st.plotly_chart(score_bar_chart(scores), width='stretch')
    st.divider()

    sorted_scores = sorted(scores, key=lambda x: x["total"], reverse=True)

    for sc in sorted_scores:
        ad_id = sc["ad_id"]
        bd    = breakdown_map.get(ad_id, {})
        img_p = path_map.get(ad_id)

        with st.expander(f"{'🥇' if sc['total']>=75 else '🟡' if sc['total']>=55 else '🔴'} {ad_id}  —  {sc['total']}/100"):
            col_img, col_info = st.columns([1, 2])

            with col_img:
                if img_p and os.path.exists(img_p):
                    img = Image.open(img_p)
                    img.thumbnail((300, 300))
                    st.image(img, use_container_width=True)

            with col_info:
                st.markdown(f"<div class='score-badge'>{sc['total']}/100</div>", unsafe_allow_html=True)
                st.plotly_chart(dimension_bars(sc["dimensions"]), width='stretch', key=f"chart_{ad_id}")

            st.markdown("**Breakdown**")
            col_a, col_b, col_c = st.columns(3)

            hook  = bd.get("hook", {})
            offer = bd.get("offer", {})
            copy_ = bd.get("copy", {})
            vis   = bd.get("visual_style", {})
            trust = bd.get("trust_signals", {})

            with col_a:
                st.markdown("**Hook**")
                st.write(f"- Text: {hook.get('hook_text','—')}")
                st.write(f"- Strength: `{hook.get('hook_strength','—')}`")
                st.write(f"- Pattern interrupt: `{hook.get('pattern_interrupt')}`")
                st.markdown("**Offer**")
                st.write(f"- CTA: {offer.get('cta_text','—')} (`{offer.get('cta_strength')}`)")
                st.write(f"- Discount: `{offer.get('discount_type')}`")

            with col_b:
                st.markdown("**Copy**")
                st.write(f"- Tone: `{copy_.get('tone','—')}`")
                st.write(f"- Length: `{copy_.get('copy_length','—')}`")
                st.write(f"- Body: {copy_.get('body_copy','—')[:120]}")
                st.markdown("**Visual**")
                st.write(f"- Layout: `{vis.get('layout_type','—')}`")
                st.write(f"- People: `{vis.get('people_present')}`")

            with col_c:
                st.markdown("**Trust Signals**")
                signals = {
                    "Reviews": trust.get("has_reviews"),
                    "Ratings": trust.get("has_ratings"),
                    "UGC": trust.get("has_ugc"),
                    "Celebrity": trust.get("has_celebrity"),
                    "Press": trust.get("has_press_logo"),
                }
                for name, val in signals.items():
                    icon = "✅" if val else "❌"
                    st.write(f"{icon} {name}")

# ── TAB 2 ─────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Pattern Analysis")

    sig = patterns.get("brand_creative_signature", "")
    gap = patterns.get("biggest_gap", "")
    if sig:
        st.info(f"**Brand Signature:** {sig}")
    if gap:
        st.warning(f"**Biggest Gap:** {gap}")

    st.divider()
    col_w, col_l = st.columns(2)

    with col_w:
        st.markdown("### ✅ Winning Patterns")
        for p in patterns.get("winning_patterns", []):
            st.markdown(f"""<div class='pattern-win'>
<strong>{p['pattern']}</strong> <small>({p['confidence']} confidence)</small><br>
{p['description']}<br>
<small>Evidence: {', '.join(p['evidence'])}</small>
</div>""", unsafe_allow_html=True)

    with col_l:
        st.markdown("### ❌ Losing Patterns")
        for p in patterns.get("losing_patterns", []):
            st.markdown(f"""<div class='pattern-lose'>
<strong>{p['pattern']}</strong> <small>({p['confidence']} confidence)</small><br>
{p['description']}<br>
<small>Evidence: {', '.join(p['evidence'])}</small>
</div>""", unsafe_allow_html=True)

# ── TAB 3 ─────────────────────────────────────────────────────────────────────
with tab3:
    st.subheader(f"Creative Test Ideas for {brand}")
    st.caption("Each idea is grounded in a specific winning pattern or identified gap.")

    for i, idea in enumerate(ideas, 1):
        pri_class = "priority-high" if idea.get("priority") == "high" else "priority-medium"
        st.markdown(f"""<div class='idea-card'>
<h4>{i}. {idea['idea_title']} &nbsp;
<span class='{pri_class}'>[{idea.get('priority','').upper()}]</span>
&nbsp; <code>{idea.get('format','')}</code></h4>
<p><strong>🎣 Hook:</strong> {idea.get('hook_concept','')}</p>
<p><strong>✏️ Headline draft:</strong> <em>"{idea.get('headline_draft','')}"</em></p>
<p><strong>🎨 Visual brief:</strong> {idea.get('visual_brief','')}</p>
<p><strong>🧪 Hypothesis:</strong> {idea.get('hypothesis','')}</p>
</div>""", unsafe_allow_html=True)

# ── Export ────────────────────────────────────────────────────────────────────
st.divider()
col_dl1, col_dl2, _ = st.columns([1, 1, 4])

md_report = export_markdown(brand, breakdowns, scores, patterns, ideas)
col_dl1.download_button(
    "⬇ Export Markdown", md_report,
    file_name=f"{brand.lower()}_ad_analysis.md",
    mime="text/markdown",
)

col_dl2.download_button(
    "⬇ Export JSON",
    json.dumps({"scores": scores, "patterns": patterns, "ideas": ideas}, indent=2),
    file_name=f"{brand.lower()}_ad_analysis.json",
    mime="application/json",
)