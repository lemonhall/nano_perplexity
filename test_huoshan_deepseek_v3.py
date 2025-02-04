import os
from openai import OpenAI

# -----------------------------------------------------------------------------
# 使用 PowerShell
# 打开 PowerShell（在 “开始” 菜单中搜索 “PowerShell” 并打开）。
# 要为当前用户设置环境变量，可以使用
# $env:OPENAI_API_KEY = "your_api_key"
# 命令。
# 同样，将"your_api_key"替换为实际的 API 密钥。不过，这种方式设置的环境变量只在当前 PowerShell 会话中有效。

# 要永久设置环境变量（对于当前用户），可以使用
# [Environment]::SetEnvironmentVariable("HUOSHAN_API_KEY","your_api_key","User")。
# 如果要设置系统级别的环境变量（需要管理员权限），可以将最后一个参数改为"Machine"，
# 例如
# [Environment]::SetEnvironmentVariable("HUOSHAN_API_KEY","your_api_key","Machine")。
# Set up OpenAI API key
# 记得使用以上方法后，需要关闭vscode后重启vscode，之后点击F5运行python脚本的时候才能生效
HUOSHAN_API_KEY = os.getenv('HUOSHAN_API_KEY')


if not HUOSHAN_API_KEY:
    raise ValueError("HUOSHAN API key is not set. Please set the HUOSHAN_API_KEY environment variable.")


client = OpenAI(
    api_key = HUOSHAN_API_KEY,
    base_url = "https://ark.cn-beijing.volces.com/api/v3",
)

# Non-streaming:
print("----- standard request -----")
completion = client.chat.completions.create(
    model = "ep-20250204220334-l2q5g",  # V3的模型编码
    messages = [
        {"role": "system", "content": "你是一位谦逊的 AI 人工智能助手"},
        {"role": "user", "content": "你好啊"},
    ],
)
print(completion.choices[0].message.content)

# Streaming:
print("----- streaming request -----")
stream = client.chat.completions.create(
    model = "ep-20250204220334-l2q5g",  # V3的模型编码
    messages = [
        {"role": "system", "content": "你是一位谦逊的 AI 人工智能助手"},
        {"role": "user", "content": "你好啊"},
    ],
    stream=True
)

for chunk in stream:
    if not chunk.choices:
        continue
    print(chunk.choices[0].delta.content, end="")
print()