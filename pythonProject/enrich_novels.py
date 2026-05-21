#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import time
import pandas as pd
from openai import OpenAI


def load_dotenv():
    """读取项目根目录或当前目录下的 .env，方便 PyCharm 直接运行。"""
    candidates = [
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.path.dirname(__file__), ".env"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
    ]
    for path in candidates:
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_dotenv()

# =========================
# 基础配置
# =========================

INPUT_FILE = "novels.xlsx"
OUTPUT_FILE = "novels_with_ai_fields.xlsx"

MODEL_NAME = "deepseek-v4-flash"

client = None


def get_client():
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError(
            "没有找到 DEEPSEEK_API_KEY。\n"
            "推荐做法：在 /Users/eiyo/Documents/Codex/2026-05-08/gpt/.env 新增一行：\n"
            'DEEPSEEK_API_KEY="你的 API Key"\n'
            "或者在 PyCharm 的 Run Configuration 里添加环境变量 DEEPSEEK_API_KEY。"
        )
    return OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# =========================
# 工具函数
# =========================

def safe_get(row, col):
    value = row.get(col, "")
    if pd.isna(value):
        return ""
    return str(value).strip()


def extract_json(text):
    if not text:
        raise ValueError("模型输出为空")

    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(f"未找到合法 JSON：{text}")

    return json.loads(text[start:end + 1])


def ensure_columns(df):
    target_cols = [
        "summary_core",
        "hook_line",
        "summary_display",
        "character_tags",
        "plot_points"
    ]

    for col in target_cols:
        if col not in df.columns:
            df[col] = ""

    return df


# =========================
# Prompt
# =========================

SYSTEM_PROMPT = """
你是一个长期混迹晋江BL圈的资深读者，同时也是推荐系统的数据标注助手。
你的任务是根据小说信息，输出稳定、适合批量生产的 JSON 字段，用于BL网文推荐系统。

严格规则：
1. 只输出合法 JSON
2. 不要 markdown
3. 不要解释
4. 不要闲聊
5. 所有字段必须返回
6. 无法判断时返回空字符串或空数组
"""


def build_user_prompt(row):
    title = safe_get(row, "title")
    category_path = safe_get(row, "category_path")
    platform_tags = safe_get(row, "platform_tags")
    main_characters = safe_get(row, "main_characters")
    one_line_hook = safe_get(row, "one_line_hook")
    original_intro = safe_get(row, "original_intro")[:1800]

    return f"""
你是一个长期混迹晋江BL圈的资深读者，同时也是推荐系统的数据标注助手。

你的任务是根据小说原始信息，为 BL 网文推荐产品生成适合批量生产的结构化内容字段。

你的输出将用于：

1. 搜索匹配（summary_core）
2. 推荐卡片点击率（hook_line）
3. 用户快速决策（summary_display）
4. 标签召回与相关推荐（character_tags / plot_points）

━━━━━━━━━━━━━━
【输入信息】

标题：{title}
类型：{category_path}
标签：{platform_tags}
主角：{main_characters}
一句话简介：{one_line_hook}
简介：{original_intro}

━━━━━━━━━━━━━━
【信息理解优先级（非常重要）】

生成内容时，请优先依据以下字段理解作品语义：

第一优先级（权重最高）
1. 标签（platform_tags）
2. 简介（original_intro）
3. 一句话简介（one_line_hook）
4. 类型（category_path）

第二优先级（辅助参考）
5. 主角名（main_characters）
6. 标题（title）

严格要求：

- 优先根据“标签 + 简介 + 一句话简介 + 类型”判断题材、感情线、剧情线、攻受关系。
- 不要仅凭标题猜测内容。
- 如果标题与简介冲突，以简介和标签为准。
- 如果一句话简介是情绪表达，也要结合简介判断真实内容。
- 不可编造原文不存在的设定。

例如：

标题叫《失控》
不能直接猜强制爱。

若标签是：
校园、甜文、成长

则应理解为校园成长甜文。

━━━━━━━━━━━━━━
【输出格式（严格 JSON）】

{{
  "summary_core": "",
  "hook_line": "",
  "summary_display": "",
  "character_tags": [],
  "plot_points": []
}}

━━━━━━━━━━━━━━
① summary_core（给系统检索）

用途：
搜索召回、推荐匹配、数据库摘要。

要求：

- 客观概括作品类型 + 核心卖点 + 阅读体验
- 信息密度高
- 不复述具体剧情
- 不写口语化表达
- 35~60字
- 像机器可理解摘要

示例：

无限流爽文，高智商主角闯关升级，副本烧脑刺激，成长线明显，节奏紧凑。

仙侠正剧，前世今生羁绊交织，感情线浓烈，剧情完整，后劲强。

━━━━━━━━━━━━━━
② hook_line（给用户点击）

用途：
推荐卡片第一眼吸引点击。

本质：
抓住最上头的感情张力 / 关系反差 / 情绪爽点。

要求：

- 一句话
- 12~28字最佳
- 像小红书真人推文标题
- 有记忆点
- 不解释背景
- 不写成简介
- 不要模板感
- 可略带情绪，但自然

优先抓这些点：

1. 高位者沦陷
2. 嘴硬追妻
3. 死对头变情人
4. 极致拉扯
5. 强强互钓
6. 久别重逢
7. 宿命感
8. 受拿捏攻
9. 攻爱惨了嘴还硬
10. 全员替身但他是真爱（仅原文有此设定）

示例：

高岭之花攻，被老婆迷得神魂颠倒
他嘴上说不爱，背地里追妻追疯了
死对头打着打着亲到一起了
等了十三年的人，回来却不记得他了
攻高高在上，被受迷得七荤八素

━━━━━━━━━━━━━━
③ summary_display（给用户决策）

用途：
用户点进推荐卡片后，快速判断要不要看。

必须解决的问题：

- 这是什么类型文？
- 攻受什么感觉？
- 感情线爽不爽？
- 剧情线值不值得看？
- 是甜是虐是拉扯？

输出结构：

【类型定位】+
【攻受人设】+
【感情线体验】+
【剧情线体验】+
【读者评价收尾】

要求：

- 40~70字
- 有网感但克制
- 像资深读者推荐
- 不发疯
- 不使用“绝了、笑死、谁懂、狠狠、冲”
- 信息清晰，帮助决策

示例：

现代追妻文，嘴硬深情攻×清醒受，拉扯感强，追妻线又爽又憋屈，越看越上头。

无限流爽文，疯批美人受×非人神明攻，感情线带感，副本高能烧脑，停不下来。

古耽权谋，强势帝王攻×隐忍谋士受，宿命感拉满，剧情扎实，后劲很足。

━━━━━━━━━━━━━━
【攻受表达升级规则】

普通描述若吸引力不足，可升级为圈层高共鸣表达，但必须真实成立。

攻：

高冷深情攻 → 禁欲深情攻
成熟可靠攻 → 爹系苏感攻
强势控制攻 → 控制欲攻
嘴硬心软攻 → 傲娇攻
刑警攻 → 痞帅刑警攻
温柔守护攻 → 白月光攻

受：

聪明病弱受 → 美强惨受
清冷聪明受 → 清冷美人受
活泼治愈受 → 小太阳受
张扬受 → 钓系美人受
疯批受 → 疯批美人受
坚韧成长受 → 成长系受

━━━━━━━━━━━━━━
④ character_tags

用途：
角色召回、口味匹配。

要求：

- 2~4个
- 每个≤8字
- 稳定可复用
- 写人设，不写剧情

示例：

["美强惨受","爹系攻","疯批受","钓系受"]

━━━━━━━━━━━━━━
⑤ plot_points

用途：
题材召回、相关推荐。

要求：

- 3~5个
- 每个≤8字
- 高搜索价值
- 不写完整句子

示例：

["无限流","破镜重圆","重生","娱乐圈","校园"]

━━━━━━━━━━━━━━
【标签精度规则】

只有满足至少2项，才可作为核心标签：

1. 长期推动主线
2. 占比高
3. 用户感知明显
4. 是卖点
5. 去掉后体验明显变化

否则降级为辅助描述。

例如：

有查案 ≠ 悬疑文
写：旧案追查

有朝堂 ≠ 权谋文
写：朝堂线

有虐点 ≠ 虐文
写：刀糖并存

━━━━━━━━━━━━━━
【严格规则】

1. 只输出 JSON
2. 不要 markdown
3. 不要解释
4. 不要闲聊
5. 所有字段必须返回
6. 无法判断时返回空字符串或空数组
7. 不编造剧情
8. 不只根据标题猜测内容
9. 优先依据 标签 / 简介 / 一句话简介 / 类型 生成内容
"""


# =========================
# 调用 DeepSeek
# =========================

def call_deepseek(row):
    response = get_client().chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(row)}
        ],
        stream=False,
        temperature=0.3
    )

    return response.choices[0].message.content


# =========================
# 主程序
# =========================

def main():
    print(f"读取文件：{INPUT_FILE}")

    df = pd.read_excel(INPUT_FILE)
    df = ensure_columns(df)

    total = len(df)
    print(f"共读取到 {total} 本小说")

    for idx, row in df.iterrows():
        title = safe_get(row, "title")

        if safe_get(row, "summary_core"):
            print(f"跳过第 {idx + 1}/{total} 行：{title}，已生成")
            continue

        print(f"\n正在处理第 {idx + 1}/{total} 行：{title}")

        try:
            raw_result = call_deepseek(row)
            data = extract_json(raw_result)

            df.at[idx, "summary_core"] = data.get("summary_core", "")
            df.at[idx, "hook_line"] = data.get("hook_line", "")
            df.at[idx, "summary_display"] = data.get("summary_display", "")
            df.at[idx, "character_tags"] = ";".join(data.get("character_tags", []))
            df.at[idx, "plot_points"] = ";".join(data.get("plot_points", []))

            print("生成成功")
            print("hook_line：", data.get("hook_line", ""))
            print("summary_display：", data.get("summary_display", ""))

        except Exception as e:
            print(f"第 {idx + 1} 行失败：{title}")
            print("错误：", e)

        df.to_excel(OUTPUT_FILE, index=False)
        time.sleep(1)

    print(f"\n全部完成，结果已保存到：{OUTPUT_FILE}")


if __name__ == "__main__":
    main()
