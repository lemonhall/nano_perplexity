import os
import re
import sys
import time
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

from googlesearch import search
import requests
from bs4 import BeautifulSoup
import backoff
import openai

# Default configuration and Prompts
NUM_SEARCH = 50  # Number of links to parse from Google
SEARCH_TIME_LIMIT = 6  # Max seconds to request website sources before skipping to the next URL
TOTAL_TIMEOUT = 8  # Overall timeout for all operations
MAX_CONTENT = 500  # Number of words to add to LLM context for each search result

# 这里我修改了最大TOKENS值为默认的4K，它最大能到8K，但意义不大，官方文档其实也建议就4K即可
MAX_TOKENS = 4096  # Maximum number of tokens LLM generates
# 这里我修改成了'deepseek-reasoner'，默认模型的回复里其实有一个字段叫做
# reasoner，这是openai库最新更新了的东西，但其实对于调用来说，除非你想看<think></think>
# 标签里的东西，否则其实一行代码都不需要去改动
LLM_MODEL = 'deepseek-reasoner'  # 'gpt-3.5-turbo' #'gpt-4o'


cited_answer_prompt = """
Provide a relevant, informative response to the user's query using the given context (search results with [citation number](website link) and brief descriptions).

- Answer directly without referring the user to any external links.
- Use an unbiased, journalistic tone and avoid repeating text.
- Format your response in markdown with bullet points for clarity.
- Cite all information using [citation number](website link) notation, matching each part of your answer to its source.

Context Block:
{context_block}

User Query:
{query}
"""


def trace_function_factory(start):
    """Create a trace function to timeout request"""

    def trace_function(frame, event, arg):
        if time.time() - start > TOTAL_TIMEOUT:
            raise TimeoutError('Website fetching timed out')
        return trace_function

    return trace_function


def fetch_webpage(url, timeout):
    """Fetch the content of a webpage given a URL and a timeout."""
    start = time.time()
    sys.settrace(trace_function_factory(start))
    try:
        print(f"Fetching link: {url}")
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        paragraphs = soup.find_all('p')
        page_text = ' '.join([para.get_text() for para in paragraphs])
        return url, page_text
    except (requests.exceptions.RequestException, TimeoutError) as e:
        print(f"Error fetching {url}: {e}")
    finally:
        sys.settrace(None)
    return url, None


def parse_google_results(query, num_search=NUM_SEARCH, search_time_limit=SEARCH_TIME_LIMIT):
    """Perform a Google search and parse the content of the top results."""
    urls = search(query, num_results=num_search)
    print("parse_google_results返回的urls是什么？：")
    print("解析出的URL列表：")
    #是一个<generator object search at 0x000001AD117ED9A0>
    #然后这个东西就真的只是一堆url的列表而已，因为迭代器只能被遍历一次，那就算了，不打印了
    print("======================================")
    max_workers = os.cpu_count() or 1  # Fallback to 1 if os.cpu_count() returns None
    print("max_workers的值：",max_workers)
    print("======================================")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(fetch_webpage, url, search_time_limit): url for url in urls}
        return {url: page_text for future in as_completed(future_to_url) if (url := future.result()[0]) and (
                page_text := future.result()[1])}


# 这里我加入了, encoding='utf-8'，解决了原版的markdown文件输出乱码的问题
def save_markdown(content, file_path):
    with open(file_path, 'a', encoding='utf-8') as file:
        file.write(content)


@backoff.on_exception(backoff.expo, (openai.RateLimitError, openai.APITimeoutError))
def llm_check_search(query, file_path, msg_history=None, llm_model=LLM_MODEL):
    """Check if query requires search and execute Google search."""
    cleaned_response = "特朗普 关税"
    print(f"Performing Google search: {cleaned_response}")
    search_dic = parse_google_results(cleaned_response)
    # Format search result in dic into markdown format
    search_result_md = "\n".join([f"{number + 1}. {link}" for number, link in enumerate(search_dic.keys())])
    save_markdown(f"## Sources\n{search_result_md}\n\n", file_path)
    return search_dic

#原来的函数
@backoff.on_exception(backoff.expo, (openai.RateLimitError, openai.APITimeoutError))
def llm_answer(query, file_path, msg_history=None, search_dic=None, llm_model=LLM_MODEL, max_content=MAX_CONTENT,
               max_tokens=MAX_TOKENS, debug=False):
    """Build the prompt for the language model including the search results context."""
    if search_dic:
        context_block = "\n".join(
            [f"[{i + 1}]({url}): {content[:max_content]}" for i, (url, content) in enumerate(search_dic.items())])
        prompt = cited_answer_prompt.format(context_block=context_block, query=query)


if __name__ == "__main__":
    query = None
    file_path = "playground.md"
    msg_history = None
    max_content=MAX_CONTENT

    search_dic = llm_check_search(query, file_path, msg_history)
    context_block = "\n".join(
            [f"[{i + 1}]({url}): {content[:max_content]}" for i, (url, content) in enumerate(search_dic.items())])
    print("======================================")
    print("打印context_block如下：")
    print(context_block)
    print("======================================")
    prompt = cited_answer_prompt.format(context_block=context_block, query=query)
    print(prompt)