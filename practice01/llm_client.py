import os
import json
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from http.client import HTTPConnection, HTTPSConnection

ENV_PATH = '../.env'
DEFAULT_TIMEOUT = 30
API_ENDPOINT = '/chat/completions'

def load_env(env_path):
    if not os.path.exists(env_path):
        raise FileNotFoundError(f"配置文件不存在: {env_path}")
    
    config = {}
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            config[key.strip()] = value.strip()
    
    required_params = ['LLM_BASE_URL', 'LLM_MODEL', 'LLM_API_KEY']
    for param in required_params:
        if param not in config:
            raise ValueError(f"缺少必需参数: {param}")
    
    return config

def call_llm(config, prompt):
    base_url = config['LLM_BASE_URL']
    full_url = base_url.rstrip('/') + API_ENDPOINT
    
    if full_url.startswith('https://'):
        host = full_url.replace('https://', '').split('/')[0]
        path = '/' + '/'.join(full_url.replace('https://', '').split('/')[1:])
        conn = HTTPSConnection(host, timeout=DEFAULT_TIMEOUT)
    else:
        host = full_url.replace('http://', '').split('/')[0]
        path = '/' + '/'.join(full_url.replace('http://', '').split('/')[1:])
        conn = HTTPConnection(host, timeout=DEFAULT_TIMEOUT)
    
    request_body = {
        "model": config['LLM_MODEL'],
        "messages": [{"role": "user", "content": prompt}]
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {config['LLM_API_KEY']}"
    }
    
    start_time = time.time()
    
    conn.request('POST', path, body=json.dumps(request_body).encode('utf-8'), headers=headers)
    response = conn.getresponse()
    
    status_code = response.status
    response_body = response.read().decode('utf-8')
    
    if status_code != 200:
        raise HTTPError(f"API请求失败: {status_code}", status_code, '', headers, None)
    
    response_data = json.loads(response_body)
    elapsed_time = time.time() - start_time
    
    return (response_data, elapsed_time)

def calculate_stats(response_data, elapsed_time):
    model = response_data.get('model', '')
    usage = response_data.get('usage', {})
    prompt_tokens = usage.get('prompt_tokens', 0)
    completion_tokens = usage.get('completion_tokens', 0)
    total_tokens = usage.get('total_tokens', 0)
    
    if elapsed_time > 0:
        tokens_per_second = total_tokens / elapsed_time
    else:
        tokens_per_second = 0.0
    
    stats = {
        'model': model,
        'prompt_tokens': prompt_tokens,
        'completion_tokens': completion_tokens,
        'total_tokens': total_tokens,
        'elapsed_time': elapsed_time,
        'tokens_per_second': tokens_per_second
    }
    
    return stats

def print_results(stats, response_text):
    print("=" * 40)
    print("LLM API 调用统计")
    print("=" * 40)
    print(f"模型: {stats['model']}")
    print(f"提示词 Token: {stats['prompt_tokens']}")
    print(f"生成 Token: {stats['completion_tokens']}")
    print(f"总 Token: {stats['total_tokens']}")
    print(f"响应时间: {stats['elapsed_time']:.2f}s")
    print(f"处理速度: {stats['tokens_per_second']:.2f} token/s")
    print("=" * 40)
    print("响应内容:")
    print(response_text)

def main():
    try:
        config = load_env(ENV_PATH)
        
        prompt = input("请输入您的问题: ")
        
        response_data, elapsed_time = call_llm(config, prompt)
        
        stats = calculate_stats(response_data, elapsed_time)
        
        response_text = response_data['choices'][0]['message']['content']
        
        print_results(stats, response_text)
    
    except FileNotFoundError as e:
        print(f"错误: {e}. 请先复制 env.example 为 .env 并填写配置")
    
    except ValueError as e:
        print(f"配置错误: {e}")
    
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == '__main__':
    main()
