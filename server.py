from __future__ import annotations

import json
import os
import random
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "pythonProject" / "novels_with_ai_fields.xlsx"
if not DATA_FILE.exists():
    DATA_FILE = ROOT / "novels_with_ai_fields.xlsx"


FALLBACK_BOOKS = [
    {
        "id": "po-yun",
        "title": "破云",
        "author": "淮上",
        "tags": ["刑侦", "强强", "美强惨", "悬疑", "正剧"],
        "color": "red",
        "short": "破\n云",
        "hook": "刑侦线和双强对峙一起往前推，关系感不是硬凑出来的。",
        "oneLine": "现代都市刑侦悬疑，圆满结局",
        "summary": "现代刑侦悬疑文，痞帅刑警严峫×美强惨高智商江停。旧案追查、彼此试探和双向奔赴一起推进。",
        "intro": "城市天空，诡云奔涌。三年前恭州市的缉毒行动中，因总指挥江停判断失误，现场发生连环爆炸。",
        "progress": 154,
    },
    {
        "id": "tun-hai",
        "title": "破云2吞海",
        "author": "淮上",
        "tags": ["刑侦", "救赎", "强强", "悬疑"],
        "color": "dark",
        "short": "吞\n海",
        "hook": "冷淡和隐忍不是卖惨，重点是伤口被一点点看见。",
        "oneLine": "那些窥探藏在浪潮之下",
        "summary": "刑侦悬疑续作，冷静学院派刑警×深渊归来的受。案件推进密，人物关系带着克制和救赎感。",
        "intro": "那些窥探的触角隐藏在互联网浪潮中，无处不在，生生不息。",
        "progress": 88,
    },
    {
        "id": "mengyan",
        "title": "欢迎进入梦魇直播间",
        "author": "桑沃",
        "tags": ["无限流", "疯批", "直播", "高能"],
        "color": "blue",
        "short": "梦\n魇",
        "hook": "副本压力会把人物关系逼出来，紧张感和感情线能一起走。",
        "oneLine": "欢迎来到梦魇直播间",
        "summary": "无限流直播副本，主角在高压规则里不断拆局。节奏快、反转密，适合想看刺激和上头感的人。",
        "intro": "温简言是一名欺诈师，某天被迫成为梦魇直播间的新人主播。",
        "progress": 211,
    },
    {
        "id": "zhengjing",
        "title": "我这儿是正经店",
        "author": "忘却的悠",
        "tags": ["萌宠", "甜文", "日常", "异能"],
        "color": "green",
        "short": "正\n经",
        "hook": "日常互动比较软，甜点藏在相处细节里，适合想放松的时候看。",
        "oneLine": "这里真的是正经店",
        "summary": "现代异能甜文，温柔店主受×神秘兽医攻。萌宠日常托住感情线，治愈轻松。",
        "intro": "一家规矩和其他地方不太一样的店，迎来一位能听懂小动物说话的店主。",
        "progress": 42,
    },
]


def safe_text(value) -> str:
    if value is None:
        return ""
    text = str(value)
    if text.lower() == "nan":
        return ""
    return text.strip()


def split_tags(value: str) -> list[str]:
    for sep in ["，", "、", "/", "|", ";", "；"]:
        value = value.replace(sep, " ")
    return [item for item in value.split() if item]


def color_for(index: int) -> str:
    return ["red", "dark", "blue", "green"][index % 4]


def short_title(title: str) -> str:
    clean = title.replace("《", "").replace("》", "")
    return "\n".join(clean[:2]) if clean else "书\n页"


def load_books() -> list[dict]:
    if not DATA_FILE.exists():
        return FALLBACK_BOOKS
    try:
        import pandas as pd

        frame = pd.read_excel(DATA_FILE).fillna("")
    except Exception:
        return FALLBACK_BOOKS

    books = []
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
        hook = safe_text(row.get("social_hook") or row.get("hook_line"))
        summary = safe_text(row.get("summary_display") or row.get("summary_core"))
        books.append(
            {
                "id": safe_text(row.get("link")) or f"book-{idx}",
                "title": title,
                "author": safe_text(row.get("author") or row.get("作者")),
                "tags": tags[:8],
                "color": color_for(idx),
                "short": short_title(title),
                "hook": hook or f"《{title}》的口味很明确，可以先看简介判断合不合拍。",
                "oneLine": safe_text(row.get("one_line_hook") or row.get("一句话简介") or hook),
                "summary": summary or "暂无智能摘要。",
                "intro": safe_text(row.get("original_intro") or row.get("简介")),
                "progress": random.randint(24, 260),
                "link": safe_text(row.get("link")),
            }
        )
    return books or FALLBACK_BOOKS


BOOKS = load_books()

DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")


def score_book(book: dict, query: str) -> int:
    words = [word for word in query.replace("，", " ").replace("、", " ").split() if word]
    text = " ".join(
        [
            safe_text(book.get("title")),
            safe_text(book.get("author")),
            " ".join(book.get("tags", [])),
            safe_text(book.get("hook")),
            safe_text(book.get("summary")),
            safe_text(book.get("intro")),
        ]
    )
    return sum(3 for word in words if word in text)


def recommend(query: str) -> list[dict]:
    query = safe_text(query)
    if not query:
        return BOOKS[:8]
    ranked = [(score_book(book, query), book) for book in BOOKS]
    hits = [book for score, book in sorted(ranked, key=lambda item: item[0], reverse=True) if score > 0]
    return hits[:8] or BOOKS[:4]


def chat_reply(text: str) -> dict:
    query = text
    if "酸" in text or "虐" in text:
        query = "酸涩 拉扯 校园"
        reply = "你要的更像有拉扯、有后劲，但不是把人虐到喘不过气。我先按这个方向捞。"
    elif "疯" in text or "无限" in text:
        query = "无限流 疯批"
        reply = "这个方向我懂，重点不是乱疯，而是高压环境里人物关系被逼出来。"
    elif "刑" in text or "案" in text or "破" in text:
        query = "刑侦 破案 强强"
        reply = "你应该会更吃剧情线有分量、感情张力跟着案件一起走的类型。"
    else:
        reply = "我先理解成：你想要关系感明确、读起来有抓力的文。你也可以再补一句题材。"
    return {"reply": reply, "items": recommend(query)[:2]}


def deepseek_chat_reply(text: str) -> dict | None:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return None

    candidates = recommend(text)[:6]
    book_context = json.dumps(
        [
            {
                "title": book.get("title"),
                "author": book.get("author"),
                "tags": book.get("tags", []),
                "hook": book.get("hook"),
                "summary": book.get("summary"),
            }
            for book in candidates
        ],
        ensure_ascii=False,
    )
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是一个长期混晋江 BL 圈的搜文搭子。"
                    "回复要像真实读者聊天：懂梗、有分寸、不营销、不客服。"
                    "你需要先理解用户的模糊需求，再自然追问或给出推荐理由。"
                    "不要编造书库外的书名。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"用户想找：{text}\n\n"
                    f"当前可用候选书库：{book_context}\n\n"
                    "请用 80 字以内回复。若需求还模糊，先追问 1 个关键问题；"
                    "若候选书明显匹配，可以点出最合适的一本和理由。"
                ),
            },
        ],
        "temperature": 0.8,
        "max_tokens": 220,
    }
    request = urllib.request.Request(
        DEEPSEEK_API_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None

    reply = safe_text(data.get("choices", [{}])[0].get("message", {}).get("content"))
    if not reply:
        return None
    return {"reply": reply, "items": candidates[:2]}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def read_json(self) -> dict:
        length = int(self.headers.get("content-length", 0))
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def send_json(self, payload: dict | list):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            self.send_json({"ok": True, "books": len(BOOKS)})
            return
        if path == "/api/books":
            self.send_json({"items": BOOKS})
            return
        if path == "/api/wheel":
            self.send_json(random.choice(BOOKS))
            return
        super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        data = self.read_json()
        if path == "/api/recommend":
            self.send_json({"items": recommend(unquote(safe_text(data.get("query"))))})
            return
        if path == "/api/chat":
            text = safe_text(data.get("text"))
            self.send_json(deepseek_chat_reply(text) or chat_reply(text))
            return
        self.send_error(404)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8620"))
    host = os.getenv("HOST", "0.0.0.0" if os.getenv("PORT") else "127.0.0.1")
    print(f"智能搜文助手已启动：http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
