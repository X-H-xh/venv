import os
import json
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    config = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key] = value.strip()
    return config

def call_llm(api_base, model, api_key, prompt):
    url = f"{api_base.rstrip('/')}/chat/completions"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    payload = {
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}]
    }
    req = Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
    with urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode('utf-8'))

def main():
    config = load_env()
    api_base = config.get('OPENAI_API_BASE', '')
    model = config.get('OPENAI_API_MODEL', '')
    api_key = config.get('OPENAI_API_KEY', '')

    if not all([api_base, model, api_key]):
        print('Error: Please configure .env file with OPENAI_API_BASE, OPENAI_API_MODEL, OPENAI_API_KEY')
        return

    prompt = "Hello, how are you? Please respond briefly."

    print(f"Model: {model}")
    print(f"API Base: {api_base}")
    print("-" * 50)

    start_time = time.time()
    response = call_llm(api_base, model, api_key, prompt)
    end_time = time.time()

    elapsed_time = end_time - start_time

    content = response['choices'][0]['message']['content']
    usage = response.get('usage', {})

    prompt_tokens = usage.get('prompt_tokens', 0)
    completion_tokens = usage.get('completion_tokens', 0)
    total_tokens = usage.get('total_tokens', 0)

    tokens_per_second = (completion_tokens / elapsed_time) if elapsed_time > 0 else 0

    print(f"Response: {content}")
    print("-" * 50)
    print(f"Prompt Tokens: {prompt_tokens}")
    print(f"Completion Tokens: {completion_tokens}")
    print(f"Total Tokens: {total_tokens}")
    print(f"Time Elapsed: {elapsed_time:.2f} seconds")
    print(f"Token/s Speed: {tokens_per_second:.2f}")

if __name__ == '__main__':
    main()
