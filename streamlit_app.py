from __future__ import annotations

import json
import os
import random
import re
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "pythonProject" / "novels_with_ai_fields.xlsx"

st.set_page_config(page_title="AI BL 搜文助手", page_icon="📚", layout="wide")


def inject_style() -> None:
    st.markdown(
        """
        <style>
        :root {
            --paper: #faf6ef;
            --ink: #161820;
            --muted: #756f68;
            --line: #d9cdbd;
            --accent: #cf5361;
            --brown: #7c5b52;
            --soft: #fffdf8;
            --chip: #edf3ee;
        }
        html, body, [data-testid="stAppViewContainer"] {
            background: var(--paper);
            color: var(--ink);
        }
        [data-testid="stHeader"] { background: transparent; }
        .block-container {
            max-width: 1120px;
            padding: 2rem 1rem 6rem;
        }
        h1, h2, h3 { letter-spacing: 0 !important; }
        .app-title {
            font-size: clamp(34px, 6vw, 64px);
            line-height: 1.05;
            font-weight: 800;
            margin: 0.2rem 0 0.7rem;
        }
        .eyebrow {
            color: var(--accent);
            font-weight: 800;
            letter-spacing: 0 !important;
        }
        .muted { color: var(--muted); font-size: 1.03rem; }
        .panel {
            background: rgba(255,253,248,0.88);
            border: 1px solid var(--line);
            border-radius: 28px;
            padding: 1.25rem;
            box-shadow: 0 18px 45px rgba(68,52,38,.08);
        }
        .book-card {
            background: linear-gradient(90deg, #fffdf8 0%, #fffdf8 48%, #f7f0e6 50%, #fffdf8 52%, #fffdf8 100%);
            border: 1px solid var(--line);
            border-radius: 24px;
            padding: 1.3rem;
            margin: 0 0 1rem;
            box-shadow: 0 18px 40px rgba(68,52,38,.08);
        }
        .card-head {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 1rem;
        }
        .book-title {
            font-size: clamp(27px, 5vw, 44px);
            line-height: 1.12;
            margin: .3rem 0 .35rem;
            font-weight: 800;
            font-family: Georgia, "Songti SC", serif;
        }
        .author { color: var(--muted); font-weight: 700; }
        .hook {
            margin: 1rem 0;
            padding: 1rem 1rem 1rem 1.15rem;
            border-left: 5px solid var(--accent);
            border-radius: 18px;
            background: #fff0ee;
            color: #30231f;
            font-size: 1.08rem;
            font-weight: 800;
            line-height: 1.65;
        }
        .summary {
            color: #443833;
            line-height: 1.8;
            font-size: 1.02rem;
        }
        .chips {
            display: flex;
            flex-wrap: wrap;
            gap: .55rem;
            margin: .9rem 0 .4rem;
        }
        .chip {
            background: var(--chip);
            color: #315b53;
            border-radius: 999px;
            padding: .35rem .7rem;
            font-weight: 700;
            font-size: .9rem;
        }
        .feed-card {
            min-height: 185px;
            border: 1px solid var(--line);
            background: #fffdf8;
            border-radius: 22px;
            padding: 1.1rem;
            box-shadow: 0 12px 34px rgba(68,52,38,.07);
        }
        .feed-hook {
            color: var(--accent);
            font-weight: 800;
            line-height: 1.5;
            margin-bottom: .9rem;
        }
        .lot {
            border-radius: 28px;
            min-height: 360px;
            background: linear-gradient(135deg, #fff8eb, #f6ddbb);
            border: 1px solid #d9b77b;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            box-shadow: inset 0 0 0 8px rgba(255,255,255,.42), 0 18px 46px rgba(97,57,22,.16);
            padding: 2rem;
        }
        .lot-title { color: var(--accent); font-weight: 800; }
        .lot-main { font-size: clamp(30px, 5vw, 52px); font-weight: 900; margin: 1rem 0; }
        .chat-box {
            background: #f1efea;
            border: 1px solid #ded5ca;
            border-radius: 34px;
            padding: 1rem;
            max-width: 760px;
            margin: auto;
        }
        .bubble {
            border-radius: 22px;
            padding: .85rem 1rem;
            margin: .65rem 0;
            line-height: 1.65;
            max-width: 82%;
        }
        .bubble.user {
            margin-left: auto;
            background: #d45a5a;
            color: white;
        }
        .bubble.assistant {
            background: #fffdf8;
            border: 1px solid var(--line);
        }
        .empty {
            padding: 4rem 1.5rem;
            text-align: center;
            border: 1px dashed var(--line);
            border-radius: 28px;
            color: var(--muted);
            background: rgba(255,253,248,.72);
        }
        div.stButton > button, div.stLinkButton > a {
            border-radius: 999px !important;
            border: 1px solid var(--line) !important;
            min-height: 44px;
            font-weight: 800 !important;
        }
        .primary-action div.stButton > button {
            background: #161820 !important;
            color: white !important;
            border: 0 !important;
        }
        @media (max-width: 720px) {
            .block-container { padding: 1.2rem .85rem 5rem; }
            .book-card { padding: 1rem; border-radius: 20px; }
            .panel { padding: 1rem; border-radius: 22px; }
            .hook { font-size: 1rem; }
            .lot { min-height: 300px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def safe_text(value) -> str:
    if value is None:
        return ""
    text = str(value)
    if text.lower() == "nan":
        return ""
    return text.strip()


def split_tags(value: str) -> list[str]:
    for sep in ["，", "、", "/", "|", ";", "；", "\n"]:
        value = value.replace(sep, " ")
    seen: set[str] = set()
    tags: list[str] = []
    for item in value.split():
        item = item.strip("# ")
        if item and item not in seen:
            seen.add(item)
            tags.append(item)
    return tags


@st.cache_data(show_spinner=False)
def load_books() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    frame = pd.read_excel(DATA_FILE).fillna("")
    books: list[dict] = []
    for idx, row in frame.iterrows():
        title = safe_text(row.get("title") or row.get("书名"))
        if not title:
            continue
        tags = split_tags(
            " ".join(
                [
                    safe_text(row.get("character_tags")),
                    safe_text(row.get("plot_points")),
                    safe_text(row.get("platform_tags")),
                ]
            )
        )
        hook = safe_text(row.get("hook_line") or row.get("social_hook") or row.get("one_line_hook"))
        books.append(
            {
                "id": safe_text(row.get("link")) or f"{title}-{safe_text(row.get('author'))}-{idx}",
                "title": title,
                "author": safe_text(row.get("author") or row.get("作者")),
                "platform": safe_text(row.get("platform")),
                "status": "完结" if bool(row.get("is_finished")) else "连载",
                "word_count": safe_text(row.get("word_count")),
                "heat": safe_text(row.get("heat_level")),
                "tags": tags[:9],
                "hook": hook or f"《{title}》可以先收进备选，看看是不是你的那口。",
                "summary": safe_text(row.get("summary_display") or row.get("summary_core")),
                "intro": safe_text(row.get("original_intro") or row.get("简介")),
                "link": safe_text(row.get("link")),
            }
        )
    return books


BOOKS = load_books()


def init_state() -> None:
    st.session_state.setdefault("favorites", [])
    st.session_state.setdefault("chat_messages", [
        {"role": "assistant", "text": "你可以直接说想看的感觉，不用想标签。比如“想看攻很高高在上但最后彻底栽了”，我会帮你慢慢缩小到具体文。", "items": []}
    ])
    st.session_state.setdefault("last_lot", None)


def book_key(book: dict) -> str:
    return safe_text(book.get("id")) or f"{book.get('title')}-{book.get('author')}"


def is_fav(book: dict) -> bool:
    return book_key(book) in st.session_state.favorites


def toggle_fav(book: dict) -> None:
    key = book_key(book)
    if key in st.session_state.favorites:
        st.session_state.favorites.remove(key)
        st.toast("已取消收藏")
    else:
        st.session_state.favorites.insert(0, key)
        st.toast("已加入收藏")


def word_count_text(book: dict) -> str:
    raw = safe_text(book.get("word_count"))
    if not raw:
        return ""
    try:
        value = float(raw)
    except ValueError:
        return raw
    if value >= 10000:
        return f"{value / 10000:.1f}万字"
    return f"{int(value)}字"


def meta_line(book: dict) -> str:
    parts = [safe_text(book.get("author")), safe_text(book.get("status")), word_count_text(book)]
    heat = safe_text(book.get("heat"))
    if heat:
        parts.append(f"热度 {heat}")
    return " | ".join([item for item in parts if item])


def render_chips(tags: list[str]) -> None:
    if not tags:
        return
    html = "".join(f'<span class="chip">{tag}</span>' for tag in tags[:8])
    st.markdown(f'<div class="chips">{html}</div>', unsafe_allow_html=True)


def render_book_card(book: dict, key_prefix: str, expanded: bool = False) -> None:
    with st.container():
        st.markdown('<div class="book-card">', unsafe_allow_html=True)
        left, right = st.columns([0.78, 0.22], vertical_alignment="top")
        with left:
            st.markdown(
                f"""
                <div class="author">{meta_line(book)}</div>
                <div class="book-title">《{safe_text(book.get("title"))}》</div>
                """,
                unsafe_allow_html=True,
            )
        with right:
            label = "♥ 已收藏" if is_fav(book) else "♡ 收藏"
            if st.button(label, key=f"{key_prefix}_fav_{book_key(book)}"):
                toggle_fav(book)
                st.rerun()

        st.markdown(f'<div class="hook">{safe_text(book.get("hook"))}</div>', unsafe_allow_html=True)
        summary = safe_text(book.get("summary"))
        if summary:
            st.markdown(f'<div class="summary">{summary}</div>', unsafe_allow_html=True)
        render_chips(book.get("tags", []))

        if safe_text(book.get("intro")):
            with st.expander("展开简介", expanded=expanded):
                st.write(book.get("intro"))

        link = safe_text(book.get("link"))
        if link:
            st.link_button("去原站阅读 ↗", link)
        st.markdown("</div>", unsafe_allow_html=True)


def score_book(book: dict, query: str) -> int:
    query = safe_text(query)
    if not query:
        return 0
    words = [word for word in re.split(r"[\s，、/|;；]+", query) if word]
    text = " ".join(
        [
            safe_text(book.get("title")),
            safe_text(book.get("author")),
            safe_text(book.get("hook")),
            safe_text(book.get("summary")),
            safe_text(book.get("intro")),
            " ".join(book.get("tags", [])),
        ]
    )
    score = 0
    for word in words:
        if word in text:
            score += 3
    for tag in book.get("tags", []):
        if tag and tag in query:
            score += 5
    return score


def recommend(query: str, limit: int = 8) -> list[dict]:
    if not BOOKS:
        return []
    ranked = sorted(((score_book(book, query), book) for book in BOOKS), key=lambda item: item[0], reverse=True)
    hits = [book for score, book in ranked if score > 0]
    if hits:
        return hits[:limit]
    return random.sample(BOOKS, min(limit, len(BOOKS)))


def secret_value(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return safe_text(value or os.getenv(name, default))


def deepseek_reply(user_text: str) -> tuple[str, list[dict]]:
    candidates = recommend(user_text, 6)
    api_key = secret_value("DEEPSEEK_API_KEY")
    if not api_key:
        return local_chat_reply(user_text, candidates)

    book_context = json.dumps(
        [
            {
                "title": item.get("title"),
                "author": item.get("author"),
                "tags": item.get("tags", []),
                "hook": item.get("hook"),
                "summary": item.get("summary"),
            }
            for item in candidates
        ],
        ensure_ascii=False,
    )
    payload = {
        "model": secret_value("DEEPSEEK_MODEL", "deepseek-chat"),
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是长期混晋江 BL 圈的 AI 找文搭子。回复像真实读者，不像客服。"
                    "先理解用户想看的关系感、题材、人设和避雷点。"
                    "可以自然追问，也可以基于候选书推荐 1-2 本。不要编造候选列表外的书。"
                ),
            },
            {"role": "user", "content": f"用户说：{user_text}\n候选书库：{book_context}"},
        ],
        "temperature": 0.75,
        "max_tokens": 520,
    }
    request = urllib.request.Request(
        secret_value("DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions"),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            data = json.loads(response.read().decode("utf-8"))
        text = safe_text(data["choices"][0]["message"]["content"])
        return text or "我先帮你捞了几本，看看有没有贴近那个感觉。", candidates[:2]
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, TimeoutError, json.JSONDecodeError) as exc:
        st.warning(f"DeepSeek 暂时没接通，先用本地规则推荐：{exc}")
        return local_chat_reply(user_text, candidates)


def local_chat_reply(user_text: str, candidates: list[dict]) -> tuple[str, list[dict]]:
    if "酸" in user_text or "虐" in user_text:
        reply = "你要的更像有拉扯、有后劲，但不是把人虐到喘不过气。我先按这个方向捞。"
    elif "疯" in user_text or "无限" in user_text:
        reply = "懂，你要的不是乱疯，是那种高压关系里越看越上头的张力。"
    elif "刑" in user_text or "案" in user_text or "破" in user_text:
        reply = "那我会更偏剧情线站得住、CP 张力跟着案子一起走的文。"
    else:
        reply = "我先理解成你想要关系感明确、读起来抓人的文。你也可以再补一句题材或避雷。"
    return reply, candidates[:2]


def home_page() -> None:
    st.markdown('<div class="eyebrow">AI BL 搜文助手</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-title">今晚想看点什么？</div>', unsafe_allow_html=True)
    st.markdown('<div class="muted">说出你想看的氛围、人设和避雷点。</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        query = st.text_input(
            "搜索",
            placeholder="想看攻后面越来越爱老婆的 / 最近想看酸涩一点",
            label_visibility="collapsed",
            key="home_query",
        )
        if st.button("开始找文", type="primary"):
            st.session_state.home_results = recommend(query, 8)
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    st.subheader("不知道搜什么？")
    prompts = ["刑警 破案 强强", "酸涩一点但别太虐", "无限流 疯批美人受", "古代 破案 慢热"]
    cols = st.columns(4)
    for col, prompt in zip(cols, prompts):
        if col.button(prompt):
            st.session_state.home_query = prompt
            st.session_state.home_results = recommend(prompt, 8)
            st.rerun()

    results = st.session_state.get("home_results", [])
    if results:
        st.divider()
        st.subheader("你可能会喜欢")
        for i, book in enumerate(results):
            render_book_card(book, f"home_{i}")


def square_page() -> None:
    st.markdown('<div class="eyebrow">广场发现</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-title">逛逛大家会心动的文</div>', unsafe_allow_html=True)
    mode = st.segmented_control("排序", ["最新", "最热", "收藏最多"], default="最新")
    query = st.text_input("广场搜索", placeholder="搜索书名、作者、口味标签...", label_visibility="collapsed")
    books = recommend(query, 20) if query else BOOKS[:20]
    if mode == "最热":
        books = sorted(books, key=lambda item: safe_text(item.get("heat")), reverse=True)
    elif mode == "收藏最多":
        books = sorted(books, key=lambda item: int(is_fav(item)), reverse=True)

    for row_start in range(0, min(len(books), 12), 3):
        cols = st.columns(3)
        for col, book in zip(cols, books[row_start : row_start + 3]):
            with col:
                st.markdown(
                    f"""
                    <div class="feed-card">
                        <div class="feed-hook">{safe_text(book.get("hook"))}</div>
                        <b>《{safe_text(book.get("title"))}》</b><br>
                        <span class="muted">{safe_text(book.get("author"))}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("展开", key=f"square_open_{book_key(book)}"):
                    st.session_state.square_open = book_key(book)
        st.write("")

    open_key = st.session_state.get("square_open")
    if open_key:
        book = next((item for item in BOOKS if book_key(item) == open_key), None)
        if book:
            st.divider()
            render_book_card(book, "square_detail", expanded=True)


def chat_page() -> None:
    st.markdown('<div class="eyebrow">AI 找文搭子</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-title">不知道想看什么？先聊聊。</div>', unsafe_allow_html=True)
    st.markdown('<div class="chat-box">', unsafe_allow_html=True)
    for idx, message in enumerate(st.session_state.chat_messages):
        st.markdown(f'<div class="bubble {message["role"]}">{message["text"]}</div>', unsafe_allow_html=True)
        for j, book in enumerate(message.get("items", [])):
            render_book_card(book, f"chat_{idx}_{j}")
    st.markdown("</div>", unsafe_allow_html=True)

    user_text = st.chat_input("想看那种嘴硬但越来越爱老婆的攻 / 最近文荒了救救")
    if user_text:
        st.session_state.chat_messages.append({"role": "user", "text": user_text, "items": []})
        with st.spinner("搭子正在翻书架..."):
            reply, items = deepseek_reply(user_text)
        st.session_state.chat_messages.append({"role": "assistant", "text": reply, "items": items})
        st.rerun()


def wheel_page() -> None:
    st.markdown('<div class="eyebrow">找文求签</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-title">今天适合看哪一本？</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="lot">
            <div class="lot-title">今日签文</div>
            <div class="lot-main">点击求签</div>
            <div class="muted">抽一本适合现在心情的文。</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("求签", type="primary"):
        st.session_state.last_lot = random.choice(BOOKS) if BOOKS else None
        st.rerun()

    if st.session_state.last_lot:
        st.divider()
        render_book_card(st.session_state.last_lot, "wheel")


def profile_page() -> None:
    st.markdown('<div class="eyebrow">我的</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-title">我的收藏</div>', unsafe_allow_html=True)
    st.markdown('<div class="muted">那些让你心动过的文。</div>', unsafe_allow_html=True)
    favorites = [book for key in st.session_state.favorites for book in BOOKS if book_key(book) == key]
    if not favorites:
        st.markdown('<div class="empty">还没有收藏的文。<br>遇到喜欢的文时，记得点一下小书签。</div>', unsafe_allow_html=True)
        return
    for i, book in enumerate(favorites):
        render_book_card(book, f"profile_{i}")


def main() -> None:
    inject_style()
    init_state()
    page = st.radio("导航", ["首页", "广场", "搭子", "求签", "我的"], horizontal=True, label_visibility="collapsed")
    if not BOOKS:
        st.error("没有找到小说数据库，请确认 pythonProject/novels_with_ai_fields.xlsx 已上传到仓库。")
        return
    if page == "首页":
        home_page()
    elif page == "广场":
        square_page()
    elif page == "搭子":
        chat_page()
    elif page == "求签":
        wheel_page()
    else:
        profile_page()


if __name__ == "__main__":
    main()
