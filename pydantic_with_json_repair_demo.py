#uv add json-repair
#uv add pydantic
from pydantic import BaseModel, field_validator, RootModel
from typing import List, Optional

import json_repair

json_string = '''
```json
[
    {
        "title": "英伟达的崛起：Ai创新与未来【Ai知识库】 - 腾讯网",
        "url": "https://news.qq.com/rain/a/20240618A0A8K100",
        "content": "点击蓝字 关注我们前言近年来，英伟达的股价显著增长，这在很大程度上反映了市场对算力需求的不断增加。自2020年起，英伟达的股价从每股不到",
        "score": "9.5",
        "raw_content": null
    },
    {
        "title": "英伟达 为何股价坚挺，一直不断在创新高？大规模回购已在路上？英伟达股票市值最近几年，一直在不断的创新高。已经成为全球股票... - 雪球",
        "url": "https://xueqiu.com/1221265530/313879710",
        "content": "英伟达 为何股价坚挺，一直不断在创新高？大规模回购已在路上？ ... 高盛表示，预计该公司\"股票回购将逐步增 加\"，到2026年累计达到1810亿美元。 ... 根据媒体统计的数据，在英伟达公布财报后，华尔街对英伟达的平均目标价从发布前的每股150 美元跃升至每股",
        "score": "8.7",
        "raw_content": null
    },
    {
        "title": "为什么英伟达成了这世界上最厉害的股票？ - 36氪",
        "url": "https://www.36kr.com/p/2660820859396868",
        "content": "之所以英伟达股价能如此强力，很大程度上源于每次都能带来的惊喜：作为当今世界上最能赚钱的商业机器，过去四 个季度中，英伟达每次营收公布",
        "score": "8.2",
        "raw_content": null
    },
    {
        "title": "股价不到一年飙升190%后，凭什么相信英伟达还能涨？ 众所周知， 英伟达 股价如坐上火箭，一飞冲天，有人肯定开始在想：飙升的股价究竟是基于公司 ...",
        "url": "https://xueqiu.com/4894511814/312258382",
        "content": "众所周知， 英伟达 股价如坐上火箭，一飞冲天，有人肯定开始在想：飙升的股价究竟是基于公司的真实基本面，还 是「非理性繁荣」？ 英伟达 的股价确实出乎所有人意料，市值从2023年11月的1.11万亿美元，到一年后的3.65万亿美元，翻了三倍多。截 至撰稿时，英伟达已经成为全球市值最高的公司，甚",
        "score": "7.8",
        "raw_content": null
    },
    },
    {
        "title": "英伟达市值一夜大涨16%，跻身全球第四，为什么？_澎湃号·湃客_澎湃新闻-The Paper",
        "url": "https://www.thepaper.cn/newsDetail_forward_26444909",
        "content": "2月22日英伟达刚刚公布了截至今年 1 月 28 日的 2024 财年第四季度财报。在财报公布前一天，英伟达股价下跌 4.35%，出现今年年内最大单日跌幅；财报公布当天，股价再跌 2.85%。 但英伟达近乎满分的答卷一夜之间填满了投资者的信心。",
        "score": "6.5",
        "raw_content": null
    }
]
```
'''

decoded_object = json_repair.loads(json_string)

print(decoded_object)


# 定义新闻条目的 Pydantic 模型
class NewsItem(BaseModel):
    title: str
    url: str
    content: str
    score: float
    raw_content: Optional[str] = None

    @field_validator('score', mode='before')
    def convert_score_to_float(cls, value):
        return float(value)

# 定义包含多个新闻条目的列表模型
NewsList = RootModel[List[NewsItem]]

try:
    # 扁平化嵌套列表
    flattened_data = []
    for item in decoded_object:
        if isinstance(item, list):
            flattened_data.extend(item)
        else:
            flattened_data.append(item)

    print(flattened_data)
    print("-" * 50)

    # 使用 Pydantic 模型进行验证和处理
    news_list = NewsList(flattened_data)

    for news in news_list.root:  # 注意这里使用 .root 访问实际的列表:
        print(f"标题: {news.title}")
        print(f"链接: {news.url}")
        print(f"内容: {news.content}")
        print(f"得分: {news.score}")
        print("-" * 50)
except ValueError as e:
    print(f"数据验证失败: {e}")