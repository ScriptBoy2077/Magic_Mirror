# pip install openai

import os
import textwrap
from openai import OpenAI

from services.config import AI_API_KEY, AI_BASE_URL

def ask_ai(tmp_out, tmp_in): 
    prompt_sys = """
        # 角色
        你的专属衣物管理与搭配师。

        # 库存（仅根据以下衣物推荐）
        * 【必备】薄秋衣、薄秋裤；
        * 软壳三合一冲锋衣（含外壳+抓绒内胆）；
        * 软壳三合一冲锋裤（含外壳+抓绒内胆）；

        # 穿搭指令
        1. 场景：室内与室外切换。
        2. 组合：利用库存中的衣物，组合出一套适合当前温度的穿搭。
        3. 特别提示：请考虑通勤与室内办公的便利性。

        # 输出限制
        1. **字数**：严格 ≤ 140字。
        2. **内容**：仅包含“推荐搭配”的具体内容。
        3. **禁止行为**：严禁任何背景介绍、分析、总结、语气词。
        4. **格式**：直接列出衣物组合，不要分段，不要列表符号。

        # 响应示例（仅作参考，不要模仿语气）
        薄秋衣+薄秋裤+冲锋衣外壳+冲锋裤外壳。
    """

    prompt_user = f"室外气温{tmp_out}，室内气温{tmp_in}，请推荐适合当前温度的穿搭组合。"

    client = OpenAI(
        api_key = AI_API_KEY, 
        base_url = AI_BASE_URL
    )

    completion = client.chat.completions.create(
        model = "mimo-v2-flash", 
        messages = [
            {
                "role": "system", 
                "content": textwrap.dedent(prompt_sys)
            },
            {
                "role": "user",
                "content": prompt_user
            }
        ],
        max_completion_tokens = 1024,
        temperature = 0.3,
        top_p = 0.95,
        stream = False,
        stop = None,
        frequency_penalty = 0,
        presence_penalty = 0,
        extra_body = {
            "thinking": {"type": "disabled"}
        }
    )

    print(completion.choices[0].message.content)
    return completion.choices[0].message.content
    
    
if __name__ == "__main__":
    from get_db import get_recent_readings
    temp = get_recent_readings(1)
    tmp_out, tmp_in = 15, temp[0]['temperature']
    ask_ai(tmp_out, tmp_in)
