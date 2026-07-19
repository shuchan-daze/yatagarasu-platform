from __future__ import annotations

import html
from typing import Any
from urllib.parse import quote_plus

import feedparser
import requests
import streamlit as st

st.set_page_config(page_title="八咫烏 VIEW", page_icon="🪶", layout="wide", initial_sidebar_state="collapsed")

st.markdown(
    """
    <style>
    .stApp { background:#090b12; color:#f7f7f3; }
    .block-container { max-width:980px; padding-top:1rem; padding-bottom:5rem; }
    .brand { font-weight:900; letter-spacing:.08em; font-size:1rem; opacity:.9; }
    .hero { border-radius:28px; padding:2.2rem; margin:.8rem 0 1.4rem;
      background:linear-gradient(145deg,#16213e,#0f3460 45%,#533483 100%); box-shadow:0 20px 60px rgba(0,0,0,.35); }
    .hero h1 { font-size:clamp(2.4rem,7vw,5.2rem); line-height:1.02; margin:.2rem 0 .8rem; }
    .hero p { font-size:1.05rem; line-height:1.8; color:#e8e8ef; max-width:760px; }
    .time-card { border-radius:28px; padding:1.5rem 1.6rem; margin:1rem 0;
      background:linear-gradient(135deg,var(--c1),var(--c2)); min-height:220px; display:flex; flex-direction:column; justify-content:flex-end;
      box-shadow:0 18px 45px rgba(0,0,0,.28); }
    .time-card .clock { font-size:clamp(3rem,12vw,7rem); font-weight:900; letter-spacing:-.05em; }
    .time-card .label { font-size:1.05rem; opacity:.92; }
    .news-card { background:#151923; border:1px solid #2a3040; border-radius:24px; padding:1.2rem 1.25rem; margin:.8rem 0; }
    .news-card a { color:#fff; text-decoration:none; font-size:1.06rem; }
    .news-card a:hover { text-decoration:underline; }
    .meta { color:#aab2c5; font-size:.8rem; margin-top:.5rem; }
    .soft { background:#111520; border:1px solid #293044; border-radius:22px; padding:1rem 1.1rem; }
    div[data-testid="stButton"] button { border-radius:999px; font-weight:800; min-height:3rem; }
    div[data-testid="stSlider"] { padding-top:.5rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

DEFAULTS = {
    "started": False,
    "delivery_slot": 16,
    "bear": False,
    "depth": 0,
    "feedback": [],
}
for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, value)


def slot_to_time(slot: int) -> str:
    minutes = slot * 30
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def sky(slot: int) -> tuple[str, str, str]:
    hour = slot / 2
    if 5 <= hour < 9:
        return "#ff9966", "#ff5e62", "朝の光がほどける時間"
    if 9 <= hour < 16:
        return "#56ccf2", "#2f80ed", "空がいちばん高く見える時間"
    if 16 <= hour < 19:
        return "#f7971e", "#ffd200", "世界が夕色に変わる時間"
    if 19 <= hour < 24:
        return "#141e30", "#243b55", "街の音が少し静かになる時間"
    return "#020024", "#090979", "星の下で世界を受け取る時間"


def google_news_url(query: str) -> str:
    return f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=ja&gl=JP&ceid=JP:ja"


@st.cache_data(ttl=900, show_spinner=False)
def fetch_feed(query: str, limit: int = 12) -> list[dict[str, str]]:
    try:
        response = requests.get(google_news_url(query), timeout=12, headers={"User-Agent": "YATAGARASU-VIEW/0.3"})
        response.raise_for_status()
        parsed = feedparser.parse(response.content)
        items: list[dict[str, str]] = []
        for entry in parsed.entries[:limit]:
            source_data: Any = entry.get("source", {})
            source = source_data.get("title", "") if isinstance(source_data, dict) else ""
            items.append({
                "title": str(entry.get("title", "見出しなし")),
                "link": str(entry.get("link", "")),
                "published": str(entry.get("published", "")),
                "source": str(source),
            })
        return items
    except requests.RequestException:
        return []


def render_news(items: list[dict[str, str]], limit: int) -> None:
    if not items:
        st.info("いま取得できる見出しがありません。少し時間を置いて更新してください。")
        return
    for item in items[:limit]:
        title = html.escape(item["title"])
        link = html.escape(item["link"], quote=True)
        source = html.escape(item["source"] or "配信元表記なし")
        st.markdown(
            f'<div class="news-card"><a href="{link}" target="_blank"><strong>{title}</strong></a><div class="meta">{source}</div></div>',
            unsafe_allow_html=True,
        )


def onboarding() -> None:
    st.markdown('<div class="brand">八咫烏 VIEW</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="hero">
          <h1>世界は、<br>取りに行かなくていい。</h1>
          <p>必要なことは八咫烏が届けます。最初に決めるのは、受け取る時間だけです。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    slot = st.slider("", 0, 47, int(st.session_state.delivery_slot), label_visibility="collapsed")
    c1, c2, label = sky(slot)
    time_text = slot_to_time(slot)
    st.markdown(
        f'<div class="time-card" style="--c1:{c1};--c2:{c2};"><div class="label">{label}</div><div class="clock">{time_text}</div><div class="label">この時間に、今日の世界を届けます</div></div>',
        unsafe_allow_html=True,
    )

    bear = st.toggle("クマ・野生動物の安全情報も受け取る", value=st.session_state.bear)
    if st.button("この時間から始める", type="primary", use_container_width=True):
        st.session_state.delivery_slot = slot
        st.session_state.bear = bear
        st.session_state.started = True
        st.rerun()


if not st.session_state.started:
    onboarding()
    st.stop()

st.markdown('<div class="brand">八咫烏 VIEW　<small>GUIDE, NOT DECIDE.</small></div>', unsafe_allow_html=True)

hour = st.session_state.delivery_slot / 2
if 5 <= hour < 11:
    greeting = "今日の世界が、静かに届きました。"
elif 11 <= hour < 18:
    greeting = "いま知っておきたい流れを、まとめました。"
else:
    greeting = "今日、世界で動いたことを振り返ります。"

st.markdown(
    f"""
    <div class="hero">
      <h1>{greeting}</h1>
      <p>今日は決まった本数ではありません。世界の動きに合わせて、必要な分だけ並べます。</p>
    </div>
    """,
    unsafe_allow_html=True,
)

query = "日本 世界 重要ニュース when:1d"
items = fetch_feed(query, 15)
initial_count = 4 if len(items) >= 4 else len(items)
render_news(items, initial_count + st.session_state.depth * 4)

if items and initial_count + st.session_state.depth * 4 < len(items):
    if st.button("もう少し先を見る", use_container_width=True):
        st.session_state.depth += 1
        st.rerun()

st.markdown("### どう感じましたか？")
st.caption("うまくまとめなくて大丈夫です。ひとことでも、長く話しても構いません。")
feedback = st.text_area("感想", placeholder="例：これは自分の仕事にも関係ありそう／海外ではどう見ているのか気になる", label_visibility="collapsed")
col1, col2, col3 = st.columns(3)
with col1:
    liked = st.button("👍 もっと見たい", use_container_width=True)
with col2:
    bored = st.button("😐 いまいち", use_container_width=True)
with col3:
    saved = st.button("💬 感想を残す", use_container_width=True)

if liked or bored or saved:
    st.session_state.feedback.append({"reaction": "more" if liked else "less" if bored else "comment", "text": feedback})
    st.success("受け取りました。八咫烏は、ここから少しずつ育っていきます。")

if st.session_state.bear:
    st.markdown("### クマ・野生動物")
    bear_items = fetch_feed("クマ 出没 長野 群馬 軽井沢 when:3d", 8)
    render_news(bear_items, 4)

with st.expander("配信時間を変える"):
    new_slot = st.slider("配信時間", 0, 47, int(st.session_state.delivery_slot))
    if st.button("時間を更新"):
        st.session_state.delivery_slot = new_slot
        st.rerun()
