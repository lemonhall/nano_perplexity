from openai import OpenAI
import os

#这个程序是一个例子程序，用来给v3一个输入并得到重排序后的输出



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
#
# 然后在linux下，可以写入.bashrc下面去
# 但是在生产环境部署的时候，用supervior的时候，可以卸载配置文件里，这个可以问豆包具体的语法
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key is not set. Please set the OPENAI_API_KEY environment variable.")


client = OpenAI(api_key=OPENAI_API_KEY,base_url="https://api.deepseek.com")


system_prompt = '''
我将会给你一个列表和一个问询的主题语句作为输入，列表是关于某个主题的一系列文章的摘要，以及它们的原文链接;
你需要给我输出该列表当中每一篇摘要的相关度分值(0-10分,分值可以为小数，比如9.8，保留一位)，并进行再排序，
并使用JSON输出结果。

其中列表当中的item项目的示例输入为：
{
    "title": "英伟达市值一夜大涨16%，跻身全球第四，为什么？_澎湃号·湃客_澎湃新闻-The Paper",
    "url": "https://www.thepaper.cn/newsDetail_forward_26444909",
    "content": "2月22日英伟达刚刚公布了截至今年 1 月 28 日的 2024 财年第四季度财报。在财报公布前一天，英伟达股价下跌 4.35%，出现今年年内最大单日跌幅；财报公布当天，股价再跌 2.85%。 但英伟达近乎满分的答卷一夜之间填满了投资者的信心。",
    "raw_content": null
}

经过你处理后的示例输出为：
{
    "title": "英伟达市值一夜大涨16%，跻身全球第四，为什么？_澎湃号·湃客_澎湃新闻-The Paper",
    "url": "https://www.thepaper.cn/newsDetail_forward_26444909",
    "content": "2月22日英伟达刚刚公布了截至今年 1 月 28 日的 2024 财年第四季度财报。在财报公布前一天，英伟达股价下跌 4.35%，出现今年年内最大单日跌幅；财报公布当天，股价再跌 2.85%。 但英伟达近乎满分的答卷一夜之间填满了投资者的信心。",
    "score":"5.2"
    "raw_content": null
}

接受输入后，仅回复结果的JSON，无需回复任何评价等其余话语，方便我进行程序化解析
'''

input = '''
//问询的主题语句
英伟达从2020年起，股价为何一路攀升到这个程度？

//列表
{
    "title": "英伟达的崛起：Ai创新与未来【Ai知识库】 - 腾讯网",
    "url": "https://news.qq.com/rain/a/20240618A0A8K100",
    "content": "点击蓝字 关注我们前言近年来，英伟达的股价显著增长，这在很大程度上反映了市场对算力需求的不断增加。自2020年起，英伟达的股价从每股不到",
    "raw_content": null
},
{
    "title": "英伟达 为何股价坚挺，一直不断在创新高？大规模回购已在路上？英伟达股票市值最近几年，一直在不断的创新高。已经成为全球股票... - 雪球",
    "url": "https://xueqiu.com/1221265530/313879710",
    "content": "英伟达 为何股价坚挺，一直不断在创新高？大规模回购已在路上？ ... 高盛表示，预计该公司\"股票回购将逐步增加\"，到2026年累计达到1810亿美元。 ... 根据媒体统计的数据，在英伟达公布财报后，华尔街对英伟达的平均目标价从发布前的每股150美元跃升至每股",
    "raw_content": null
},
{
    "title": "为什么英伟达成了这世界上最厉害的股票？ - 36氪",
    "url": "https://www.36kr.com/p/2660820859396868",
    "content": "之所以英伟达股价能如此强力，很大程度上源于每次都能带来的惊喜：作为当今世界上最能赚钱的商业机器，过去四个季度中，英伟达每次营收公布",
    "raw_content": null
},
{
    "title": "股价不到一年飙升190%后，凭什么相信英伟达还能涨？ 众所周知， 英伟达 股价如坐上火箭，一飞冲天，有人肯定开始在想：飙升的股价究竟是基于公司 ...",
    "url": "https://xueqiu.com/4894511814/312258382",
    "content": "众所周知， 英伟达 股价如坐上火箭，一飞冲天，有人肯定开始在想：飙升的股价究竟是基于公司的真实基本面，还是「非理性繁荣」？ 英伟达 的股价确实出乎所有人意料，市值从2023年11月的1.11万亿美元，到一年后的3.65万亿美元，翻了三倍多。截至撰稿时，英伟达已经成为全球市值最高的公司，甚",
    "raw_content": null
},
{
    "title": "英伟达市值一夜大涨16%，跻身全球第四，为什么？_澎湃号·湃客_澎湃新闻-The Paper",
    "url": "https://www.thepaper.cn/newsDetail_forward_26444909",
    "content": "2月22日英伟达刚刚公布了截至今年 1 月 28 日的 2024 财年第四季度财报。在财报公布前一天，英伟达股价下跌 4.35%，出现今年年内最大单日跌幅；财报公布当天，股价再跌 2.85%。 但英伟达近乎满分的答卷一夜之间填满了投资者的信心。",
    "raw_content": null
}
'''


response  = client.chat.completions.create(
    messages=[
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": input,
        }
    ],
    model="deepseek-chat",
    stream=False,
)

print(response.choices[0].message.content)