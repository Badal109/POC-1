import streamlit as st
import json
from agent.gap_agent import run_gap_analysis
from tools.snowflake_metadata import fetch_all_metadata

st.set_page_config(page_title="Gap Analysis Agent", page_icon="🔍", layout="wide")

# ── CSS ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.card { padding: 14px 18px; border-radius: 10px; margin-bottom: 10px; }
.badge { padding: 3px 10px; border-radius: 12px; font-size: 0.78em; font-weight: 700; margin-left: 8px; }
.conf-bar-bg { background: #333; border-radius: 6px; height: 8px; margin-top: 6px; }
.conf-bar { height: 8px; border-radius: 6px; }
.tag { background: #ffffff18; padding: 2px 8px; border-radius: 4px; font-size: 0.82em; margin-right: 6px; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────
st.title("🔍 CPG Retail Gap Analysis Agent")
st.caption("LangChain · Llama 3.3 70b · Groq · RETAIL_DB (Bronze/Silver/Gold)")

# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Legend")
    st.markdown("🟢 **L1** — Ready in Gold")
    st.markdown("🟡 **L2** — Silver only → promote to Gold")
    st.markdown("🟠 **L3** — Bronze only → full pipeline")
    st.markdown("🔴 **L4** — Not found → source upstream")
    st.divider()
    st.header("Confidence")
    st.markdown("🔵 **High** ≥ 75")
    st.markdown("🟣 **Medium** 50–74")
    st.markdown("⚫ **Low** < 50")
    st.divider()
    st.header("Match Type")
    st.markdown("**exact** — column name match")
    st.markdown("**partial** — substring match")
    st.markdown("**semantic** — meaning-based match")
    st.markdown("**none** — not found anywhere")
    st.divider()
    if st.button("🔄 Refresh DB Metadata"):
        st.cache_data.clear()
        st.success("Metadata cache cleared")

# ── Metadata preview ──────────────────────────────────────────────────────
with st.expander("📦 RETAIL_DB Metadata", expanded=False):
    try:
        meta = fetch_all_metadata()
        for layer, tables in meta.items():
            icon = {"BRONZE": "🥉", "SILVER": "🥈", "GOLD": "🥇"}.get(layer, "")
            st.markdown(f"**{icon} {layer}**")
            cols_data = {t: f"{len(c)} cols" for t, c in tables.items()}
            st.json(cols_data)
    except Exception as e:
        st.error(f"Could not fetch metadata: {e}")

# ── PRD Input ─────────────────────────────────────────────────────────────
st.subheader("📋 PRD Input")

col1, col2 = st.columns([3, 1])
with col1:
    default_prd = json.dumps({
        "name": "Market Share Dashboard",
        "kpis": ["MARKET_SHARE_VALUE_PCT", "TOTAL_REVENUE"],
        "dimensions": ["BRAND_NAME", "RETAILER_NAME", "CATEGORY"],
        "filters": ["PROMO_SPEND", "PROFIT_MARGIN", "CUSTOMER_LIFETIME_VALUE"]
    }, indent=2)
    prd_text = st.text_area("Paste PRD JSON", value=default_prd, height=220)

with col2:
    uploaded = st.file_uploader("Or upload JSON", type="json")
    if uploaded:
        prd_text = uploaded.read().decode("utf-8")
        st.success("File loaded ✅")
    st.markdown("---")
    st.markdown("**Fields detected:**")
    try:
        _prd = json.loads(prd_text)
        total = sum(len(_prd.get(k, [])) for k in ["kpis", "dimensions", "filters", "metrics"])
        st.metric("Total fields", total)
        for section in ["kpis", "dimensions", "filters"]:
            if _prd.get(section):
                st.markdown(f"`{section}`: {len(_prd[section])}")
    except Exception:
        st.warning("Invalid JSON")

run = st.button("▶ Run Gap Analysis", type="primary", use_container_width=True)

# ── Run ───────────────────────────────────────────────────────────────────
if run:
    try:
        prd = json.loads(prd_text)
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON: {e}")
        st.stop()

    st.divider()

    with st.spinner("🧠 Agent reasoning..."):
        try:
            result = run_gap_analysis(prd)
        except Exception as e:
            st.error(f"Agent error: {e}")
            st.stop()

    # ── Parse output ──────────────────────────────────────────────────
    raw_output = result.get("output", "")
    raw_output = raw_output.replace("```json", "").replace("```", "").strip()

    try:
        gap_data = json.loads(raw_output)
    except Exception:
        st.warning("Could not parse structured output")
        st.code(raw_output)
        st.stop()

    # ── Summary metrics ───────────────────────────────────────────────
    st.subheader("📊 Summary")
    levels = [r.get("level", "?") for r in gap_data]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Fields", len(gap_data))
    c2.metric("🟢 L1 Ready", levels.count("L1"))
    c3.metric("🟡 L2 Promote", levels.count("L2"))
    c4.metric("🟠 L3 Pipeline", levels.count("L3"))
    c5.metric("🔴 L4 Missing", levels.count("L4"))

    # Coverage score
    coverage = round((levels.count("L1") * 1.0 + levels.count("L2") * 0.6 +
                      levels.count("L3") * 0.3) / max(len(levels), 1) * 100, 1)
    st.progress(int(coverage), text=f"Coverage Score: {coverage}% — L1 full weight, L2 60%, L3 30%")

    st.divider()

    # ── Filter controls ───────────────────────────────────────────────
    st.subheader("🗂 Gap Report")
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        level_filter = st.multiselect("Filter by Level", ["L1", "L2", "L3", "L4"],
                                       default=["L1", "L2", "L3", "L4"])
    with filter_col2:
        conf_filter = st.multiselect("Filter by Confidence", ["High", "Medium", "Low"],
                                      default=["High", "Medium", "Low"])

    # ── Field cards ───────────────────────────────────────────────────
    COLORS = {
        "L1": ("#1a3a1a", "#2d7a2d", "🟢"),
        "L2": ("#3a3a0a", "#a0960a", "🟡"),
        "L3": ("#3a1a00", "#c06010", "🟠"),
        "L4": ("#3a0a0a", "#b03030", "🔴"),
    }
    MATCH_ICONS = {"exact": "🎯", "partial": "🔍", "semantic": "🧠", "none": "❌"}

    for item in gap_data:
        level = item.get("level", "?")
        conf = item.get("confidence_label") or item.get("confidence", {}).get("label", "?") if isinstance(item.get("confidence"), dict) else "?"
        conf_score = item.get("confidence_score") or (item.get("confidence", {}).get("score", 0) if isinstance(item.get("confidence"), dict) else 0)

        if level not in level_filter:
            continue
        if conf not in conf_filter and conf != "?":
            continue

        bg, accent, icon = COLORS.get(level, ("#222", "#888", "⚪"))
        match_icon = MATCH_ICONS.get(item.get("match_type", "none"), "?")
        bar_color = {"High": "#2d7a2d", "Medium": "#a0960a", "Low": "#b03030"}.get(conf, "#555")
        bar_width = int(conf_score) if conf_score else 0

        table_info = item.get("found_in_table") or "Not found"
        layer_info = item.get("found_in_layer") or "—"
        action = item.get("action", "")
        match_type = item.get("match_type", "none")

        st.markdown(f"""
        <div class="card" style="background:{bg};border-left:4px solid {accent};">
            <div style="display:flex;align-items:center;justify-content:space-between;">
                <span style="font-size:1.1em;font-weight:700;color:#fff;">
                    {icon} {item.get('field','')}
                </span>
                <span>
                    <span class="badge" style="background:{accent};color:#fff;">{level}</span>
                    <span class="badge" style="background:#333;color:#ccc;">{conf} {conf_score}</span>
                </span>
            </div>
            <div style="margin-top:8px;">
                <span class="tag">{match_icon} {match_type}</span>
                <span class="tag">📁 {layer_info}</span>
                <span class="tag">🗄 {table_info}</span>
            </div>
            <div class="conf-bar-bg">
                <div class="conf-bar" style="width:{bar_width}%;background:{bar_color};"></div>
            </div>
            <div style="color:#aaa;font-size:0.82em;margin-top:6px;">{action}</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ── Download ──────────────────────────────────────────────────────
    st.download_button(
        "⬇ Download Gap Report JSON",
        data=json.dumps(gap_data, indent=2),
        file_name=f"gap_report_{prd.get('name','report').replace(' ','_')}.json",
        mime="application/json",
        use_container_width=True
    )