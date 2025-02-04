import os
import requests


#查询deepseek官方的余额

url = "https://api.deepseek.com/user/balance"

# -----------------------------------------------------------------------------
# 使用 PowerShell
# 打开 PowerShell（在 “开始” 菜单中搜索 “PowerShell” 并打开）。
# 要为当前用户设置环境变量，可以使用
# $env:OPENAI_API_KEY = "your_api_key"
# 命令。
# 同样，将"your_api_key"替换为实际的 API 密钥。不过，这种方式设置的环境变量只在当前 PowerShell 会话中有效。

# 要永久设置环境变量（对于当前用户），可以使用
# [Environment]::SetEnvironmentVariable("OPENAI_API_KEY","your_api_key","User")。
# 如果要设置系统级别的环境变量（需要管理员权限），可以将最后一个参数改为"Machine"，
# 例如
# [Environment]::SetEnvironmentVariable("OPENAI_API_KEY","your_api_key","Machine")。
# Set up OpenAI API key
# 记得使用以上方法后，需要关闭vscode后重启vscode，之后点击F5运行python脚本的时候才能生效
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


payload={}
headers = {
  'Accept': 'application/json',
  'Authorization': 'Bearer '+OPENAI_API_KEY
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)