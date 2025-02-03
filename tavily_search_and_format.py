import os
from tavily import TavilyClient

def search_and_format(keyword):
    """
    使用 TavilyClient 搜索关键词，并将结果格式化为字典结构。

    :param keyword: 搜索关键词
    :return: 包含 URL 和对应内容的字典
    """
    # 获取 TAVILY_API_KEY 环境变量
    TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
    if not TAVILY_API_KEY:
        raise ValueError("TAVILY_API_KEY 环境变量未设置")

    # 初始化 TavilyClient
    tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

    # 执行搜索
    response = tavily_client.search(keyword)

    # 创建一个字典，存储 URL 和对应的内容
    results = {}
    for item in response["results"]:
        url = item['url']
        content = item['content'].strip()  # 使用原文本内容
        results[url] = content  # 将 URL 和内容存入字典

    return results  # 返回包含 URL 和内容的字典


# 如果直接运行此脚本，则使用默认的测试关键词
if __name__ == "__main__":
    test_keyword = "大S去世了么？"
    result = search_and_format(test_keyword)
    print(result)