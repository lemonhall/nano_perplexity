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
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from ranker_by_deepseek_v3_pure_string_function import get_relevance_scores
from tavily_search_and_format import search_and_format

app = FastAPI()

# 获取脚本所在的目录
base_dir = os.path.dirname(os.path.abspath(__file__))
# 构建静态文件目录的绝对路径
static_dir = os.path.join(base_dir, 'static')

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Default configuration and Prompts
NUM_SEARCH = 10  # Number of links to parse from Google
SEARCH_TIME_LIMIT = 6  # Max seconds to request website sources before skipping to the next URL
TOTAL_TIMEOUT = 8  # Overall timeout for all operations
MAX_CONTENT = 500  # Number of words to add to LLM context for each search result

# 这里我修改了最大TOKENS值为默认的4K，它最大能到8K，但意义不大，官方文档其实也建议就4K即可
MAX_TOKENS = 4096  # Maximum number of tokens LLM generates
# 这里我修改成了'deepseek-reasoner'，默认模型的回复里其实有一个字段叫做
# reasoner，这是openai库最新更新了的东西，但其实对于调用来说，除非你想看<think></think>
# 标签里的东西，否则其实一行代码都不需要去改动
LLM_MODEL = 'deepseek-ai/DeepSeek-V3'  # 'gpt-3.5-turbo' #'gpt-4o'

system_prompt_search = """You are a helpful assistant whose primary goal is to decide if a user's query requires a Google search."""
search_prompt = """
当前是2025年，再觉得是否需要搜索时，要判断你的知识库内的知识是否过时了，如果过时了，则可以积极的启用Google 搜索；
Decide if a user's query requires a Google search. You should use Google search for most queries to find the most accurate and updated information. Follow these conditions:

- If the query does not require Google search, you must output "ns", short for no search.
- If the query requires Google search, you must respond with a reformulated user query for Google search.
- User query may sometimes refer to previous messages. Make sure your Google search considers the entire message history.

User Query:
{query}
"""

system_prompt_answer = """You are a helpful assistant who is expert at answering user's queries"""
answer_prompt = """Generate a response that is informative and relevant to the user's query
User Query:
{query}
"""

system_prompt_cited_answer = """You are a helpful assistant who is expert at answering user's queries based on the cited context."""
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

# 获取环境变量中的 SILICONFLOW API 密钥
SILICONFLOW_API_KEY = os.getenv('SILICONFLOW_API_KEY')

if not SILICONFLOW_API_KEY:
    raise ValueError("SILICONFLOW API key is not set. Please set the SILICONFLOW_API_KEY environment variable.")

client = openai.OpenAI(api_key=SILICONFLOW_API_KEY, base_url="https://api.siliconflow.cn/v1")


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
    # urls = search(query, num_results=num_search)
    # max_workers = os.cpu_count() or 1  # Fallback to 1 if os.cpu_count() returns None
    # with ThreadPoolExecutor(max_workers=max_workers) as executor:
    #     future_to_url = {executor.submit(fetch_webpage, url, search_time_limit): url for url in urls}
    #     return {url: page_text for future in as_completed(future_to_url) if (url := future.result()[0]) and (
    #             page_text := future.result()[1])}
    result = search_and_format(query)
    return result


# 这里我加入了, encoding='utf-8'，解决了原版的markdown文件输出乱码的问题
def save_markdown(content, file_path):
    with open(file_path, 'a', encoding='utf-8') as file:
        file.write(content)


@backoff.on_exception(backoff.expo, (openai.RateLimitError, openai.APITimeoutError))
def llm_check_search(query, file_path, msg_history=None, llm_model=LLM_MODEL):
    """Check if query requires search and execute Google search."""
    prompt = search_prompt.format(query=query)
    msg_history = msg_history or []
    new_msg_history = msg_history + [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model=llm_model,
        messages=[{"role": "system", "content": system_prompt_search}, *new_msg_history],
        max_tokens=30
    ).choices[0].message.content

    # check if the response contains "ns"
    cleaned_response = response.lower().strip()
    if re.fullmatch(r"\bns\b", cleaned_response):
        print("No Google search required.")
        return None
    else:
        print(f"Performing Google search: {cleaned_response}")
        search_dic = parse_google_results(query)
        # Format search result in dic into markdown format
        search_result_md = "\n".join([f"{number + 1}. {link}" for number, link in enumerate(search_dic.keys())])
        save_markdown(f"## Sources\n{search_result_md}\n\n", file_path)
        return search_dic


@backoff.on_exception(backoff.expo, (openai.RateLimitError, openai.APITimeoutError))
def llm_answer(query, file_path, msg_history=None, search_dic=None, llm_model=LLM_MODEL, max_content=MAX_CONTENT,
               max_tokens=MAX_TOKENS, debug=False):
    """Build the prompt for the language model including the search results context."""
    if search_dic:
        context_block = "\n".join(
            [f"[{i + 1}]({url}): {content[:max_content]}" for i, (url, content) in enumerate(search_dic.items())])
        prompt = cited_answer_prompt.format(context_block=context_block, query=query)
        system_prompt = system_prompt_cited_answer
    else:
        prompt = answer_prompt.format(query=query)
        system_prompt = system_prompt_answer

    """Generate a response using the OpenAI language model with stream completion"""
    msg_history = msg_history or []
    new_msg_history = msg_history + [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model=llm_model,
        messages=[{"role": "system", "content": system_prompt}, *new_msg_history],
        max_tokens=max_tokens,
        stream=True
    )

    print("\n" + "*" * 20 + " LLM START " + "*" * 20)
    save_markdown(f"## Answer\n", file_path)
    content = []
    for chunk in response:
        chunk_content = chunk.choices[0].delta.content
        if chunk_content:
            content.append(chunk_content)
            print(chunk_content, end="")
            save_markdown(chunk_content, file_path)

    print("\n" + "*" * 21 + " LLM END " + "*" * 21 + "\n")
    # change the line for the next question
    save_markdown("\n\n", file_path)
    new_msg_history = new_msg_history + [{"role": "assistant", "content": ''.join(content)}]

    return new_msg_history

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

@app.post("/ask")
async def ask(query: str):
    msg_history = None
    file_path = "playground.md"
    save_path = None
    # start with an empty file
    with open(file_path, 'w') as file:
        pass

    save_markdown(f"# {query}\n\n", file_path)
    search_dic = llm_check_search(query, file_path, msg_history)
    msg_history = llm_answer(query, file_path, msg_history, search_dic)
    save_path = save_path or f"{query}.md"  # ensure saved file has the first query as its name
    print(f"AI response recorded into {file_path}")

    with open(file_path, 'r', encoding='utf-8') as file:
        response_content = file.read()

    return {"response": response_content}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8157)