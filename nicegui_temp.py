import os
import re
import time
import sys
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from googlesearch import search
import requests
from bs4 import BeautifulSoup
import backoff
import openai
from nicegui import ui

# -----------------------------------------------------------------------------\n
# Default configuration and Prompts
NUM_SEARCH = 10  # Number of links to parse from Google
SEARCH_TIME_LIMIT = 3  # Max seconds to request website sources before skipping to next URL
TOTAL_TIMEOUT = 6  # Overall timeout for all operations
MAX_CONTENT = 500  # Number of words to add to LLM context for each search result

MAX_TOKENS = 4096  # Maximum number of tokens LLM generates
LLM_MODEL = 'deepseek-reasoner'  # 'gpt-3.5-turb o' 'gpt-40'

system_prompt_search = """You are a helpful assistant whose primary goal is to decide if a user's query requires a Google search."""
search_prompt = """
Decide if a user's query requires a Google search. You should use Google search for most queries to find the most accurate and updated information. Follow these conditions:

- If the query does not require Google search, you must output "ns", short for no search.
- If the query requires Google search, you must respond with a reformulated user query for Google search.
- User query may sometimes refer to previous messages. Make sure your Google search considers the entire message history.

User Query:
{query}
"""

system_prompt_answer = """You are a helpful assistant who is expert at answering user's queries."""
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

# Set up OpenAI API key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key is not set. Please set the OPENAI_API_KEY environment variable.")

client = openai.OpenAI(api_key=OPENAI_API_KEY, base_url="https://api.deepseek.com")


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
    max_workers = os.cpu_count() or 1
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(fetch_webpage, url, search_time_limit): url for url in urls}
        return {url: page_text for future in as_completed(future_to_url) if (url := future.result()[0]) and (page_text := future.result()[1])}


def llm_check_search(query, msg_history=None, llm_model=LLM_MODEL):
    """Check if query requires search and execute Google search."""
    prompt = search_prompt.format(query=query)
    msg_history = msg_history or []
    new_msg_history = msg_history + [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model=llm_model,
        messages=[{"role": "system", "content": system_prompt_search}, *new_msg_history],
        max_tokens=30
    ).choices[0].message.content

    cleaned_response = response.lower().strip()
    if re.fullmatch(r"\bns\b", cleaned_response):
        return None
    else:
        return parse_google_results(cleaned_response)


def llm_answer(query, msg_history=None, search_dic=None, llm_model=LLM_MODEL, max_content=MAX_CONTENT, max_tokens=MAX_TOKENS, debug=False):
    """Build the prompt for the language model including the search results context."""
    if search_dic:
        context_block = "\n".join([f"[{i+1}]({url}): {content[:max_content]}" for i, (url, content) in enumerate(search_dic.items())])
        prompt = cited_answer_prompt.format(context_block=context_block, query=query)
        system_prompt = system_prompt_cited_answer
    else:
        prompt = answer_prompt.format(query=query)
        system_prompt = system_prompt_answer

    msg_history = msg_history or []
    new_msg_history = msg_history + [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model=llm_model,
        messages=[{"role": "system", "content": system_prompt}, *new_msg_history],
        max_tokens=max_tokens,
        stream=True
    )

    content = []
    for chunk in response:
        chunk_content = chunk.choices[0].delta.content
        if chunk_content:
            content.append(chunk_content)
    return ''.join(content)


# -----------------------------------------------------------------------------\n
# NiceGUI UI Setup
with ui.column().classes('items-center gap-3'):
    ui.label("AI Playground").style("font-size: 2em")

    # Text input for user queries
    query_input = ui.textarea(label="Enter your question here", placeholder="What's on your mind?...")

    # Textbox for displaying the response
    response_output = ui.markdown("Ask a question to get started!").classes("w-full bg-gray-100 p-4 rounded-lg")

    # Button to trigger the query processing
    async def process_query():
        query = query_input.value.strip()
        print(query)
        if not query:
            response_output.value = "Please enter a question!"
            return

        response_output.value = "Processing your query..."

        # Clear previous messages and setup history
        msg_history = []

        # Check if search is needed
        search_dic = llm_check_search(query, msg_history)
        if search_dic:
            # If search is required, display sources
            sources_md = "\n".join([f"{i+1}. [{url}]({url})" for i, url in enumerate(search_dic.keys())])
            response_output.value = f"## Sources\n{sources_md}"
        else:
            response_output.value = "No search required."

        # Generate answer
        answer = llm_answer(query, msg_history, search_dic)
        response_output.value = f"## Answer\n{answer}\n\n"

    # Add a button to process the query
    ui.button("Ask", on_click=process_query).props("color=primary rounded")

# Run the NiceGUI app
ui.run(title="AI Playground", port=8080)