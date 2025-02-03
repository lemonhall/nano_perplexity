from openai import OpenAI
import os

def get_relevance_scores(query, context_block):
    """
    使用 SiliconFlow API 根据查询语句计算文章列表的相关度分值，并返回相关度大于 8.0 的条目。

    :param query: 查询语句 (主题语句)
    :param context_block: 文章列表内容
    :return: 模型返回的相关度分值和排序后的文章列表
    """
    # 获取环境变量中的 SILICONFLOW API 密钥
    SILICONFLOW_API_KEY = os.getenv('SILICONFLOW_API_KEY')

    if not SILICONFLOW_API_KEY:
        raise ValueError("SILICONFLOW API key is not set. Please set the SILICONFLOW_API_KEY environment variable.")

    # 初始化 OpenAI 客户端
    client = OpenAI(api_key=SILICONFLOW_API_KEY, base_url="https://api.siliconflow.cn/v1")

    # 定义系统提示
    system_prompt = '''
    我将会给你一个列表和一个问询的主题语句作为输入，列表是关于某个主题的一系列文章的“[编号](原文链接): 内容摘要”;
    你需要给我输出该列表当中每一篇摘要的相关度分值(0-10分,分值可以为小数，比如9.8，保留一位小数)，并进行再排序

    其中输入如以下形式：
    [1](https://m.thepaper.cn/newsDetail_forward_30075139): 总台记者获悉，当地时间2月2日，美国总统特朗普表示，他3日将与加拿大 、墨西哥就关税问题进行谈话。特朗普还称，计划很快对欧盟产品征收关税。 据悉，特朗普称其将在2月3日上午与加拿大总理特鲁多交谈。
    [2](https://www.dw.com/zh/特朗普要加征关税-中国政府或进退两难/a-71433009): 分析人士警告称，美国总统特朗普提高关税可能会加速人民币贬值，这将使中国政府推动经济复苏的努力变得更加复杂。 （德国之声中文网）上周开始第二个总统任期的特朗普宣布，最早从2月1日起对所有中国商品加征10%的关税，同时表示愿意就此进行谈判。 如果加征关税，可能会加剧人民币的疲软。有经济学家表示，今年人民币兑美元的汇率可能会跌至自中国取消固定汇率制度二十年来的最低水平。 

    经过你处理后的示例输出为，其中(score:7.5)为相关度：
    [1](score:7.5)(https://m.thepaper.cn/newsDetail_forward_30075139): 总台记者获悉，当地时间2月2日，美国总统特朗普表示，他3日将与加拿大 、墨西哥就关税问题进行谈话。特朗普还称，计划很快对欧盟产品征收关税。 据悉，特朗普称其将在2月3日上午与加拿大总理特鲁多交谈。
    [2](score:6.5)(https://www.dw.com/zh/特朗普要加征关税-中国政府或进退两难/a-71433009): 分析人士警告称，美国总统特朗普提高关税可能会加速人民币贬值，这将使中国政府推动经济复苏的努力变得更加复杂。 

    接受输入后，仅回复结果，无需回复任何评价等其余话语，并且仅回复摘要内容与主体内容相关度大于8.0的条目
    '''

    # 构造输入模板
    input_template = '''
    //问询的主题语句如下
    {query}

    //列表如下
    {context_block}
    '''

    # 将查询语句和列表替换到模板中
    input_content = input_template.format(query=query, context_block=context_block)

    # 调用 OpenAI API
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": input_content,
                }
            ],
            model="deepseek-ai/DeepSeek-V3",
            stream=False,
        )

        # 提取模型返回的内容
        res = response.choices[0].message.content
        return res

    except Exception as e:
        # 捕获异常并返回错误信息
        return f"Error: {e}"