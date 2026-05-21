# -*- coding: utf-8 -*-
import re
import time
import random
import argparse
import requests
import pandas as pd
from bs4 import BeautifulSoup

BASE_URL = "https://www.jjwxc.net/fenzhan/noyq/"
OUTPUT_FILE = "novels.xlsx"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.jjwxc.net/",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

COLUMNS = [
    "title",
    "author",
    "platform",
    "category_path",
    "pov",
    "is_finished",
    "word_count",
    "platform_tags",
    "main_characters",
    "one_line_hook",
    "original_intro",
    "link",
    "platform_score",
    "heat_level",
]


# ======================
# 基础函数
# ======================

def sleep_random(a=3, b=6, msg=""):
    sec = random.uniform(a, b)
    print(f"等待 {sec:.1f}s：{msg}")
    time.sleep(sec)


def fetch_html(url):
    sleep_random(2, 5, "请求前停顿")
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.encoding = "gb18030"
    return resp.text


def clean_num(text):
    digits = re.sub(r"[^\d]", "", str(text or ""))
    return int(digits) if digits else ""


def heat_level(score):
    if not score:
        return ""
    if score >= 1_000_000_000:
        return "S"
    if score >= 300_000_000:
        return "A"
    if score >= 50_000_000:
        return "B"
    return "C"


def find_field(text, field):
    pattern = rf"{field}[：:\s]*([\s\S]*?)(?=\n(?:文章类型|作品视角|文章进度|全文字数|内容标签|主角|配角|一句话简介|立意|简介|作者|所属系列|收藏此文章|文章积分)|$)"
    m = re.search(pattern, text)
    return m.group(1).strip() if m else ""


# ======================
# 修复：标题 / 作者 / 字数
# ======================

def clean_title(raw):
    title = str(raw or "").strip()

    title = title.replace("_晋江文学城", "")
    title = title.replace("-晋江文学城", "")
    title = title.replace("晋江文学城", "")

    title = re.sub(r"作者[:：].*$", "", title).strip()
    title = title.strip("《》 　\t\r\n")

    return title


def extract_title(soup):
    h1 = soup.find("h1")
    if h1:
        txt = h1.get_text(strip=True)
        val = clean_title(txt)
        if val:
            return val

    if soup.title:
        txt = soup.title.get_text(strip=True)
        val = clean_title(txt)
        if val:
            return val

    return ""


def clean_author(raw):
    author = str(raw or "").strip()
    author = re.sub(r"作者[：:]", "", author).strip()
    author = author.replace("作者专栏", "").strip()
    author = re.split(r"[\s　]+", author)[0].strip()
    return author


def extract_author(soup, text):
    all_text = soup.get_text("\n", strip=True)

    m = re.search(r"作者[：:]\s*([^\n\s　]+)", all_text)
    if m:
        val = clean_author(m.group(1))
        if val:
            return val

    val = clean_author(find_field(text, "作者"))

    bad_words = ["收藏", "专栏", "积分", "书评", "营养液"]
    if any(w in val for w in bad_words):
        return ""

    return val


def extract_word_count(text):
    """
    专门抓全文字数，避免串数字
    例如：
    全文字数：559118字
    """
    m = re.search(r"全文字数[：:\s]*([0-9,，]+)\s*字", text)
    if m:
        return clean_num(m.group(1))
    return ""


# ======================
# 内容标签 / 主角 / 简介
# ======================

def extract_platform_tags_from_html(html):
    m = re.search(
        r"内容标签[：:\s]*([\s\S]*?)(?:主角[：:]|一句话简介[：:]|立意[：:]|简介[：:])",
        html
    )

    if not m:
        return find_field(
            BeautifulSoup(html, "html.parser").get_text("\n", strip=True),
            "内容标签"
        )

    block = m.group(1)
    soup = BeautifulSoup(block, "html.parser")

    tags = []
    for a in soup.find_all("a"):
        txt = a.get_text(strip=True)
        if txt and txt not in tags:
            tags.append(txt)

    return " ".join(tags)


def extract_main_characters_from_html(html, text):
    patterns = [
        r"主角[：:]\s*([\s\S]*?)(?:┃|配角[：:]|一句话简介[：:]|立意[：:]|简介[：:]|<br\s*/?>)",
        r"主角[：:]\s*([\s\S]*?)(?:配角|一句话简介|立意|简介)",
    ]

    for p in patterns:
        m = re.search(p, html)
        if m:
            val = BeautifulSoup(m.group(1), "html.parser").get_text(" ", strip=True)
            val = re.sub(r"\s+", " ", val).strip(" ：:┃")
            if val:
                return val

    return ""


def extract_original_intro_from_html(soup, text):
    intro = soup.find(id="novelintro")
    if intro:
        val = intro.get_text("\n", strip=True)
        val = re.sub(r"\n{3,}", "\n\n", val)
        return val.strip()

    pattern = (
        r"(?<!一句话)简介[：:\s]*([\s\S]*?)"
        r"(?=\n(?:立意|文章积分|非v章节章均点击数|总书评数|当前被收藏数|营养液数|章节列表|到最新章)|$)"
    )
    m = re.search(pattern, text)
    return m.group(1).strip() if m else ""


# ======================
# 积分
# ======================

def parse_score(raw):
    digits = re.sub(r"[^\d]", "", str(raw or ""))
    return int(digits) if digits else None


def extract_platform_score(html):
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "textarea", "noscript"]):
        tag.decompose()

    visible_text = soup.get_text("\n", strip=True)

    m = re.search(
        r"文章积分[：:\s]*([0-9]{1,3}(?:[,，][0-9]{3})+|[0-9]{5,})",
        visible_text
    )
    if m:
        val = parse_score(m.group(1))
        if val:
            return val

    return ""


# ======================
# 主体解析
# ======================

def parse_detail(url):
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "textarea", "noscript"]):
        tag.decompose()

    text = soup.get_text("\n", strip=True)

    title = extract_title(soup)
    author = extract_author(soup, text)

    category_path = find_field(text, "文章类型")
    pov = find_field(text, "作品视角")
    is_finished = find_field(text, "文章进度")
    word_count = extract_word_count(text)

    platform_tags = extract_platform_tags_from_html(html)
    main_characters = extract_main_characters_from_html(html, text)
    original_intro = extract_original_intro_from_html(soup, text)

    one_line_hook = find_field(text, "一句话简介")
    platform_score = extract_platform_score(html)

    row = {
        "title": title,
        "author": author,
        "platform": "晋江文学城",
        "category_path": category_path,
        "pov": pov,
        "is_finished": is_finished,
        "word_count": word_count,
        "platform_tags": platform_tags,
        "main_characters": main_characters,
        "one_line_hook": one_line_hook,
        "original_intro": original_intro,
        "link": url,
        "platform_score": platform_score,
        "heat_level": heat_level(platform_score),
    }

    print(
        f"成功：{title} / {author}；"
        f"字数={word_count}；"
        f"标签={platform_tags}；"
        f"主角={main_characters}；"
        f"积分={platform_score}"
    )

    sleep_random(3, 5, "详情页后停顿")
    return row


def get_links():
    html = fetch_html(BASE_URL)
    ids = re.findall(r"onebook\.php\?novelid=(\d+)", html)
    ids = list(dict.fromkeys(ids))

    return [
        f"https://www.jjwxc.net/onebook.php?novelid={i}"
        for i in ids
    ]


# ======================
# 主程序
# ======================

def main(max_count):
    links = get_links()

    rows = []
    success = 0

    for link in links:
        if success >= max_count:
            break

        print(f"\n[{success + 1}/{max_count}] {link}")

        try:
            row = parse_detail(link)
            rows.append(row)
            success += 1
        except Exception as e:
            print("失败：", e)

    df = pd.DataFrame(rows, columns=COLUMNS)
    df.to_excel(OUTPUT_FILE, index=False, engine="openpyxl")

    print(f"\n已导出 {OUTPUT_FILE}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=1000)
    args = parser.parse_args()

    main(args.max)