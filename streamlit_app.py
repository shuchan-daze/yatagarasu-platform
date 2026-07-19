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
    .brand { font-weight:900; letter-spacing:.08em; font-size:1rem; opacity:.92; }
    .hero { border-radius:28px; padding:2.2rem; margin:.8rem 0 1.4rem;
      background:linear-gradient(145deg,#16213e,#0f3460 45%,#533483 100%); box-shadow:0 20px 60px rgba(0,0,0,.35); }
    .hero h1 { font-size:clamp(2.4rem,7vw,5.2rem); line-height:1.02; margin:.2rem 0 .8rem; }
    .hero p { font-size:1.05rem; line-height:1.8; color:#e8e8ef; max-width:760px; }
    .question { text-align:center; margin:1.4rem 0 .25rem; font-size:clamp(1.35rem,4vw,2.1rem); font-weight:850; }
    .clock-display { text-align:center; font-size:clamp(4rem,16vw,8rem); font-weight:950; letter-spacing:-.07em; line-height:1; margin:.35rem 0 .7rem; }
    .scene { position:relative; overflow:hidden; border-radius:30px; min-height:360px; margin:1rem 0 1.2rem;
      background-position:center; background-size:cover; box-shadow:0 24px 70px rgba(0,0,0,.45); }
    .scene::after { content:""; position:absolute; inset:0; background:linear-gradient(180deg,rgba(0,0,0,.04),rgba(0,0,0,.62)); }
    .scene-copy { position:absolute; z-index:2; left:1.45rem; right:1.45rem; bottom:1.25rem; }
    .scene-kicker { font-size:.78rem; letter-spacing:.15em; opacity:.85; font-weight:800; }
    .scene-label { font-size:clamp(1.35rem,4vw,2.2rem); font-weight:900; margin-top:.2rem; }
    .slider-help { text-align:center; color:#bfc7d8; margin:-.2rem 0 .3rem; font-size:.9rem; }
    .news-card { background:#151923; border:1px solid #2a3040; border-radius:24px; padding:1.2rem 1.25rem; margin:.8rem 0; }
    .news-card a { color:#fff; text-decoration:none; font-size:1.06rem; }
    .news-card a:hover { text-decoration:underline; }
    .meta { color:#aab2c5; font-size:.8rem; margin-top:.5rem; }
    div[data-testid="stButton"] button { border-radius:999px; font-weight:800; min-height:3rem; }
    div[data-testid="stSlider"] { padding-top:.2rem; }
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


def scene_for(slot: int) -> tuple[str, str, str]:
    hour = slot / 2
    if 5 <= hour < 9:
        return (
            "https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?auto=format&fit=crop&w=1600&q=88",
            "MORNING",
            "朝の光とともに、世界が届く",
        )
    if 9 <= hour < 16:
        return (
            "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1600&q=88",
            "DAYLIGHT",
            "空が広がる時間に、世界が届く",
        )
    if 16 <= hour < 19:
        return (
            "https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=1600&q=88",
            "SUNSET",
            "夕色の中で、世界が届く",
        )
    if 19 <= hour < 24:
        return (
            "https://images.unsplash.com/photo-1519681393784-d120267933ba?auto=format&fit=crop&w=1600&q=88",
            "NIGHT",
            "静かな夜に、世界が届く",
        )
    return (
        "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1600&q=88",
        "BEFORE DAWN",
        "夜明け前の静けさに、世界が届く",
    )


def google_news_url(query: str) -> str:
    return f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=ja&gl=JP&ceid=JP:ja"


@st.cache_data(ttl=900, show_spinner=False)
def fetch_feed(query: str, limit: int = 12) -> list[dict[str, str]]:
    try:
        response = requests.get(google_news_url(query), timeout=12, headers={"User-Agent": "YATAGARASU-VIEW/0.4"})
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

    current_slot = int(st.session_state.delivery_slot)
    current_time = slot_to_time(current_slot)
    image_url, kicker, scene_label = scene_for(current_slot)

    st.markdown('<div class="question">何時に、今日の世界を受け取りますか？</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="clock-display">{current_time}</div>', unsafe_allow_html=True)
    st.markdown(
        f'''
        <div class="scene" style="background-image:url('{image_url}');">
          <div class="scene-copy">
            <div class="scene-kicker">{kicker}</div>
            <div class="scene-label">{scene_label}</div>
          </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="slider-help">左右に動かすと、30分単位で時間と景色が変わります</div>', unsafe_allow_html=True)
    slot = st.slider("配信時間", 0, 47, current_slot, label_visibility="collapsed", key="onboarding_slot")

    if slot != current_slot:
        st.session_state.delivery_slot = slot
        st.rerun()

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

items = fetch_feed("日本 世界 重要ニュース when:1d", 15)
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
    render_news(fetch_feed("クマ 出没 長野 群馬 軽井沢 when:3d", 8), 4)

with st.expander("配信時間を変える"):
    new_slot = st.slider("配信時間", 0, 47, int(st.session_state.delivery_slot))
    if st.button("時間を更新"):
        st.session_state.delivery_slot = new_slot
        st.rerun()
