from __future__ import annotations

import html
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
    .stApp { background:#f4f2ec; color:#171714; }
    .block-container { max-width:1080px; padding-top:1.1rem; padding-bottom:4rem; }
    .brand { font-size:1.08rem; font-weight:800; letter-spacing:.04em; margin-bottom:.6rem; }
    .hero { background:#171714; color:#fff; padding:2rem; border-radius:24px; margin:.4rem 0 1.2rem; }
    .hero h1 { font-size:clamp(2.2rem,6vw,4.5rem); line-height:1.03; margin:.25rem 0 .8rem; }
    .hero p { color:#d8d4ca; line-height:1.75; max-width:800px; }
    .eyebrow { letter-spacing:.13em; font-size:.73rem; color:#bbb5a8; }
    .news-card { background:#fffdf7; border:1px solid #ddd8cb; border-radius:18px; padding:1rem 1.1rem; margin:.65rem 0; }
    .news-card a { color:#171714; text-decoration:none; }
    .news-card a:hover { text-decoration:underline; }
    .meta { color:#716d63; font-size:.8rem; margin-top:.4rem; }
    .notice { background:#e9e4d7; border-radius:18px; padding:1rem 1.15rem; }
    div[data-testid="stButton"] button { border-radius:999px; font-weight:700; }
    </style>
    """,
    unsafe_allow_html=True,
)

TOPICS = {
    "日本で今、見落とすと困る話": "Japan important public affairs policy society",
    "仕事・賃金・物価・税金": "Japan wages inflation tax employment economy",
    "政治・制度・行政の変更": "Japan politics regulation law government policy",
    "外交・戦争・安全保障": "Japan diplomacy geopolitics war security",
    "災害・事故・犯罪・詐欺": "Japan disaster accident crime fraud public safety",
    "医療・介護・年金・福祉": "Japan healthcare nursing care pension welfare",
    "AI・科学・テクノロジー": "artificial intelligence science technology Japan",
    "地域交通・観光・インバウンド": "Japan local transport tourism inbound travel",
    "教育・子育て・若者": "Japan education childcare youth",
    "住宅・不動産・地方移住": "Japan housing real estate regional migration",
    "環境・エネルギー・食料": "Japan environment energy food agriculture",
    "企業不祥事・消費者問題": "Japan corporate scandal consumer affairs",
    "世界で注目され、日本で薄い話": "global major story underreported in Japan",
    "X・SNSで急浮上している話": "Japan X social media viral trend public issue",
    "海外から見た日本": "international media view of Japan",
}

AGE_OPTIONS = ["回答しない", "10代", "20代", "30代", "40代", "50代", "60代", "70代以上"]
GENDER_OPTIONS = ["回答しない", "男性", "女性", "その他", "自由記述"]
REGION_OPTIONS = [
    "回答しない", "北海道", "東北", "関東", "甲信越・北陸", "東海", "近畿", "中国", "四国", "九州・沖縄", "海外"
]

DEFAULTS = {
    "profile_ready": False,
    "gender": "回答しない",
    "gender_note": "",
    "age": "回答しない",
    "job": "",
    "region": "回答しない",
    "topics": [
        "日本で今、見落とすと困る話",
        "仕事・賃金・物価・税金",
        "世界で注目され、日本で薄い話",
        "海外から見た日本",
    ],
    "custom_topic": "",
    "bear": False,
    "x_trends": True,
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
            headers={"User-Agent": "YATAGARASU-VIEW/0.2"},
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


def render_items(items: list[dict[str, str]], error: str | None, empty_message: str) -> None:
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
    selected = st.session_state.topics or ["日本で今、見落とすと困る話"]
    japanese = " OR ".join(selected)
    english = " OR ".join(TOPICS.get(topic, topic) for topic in selected)
    custom = st.session_state.custom_topic.strip()
    job = st.session_state.job.strip()
    if custom:
        japanese += f" OR {custom}"
        english += f" OR {custom}"
    if job:
        japanese += f" OR {job} 業界"
        english += f" OR Japan {job} industry"
    return japanese, english


def onboarding() -> None:
    st.markdown('<div class="brand">八咫烏 VIEW</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="hero">
          <div class="eyebrow">YATAGARASU VIEW</div>
          <h1>見えていない世界を、<br>もう一方向から。</h1>
          <p>国内報道、海外報道、一次情報、社会の急な関心を並べます。答えを押しつけず、視野と判断材料を増やすための実験版です。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.subheader("最初に、あなたの視界を整える")
    st.caption("回答はすべて任意です。職業は具体的に書くほど、仕事や周辺業界の情報を拾いやすくなります。")

    with st.form("onboarding"):
        gender = st.selectbox("1. 性別", GENDER_OPTIONS, index=GENDER_OPTIONS.index(st.session_state.gender))
        gender_note = ""
        if gender == "自由記述":
            gender_note = st.text_input("性別の自由記述", value=st.session_state.gender_note)

        age = st.selectbox("2. 年齢層", AGE_OPTIONS, index=AGE_OPTIONS.index(st.session_state.age))

        job = st.text_input(
            "3. 仕事・立場を具体的に",
            value=st.session_state.job,
            placeholder="例：軽井沢で観光客を乗せるタクシードライバー／介護施設の経営／製造業の営業",
        )
        st.caption("職種だけでなく、地域・顧客・業界を書ける範囲で入れると精度が上がります。")

        region = st.selectbox("4. 主な生活・仕事地域", REGION_OPTIONS, index=REGION_OPTIONS.index(st.session_state.region))

        topics = st.multiselect(
            "5. 普段のニュースでは足りないと感じる領域",
            list(TOPICS),
            default=st.session_state.topics,
        )

        custom = st.text_area(
            "6. 個人的に追いたいテーマ",
            value=st.session_state.custom_topic,
            placeholder="例：地方のタクシー制度、観光客の変化、睡眠医療、BMWの制度変更、手書きOCR",
            height=90,
        )

        x_trends = st.checkbox(
            "X・SNSで急に話題になった社会テーマを拾う",
            value=st.session_state.x_trends,
        )
        bear = st.checkbox(
            "クマ・野生動物の安全情報を含める",
            value=st.session_state.bear,
        )

        submitted = st.form_submit_button("八咫烏 VIEWを開く", type="primary", use_container_width=True)
        if submitted:
            st.session_state.update(
                profile_ready=True,
                gender=gender,
                gender_note=gender_note,
                age=age,
                job=job,
                region=region,
                topics=topics or ["日本で今、見落とすと困る話"],
                custom_topic=custom,
                bear=bear,
                x_trends=x_trends,
            )
            st.rerun()


def settings_panel() -> None:
    st.subheader("表示設定")
    st.session_state.topics = st.multiselect("優先分野", list(TOPICS), default=st.session_state.topics)
    st.session_state.job = st.text_input("仕事・立場", value=st.session_state.job)
    st.session_state.custom_topic = st.text_area("個別テーマ", value=st.session_state.custom_topic)
    st.session_state.x_trends = st.checkbox("X・SNS急浮上テーマ", value=st.session_state.x_trends)
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

st.markdown('<div class="brand">八咫烏 VIEW　<small>GUIDE, NOT DECIDE.</small></div>', unsafe_allow_html=True)
st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">TODAY'S PERSPECTIVE</div>
      <h1>ニュースを読むから、<br>見え方を比べるへ。</h1>
      <p>公開RSSを使った実験版です。今後、同一事件の束ね、重要度判定、一次資料の照合、Xの直接トレンド取得へ発展させます。</p>
    </div>
    """,
    unsafe_allow_html=True,
)

profile_bits = [v for v in [st.session_state.job, st.session_state.region] if v and v != "回答しない"]
st.caption("設定: " + ("・".join(profile_bits) if profile_bits else "属性指定なし"))

labels = ["今日の重要", "国内と海外", "急浮上", "設定", "このアプリの姿勢"]
if st.session_state.bear:
    labels.insert(3, "クマ情報")
tabs = st.tabs(labels)

japanese_query, english_query = selected_queries()

with tabs[0]:
    st.subheader("今日、見落とすと困る入口")
    st.caption("選択分野、仕事内容、個別テーマから直近の見出しを抽出します。重要度の最終判定はまだ行いません。")
    domestic_url = google_news_url(f"({japanese_query}) when:1d")
    items, error = fetch_feed(domestic_url, 14)
    render_items(items[:10], error, "該当する見出しが見つかりませんでした。")

with tabs[1]:
    st.subheader("日本語圏と国際報道を並べる")
    left, right = st.columns(2)
    with left:
        st.markdown("### 日本語圏")
        local_url = google_news_url(f"({japanese_query}) when:2d")
        local_items, local_error = fetch_feed(local_url, 10)
        render_items(local_items[:7], local_error, "日本語圏の見出しが見つかりませんでした。")
    with right:
        st.markdown("### 国際メディア")
        sources = '(source:Reuters OR source:BBC OR source:Bloomberg OR source:"Associated Press" OR source:"Financial Times")'
        world_url = google_news_url(
            f"({english_query}) {sources} when:2d",
            language="en-US",
            country="US",
            edition="US:en",
        )
        world_items, world_error = fetch_feed(world_url, 10)
        render_items(world_items[:7], world_error, "国際メディアの見出しが見つかりませんでした。")

with tabs[2]:
    st.subheader("急に社会の関心が集まった話")
    if st.session_state.x_trends:
        st.caption("現段階ではXの公式API直結ではなく、X・SNSで話題化したテーマを報道見出しから拾う仮実装です。")
        trend_url = google_news_url(f"(X OR SNS OR 炎上 OR 急浮上 OR トレンド) ({japanese_query}) when:1d")
        trend_items, trend_error = fetch_feed(trend_url, 14)
        render_items(trend_items[:10], trend_error, "急浮上テーマが見つかりませんでした。")
    else:
        st.info("設定で『X・SNSで急に話題になった社会テーマ』をオンにすると表示されます。")

next_index = 3
if st.session_state.bear:
    with tabs[next_index]:
        st.subheader("クマ・野生動物の安全情報")
        bear_url = google_news_url("(クマ OR 熊 OR ツキノワグマ OR ヒグマ) (出没 OR 被害 OR 注意 OR 人身) when:3d")
        bear_items, bear_error = fetch_feed(bear_url, 14)
        render_items(bear_items[:10], bear_error, "該当する安全情報が見つかりませんでした。")
    next_index += 1

with tabs[next_index]:
    settings_panel()

with tabs[next_index + 1]:
    st.markdown(
        """
        <div class="notice">
        <strong>八咫烏 VIEWの姿勢</strong><br><br>
        国内報道を否定するアプリではありません。海外報道を正解と決めるアプリでもありません。<br>
        一つの情報環境だけでは見えにくい視点を増やし、利用者が自分で判断できる状態をつくります。<br><br>
        事実、解釈、予測を分け、確認できないことを断定しません。
        </div>
        """,
        unsafe_allow_html=True,
    )
