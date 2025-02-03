import os
from tavily import TavilyClient

def search_and_format(keyword):
    """
    使用 TavilyClient 搜索关键词，并将结果格式化为指定格式。

    :param keyword: 搜索关键词
    :return: 格式化后的字符串
    """
    # 获取 TAVILY_API_KEY 环境变量
    TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
    if not TAVILY_API_KEY:
        raise ValueError("TAVILY_API_KEY 环境变量未设置")

    # 初始化 TavilyClient
    tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

    # 执行搜索
    response = tavily_client.search(keyword)

    # 格式化数据
    def generate_formatted_data(data):
        """
        将输入的数据列表转换为指定格式：
        [编号](链接): 内容摘要

        :param data: 输入的数据列表，每个元素是一个字典
        :return: 格式化后的字符串
        """
        formatted_data = []
        for index, item in enumerate(data, start=1):
            url = item['url']
            content = item['content'].strip()  # 使用原文本内容
            formatted_data.append(f"[{index}]({url}): {content}\n")
        return ''.join(formatted_data)  # 将列表拼接为一个字符串

    # 返回格式化后的结果
    return generate_formatted_data(response["results"])


# 如果直接运行此脚本，则使用默认的测试关键词
if __name__ == "__main__":
    test_keyword = "大S去世了么？"
    result = search_and_format(test_keyword)
    print(result)