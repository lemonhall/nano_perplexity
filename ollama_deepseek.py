from openai import OpenAI
import os

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key is not set. Please set the OPENAI_API_KEY environment variable.")


client = OpenAI(api_key=OPENAI_API_KEY,base_url="http://localhost:11434/v1")

stream = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "你好啊",
        }
    ],
    model="deepseek-r1:latest",
    stream=True,
)
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="")