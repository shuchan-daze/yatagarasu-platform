from __future__ import annotations

import html
import re
from datetime import datetime
from typing import Any
from urllib.parse import quote_plus

import feedparser
import requests
import streamlit as st

st.set_page_config(
    page_title="八咫烏 VIEW",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .stApp { background: #f4f2ec; color: #171714; }
    .block-container { max-width: 1080px; padding-top: 1.2rem; padding-bottom: 4rem; }
    .hero { background:#171714; color:white; padding:2rem; border-radius:24px; margin:.5rem 0 1.2rem; }
    .hero h1 { font-size:clamp(2.1rem,6vw,4.4rem); line-height:1.03; margin:.2rem 0 .8rem; }
    .hero p { color:#d8d4ca; line-height:1.75; max-width:760px; }
    .eyebrow { letter-spacing:.12em; font-size:.75rem; color:#bcb7aa; }
    .news-card { background:#fffdf7; border:1px solid #ddd8cb; border-radius:18px; padding:1rem 1.1rem; margin:.7rem 0; }
    .news-card a { color:#171714; text-decoration:none; }
    .news-card a:hover { text-decoration:underline; }
    .meta { color:#716d63; font-size:.82rem; margin-top:.45rem; }
    .principle { background:#e9e4d7; border-radius:18px; padding:1rem 1.2rem; }
    div[data-testid="stButton"] button { border-radius:999px; font-weight:700; }
    </style>
    """,
    unsafe_allow_html=True,
)

TOPICS = {
    "国民として重要": "Japan government policy public safety",
    "仕事・景気・物価": "Japan economy wages inflation employment",
    "政治・制度": "Japan politics law regulation policy",
    "外交・安全保障": "Japan diplomacy security geopolitics",
    "災害・防犯": "Japan disaster crime public safety",
    "科学・AI": "science artificial intelligence Japan",
    "医療・福祉": "Japan health healthcare welfare",
    "地域交通": "Japan local transport mobility",
}

AGE_OPTIONS = ["回答しない", "10代", "20代", "30代", "40代", "50代", "60代", "70代以上"]
GENDER_OPTIONS = ["回答しない", "男性", "女性", "その他・自由回答"]
JOB_OPTIONS = [
    "回答しない",
    "会社員",
    "自営業・経営",
    "交通・物流",
    "医療・福祉",
    "教育・研究",
    "観光・接客",
    "公務・団体",
    "学生",
    "無職・退職",
    "その他",
]
REGION_OPTIONS = [
    "回答しない",
    "北海道",
    "東北",
    "関東",
    "甲信越・北陸",
    "東海",
    "近畿",
    "中国",
    "四国",
    "九州・沖縄",
    "海外",
]

DEFAULTS = {
    "profile_ready": False,
    "age": "回答しない",
    "gender": "回答しない",
    "job": "回答しない",
    "region": "回答しない",
    "topics": ["国民として重要", "仕事・景気・物価", "政治・制度", "外交・安全保障"],
    "custom_topic": "",
    "bear": False,
}
for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, value)


def google_news_url(query: str, *, language: str = "ja", country: str = "JP", edition: str = "JP:ja") -> str:
    return (
        "https://news.google.com/rss/search"
        f"?q={quote_plus(query)}&hl={language}&gl={country}&ceid={edition}"
    )


@st.cache_data(ttl=900, show_spinner=False)
def fetch_feed(url: str, limit: int = 20) -> tuple[list[dict[str, str]], str | None]:
    try:
        response = requests.get(
            url,
            timeout=12,
            headers={
                "User-Agent": "YATAGARASU-VIEW/0.1 (+https://github.com/shuchan-daze/yatagarasu-platform)"
            },
        )
        response.raise_for_status()
        parsed = feedparser.parse(response.content)
        items: list[dict[str, str]] = []
        for entry in parsed.entries[:limit]:
            source_data: Any = entry.get("source", {})
            source = source_data.get("title", "") if isinstance(source_data, dict) else ""
            items.append(
                {
                    "title": str(entry.get("title", "見出しなし")),
                    "link": str(entry.get("link", "")),
                    "published": str(entry.get("published", "")),
                    "source": str(source),
                }
            )
        return items, None
    except requests.RequestException as exc:
        return [], f"ニュース取得に失敗しました: {exc.__class__.__name__}"


def render_items(items: list[dict[str, str]], error: str | None, *, empty_message: str) -> None:
    if error:
        st.warning(error)
        return
    if not items:
        st.info(empty_message)
        return
    for item in items:
        title = html.escape(item["title"])
        link = html.escape(item["link"], quote=True)
        source = html.escape(item["source"] or "配信元表記なし")
        published = html.escape(item["published"])
        st.markdown(
            f"""
            <div class="news-card">
              <strong><a href="{link}" target="_blank" rel="noopener noreferrer">{title}</a></strong>
              <div class="meta">{source}{' ｜ ' + published if published else ''}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def selected_queries() -> tuple[str, str]:
    selected = st.session_state.topics or ["国民として重要"]
    japanese = " OR ".join(selected)
    english = " OR ".join(TOPICS.get(topic, topic) for topic in selected)
    custom = st.session_state.custom_topic.strip()
    if custom:
        japanese += f" OR {custom}"
        english += f" OR {custom}"
    return japanese, english


def onboarding() -> None:
    st.markdown(
        """
        <div class="hero">
          <div class="eyebrow">YATAGARASU INFORMATION LENS</div>
          <h1>一つのニュースに、<br>もう一つの視点を。</h1>
          <p>国内の見出し、海外の見出し、一次情報への入口を分けて示します。結論を押しつけず、判断材料を増やすための実験アプリです。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.subheader("あなたに必要な視界をつくる")
    st.caption("すべて任意回答です。この実験版では外部データベースへ保存しません。")
    with st.form("onboarding"):
        left, right = st.columns(2)
        with left:
            age = st.selectbox("年齢層", AGE_OPTIONS, index=AGE_OPTIONS.index(st.session_state.age))
            job = st.selectbox("仕事・立場", JOB_OPTIONS, index=JOB_OPTIONS.index(st.session_state.job))
        with right:
            gender = st.selectbox("性別", GENDER_OPTIONS, index=GENDER_OPTIONS.index(st.session_state.gender))
            region = st.selectbox("地域", REGION_OPTIONS, index=REGION_OPTIONS.index(st.session_state.region))
        topics = st.multiselect("知りたい分野", list(TOPICS), default=st.session_state.topics)
        custom = st.text_input(
            "個人的に追いたいテーマ",
            value=st.session_state.custom_topic,
            placeholder="例：介護制度、観光業、農業、地域交通",
        )
        bear = st.checkbox("クマ・野生動物の安全情報を含める", value=st.session_state.bear)
        submitted = st.form_submit_button("八咫烏 VIEWを開く", type="primary", use_container_width=True)
        if submitted:
            st.session_state.update(
                profile_ready=True,
                age=age,
                gender=gender,
                job=job,
                region=region,
                topics=topics or ["国民として重要"],
                custom_topic=custom,
                bear=bear,
            )
            st.rerun()


def settings_panel() -> None:
    st.subheader("表示設定")
    st.session_state.topics = st.multiselect("優先分野", list(TOPICS), default=st.session_state.topics)
    st.session_state.custom_topic = st.text_input("個別テーマ", value=st.session_state.custom_topic)
    st.session_state.bear = st.checkbox("クマ・野生動物情報", value=st.session_state.bear)
    if st.button("設定を反映", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    if st.button("導入画面へ戻る", use_container_width=True):
        st.session_state.profile_ready = False
        st.rerun()


if not st.session_state.profile_ready:
    onboarding()
    st.stop()

st.markdown("**八咫烏 VIEW**　<small>GUIDE, NOT DECIDE.</small>", unsafe_allow_html=True)
st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">TODAY'S PERSPECTIVE</div>
      <h1>見出しを比べて、<br>判断材料を増やす。</h1>
      <p>現在は公開RSS見出しを並べる最初の実験版です。重要度の自動判定、同一事件の束ね、AI要約、一次資料との照合は次の段階で実装します。</p>
    </div>
    """,
    unsafe_allow_html=True,
)

profile_bits = [value for value in [st.session_state.job, st.session_state.region] if value != "回答しない"]
st.caption(
    "設定: "
    + ("・".join(profile_bits) if profile_bits else "属性指定なし")
    + " ｜ "
    + "・".join(st.session_state.topics)
)

labels = ["今日", "国内と海外", "視差メモ", "設定", "姿勢"]
if st.session_state.bear:
    labels.insert(2, "クマ情報")
tabs = st.tabs(labels)

japanese_query, english_query = selected_queries()

with tabs[0]:
    st.subheader("今日の入口")
    st.caption("選んだ分野と直近24時間前後の見出しを機械的に抽出しています。『重要』と断定する段階ではありません。")
    domestic_url = google_news_url(f"({japanese_query}) when:1d")
    domestic, domestic_error = fetch_feed(domestic_url, 10)
    render_items(domestic[:8], domestic_error, empty_message="該当する見出しが見つかりませんでした。")
    if st.button("最新状態に更新", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with tabs[1]:
    st.subheader("日本語圏と国際報道を並べる")
    st.caption("同一事件を自動対応させる機能は未実装です。現段階では、同じ関心分野を左右に並べて視点の違いを探します。")
    left, right = st.columns(2)
    with left:
        st.markdown("### 日本語圏の見出し")
        local_url = google_news_url(f"({japanese_query}) when:2d")
        local_items, local_error = fetch_feed(local_url, 10)
        render_items(local_items[:6], local_error, empty_message="日本語圏の見出しが見つかりませんでした。")
    with right:
        st.markdown("### 国際メディアの見出し")
        trusted_sources = '(source:Reuters OR source:BBC OR source:Bloomberg OR source:"Associated Press")'
        world_url = google_news_url(
            f"({english_query}) {trusted_sources} when:2d",
            language="en-US",
            country="US",
            edition="US:en",
        )
        world_items, world_error = fetch_feed(world_url, 12)
        render_items(world_items[:6], world_error, empty_message="国際メディアの見出しが見つかりませんでした。")

next_index = 2
if st.session_state.bear:
    with tabs[2]:
        st.subheader("クマ・野生動物の安全情報")
        region_word = "" if st.session_state.region == "回答しない" else st.session_state.region
        bear_url = google_news_url(f"クマ OR 熊 {region_word} when:7d")
        bear_items, bear_error = fetch_feed(bear_url, 15)
        render_items(bear_items[:10], bear_error, empty_message="直近の関連見出しが見つかりませんでした。")
        st.caption("緊急時は、自治体・警察・防災無線などの一次情報を優先してください。")
    next_index = 3

with tabs[next_index]:
    st.subheader("視差メモ")
    st.caption("二つの記事の見出しや要約を貼り、数字と表現の差を確認します。内容の真偽は判定しません。")
    left, right = st.columns(2)
    with left:
        text_a = st.text_area("国内側の見出し・要約", height=180)
    with right:
        text_b = st.text_area("海外側の見出し・要約", height=180)
    if st.button("差を整理する", type="primary", use_container_width=True):
        if not text_a.strip() or not text_b.strip():
            st.warning("両方の文章を入力してください。")
        else:
            number_pattern = r"\d[\d,.]*(?:%|％|円|ドル|人|件|年|月|日|倍|兆|億|万)?"
            numbers_a = re.findall(number_pattern, text_a)
            numbers_b = re.findall(number_pattern, text_b)
            c1, c2, c3 = st.columns(3)
            c1.metric("国内側の文字数", len(text_a))
            c2.metric("海外側の文字数", len(text_b))
            c3.metric("数字表現数の差", abs(len(numbers_a) - len(numbers_b)))
            st.write("**国内側の数字:**", "、".join(numbers_a) or "なし")
            st.write("**海外側の数字:**", "、".join(numbers_b) or "なし")
            st.info("片方だけにある数字・固有名詞・評価語は、元資料で確認する候補です。")

with tabs[next_index + 1]:
    settings_panel()

with tabs[next_index + 2]:
    st.subheader("このアプリの姿勢")
    st.markdown(
        """
        <div class="principle">
        <strong>国内報道を否定するアプリではありません。</strong><br><br>
        海外報道を正解とするアプリでもありません。複数の情報環境を並べ、利用者自身が見落としていた前提や違いに気づける状態を目指します。
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        - 事実、解釈、推測を分ける
        - 可能な限り一次資料へ戻れるリンクを残す
        - 一社の『信頼度点数』で真偽を決めない
        - 読者の属性を思想誘導に使わない
        - 記事本文を無断転載しない
        """
    )
    st.caption(f"Prototype 0.1 ｜ {datetime.now().strftime('%Y-%m-%d')}")
