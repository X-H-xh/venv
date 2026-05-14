import os
import json
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

LOG_DIR = r"D:\chat-log"
LOG_FILE = os.path.join(LOG_DIR, "log.txt")
EXTRACT_INTERVAL = 5

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

def ensure_log_dir():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

def append_to_log(content):
    ensure_log_dir()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"\n[{timestamp}]\n{content}\n")

def read_chat_log():
    ensure_log_dir()
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

def extract_5w_info(api_base, model, api_key, messages):
    url = f"{api_base.rstrip('/')}/chat/completions"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    conversation_text = "\n".join([
        f"{msg['role']}: {msg.get('content', '')}"
        for msg in messages
        if msg.get('content') and isinstance(msg.get('content'), str)
    ])
    
    extract_prompt = f"""请从以下对话中提取关键信息，按照5W规则提取：

对话内容：
{conversation_text}

请提取多条关键信息，每条包含：
- Who（谁）：执行动作的主体
- What（做了什么）：具体做了什么
- When（何时）：时间（可选）
- Where（何处）：地点（可选）
- Why（为什么）：原因（可选）

请以JSON数组格式输出，每条记录包含who, what, when, where, why字段。如果没有找到对应字段的值，写"未提及"。
只输出JSON数组，不要其他内容。"""

    payload = {
        'model': model,
        'messages': [{"role": "user", "content": extract_prompt}],
        'temperature': 0.3,
        'max_tokens': 800
    }
    
    req = Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
    with urlopen(req, timeout=60) as response:
        result = json.loads(response.read().decode('utf-8'))
        content = result['choices'][0]['message']['content']
        usage = result.get('usage', {})
        return content, usage.get('total_tokens', 0)

def parse_5w_json(json_str):
    try:
        start = json_str.find('[')
        end = json_str.rfind(']') + 1
        if start != -1 and end != 0:
            return json.loads(json_str[start:end])
    except:
        pass
    return []

def format_5w_records(records):
    formatted = []
    for i, record in enumerate(records, 1):
        line = f"记录{i}: "
        if record.get('who'):
            line += f"谁={record['who']};"
        if record.get('what'):
            line += f"做了什么={record['what']};"
        if record.get('when') and record['when'] != '未提及':
            line += f"何时={record['when']};"
        if record.get('where') and record['where'] != '未提及':
            line += f"何地={record['where']};"
        if record.get('why') and record['why'] != '未提及':
            line += f"为何={record['why']};"
        formatted.append(line)
    return "\n".join(formatted)

def should_search_history(user_input):
    user_input_lower = user_input.lower().strip()
    if user_input_lower.startswith('/search'):
        return True
    keywords = ['查找聊天历史', '搜索聊天记录', '之前聊过', '上次说过', '历史记录', '查找之前', '搜索之前']
    for keyword in keywords:
        if keyword in user_input_lower:
            return True
    return False

def search_history(api_base, model, api_key, user_query, chat_log_content):
    url = f"{api_base.rstrip('/')}/chat/completions"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    search_prompt = f"""你是一个聊天历史搜索助手。用户想要查找之前的聊天记录。

用户的搜索请求：{user_query}

以下是聊天历史记录：
{chat_log_content if chat_log_content else "（暂无聊天记录）"}

请根据用户的搜索请求，在聊天历史中查找相关信息，并给出准确的回答。
如果找到相关信息，请说明在什么时候聊过什么。
如果没有找到相关信息，请如实告知用户。"""

    payload = {
        'model': model,
        'messages': [{"role": "user", "content": search_prompt}],
        'temperature': 0.3,
        'max_tokens': 1000
    }
    
    req = Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
    with urlopen(req, timeout=60) as response:
        result = json.loads(response.read().decode('utf-8'))
        return result['choices'][0]['message']['content']

def call_llm(api_base, model, api_key, messages):
    url = f"{api_base.rstrip('/')}/chat/completions"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    payload = {
        'model': model,
        'messages': messages
    }
    
    req = Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
    with urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode('utf-8'))

def count_user_turns(messages):
    return sum(1 for msg in messages if msg['role'] == 'user')

def main():
    config = load_env()
    api_base = config.get('OPENAI_API_BASE', '')
    model = config.get('OPENAI_API_MODEL', '')
    api_key = config.get('OPENAI_API_KEY', '')

    if not all([api_base, model, api_key]):
        print('Error: Please configure .env file with OPENAI_API_BASE, OPENAI_API_MODEL, OPENAI_API_KEY')
        return

    system_prompt = """你是一个友好的AI助手。请根据用户的问题给出有帮助的回答。"""

    messages = [
        {"role": "system", "content": system_prompt.strip()}
    ]

    turn_count = 0
    
    print(f"\n{'='*60}")
    print(f"聊天历史管理程序")
    print(f"功能1: 每{EXTRACT_INTERVAL}次对话自动提取5W关键信息并存入日志")
    print(f"功能2: 使用 /search 或表达查找意图时可搜索聊天历史")
    print(f"日志文件: {LOG_FILE}")
    print(f"{'='*60}\n")

    while True:
        user_input = input("你: ")
        if user_input.lower() in ['exit', 'quit', '退出']:
            print(" goodbye!")
            break
        
        if should_search_history(user_input):
            search_query = user_input
            if search_query.startswith('/search'):
                search_query = search_query[7:].strip()
            
            print(f"\n>>> 检测到搜索请求: {search_query}")
            print(f">>> 正在搜索聊天历史...")
            
            chat_log = read_chat_log()
            search_result = search_history(api_base, model, api_key, search_query, chat_log)
            print(f"\nAI: {search_result}")
            continue
        
        messages.append({"role": "user", "content": user_input})
        turn_count += 1
        
        print(f"\n>>> 当前对话轮数: {turn_count}")
        
        if turn_count % EXTRACT_INTERVAL == 0:
            print(f"\n>>> 达到{EXTRACT_INTERVAL}轮，开始提取5W关键信息...")
            
            extracted_json, tokens_used = extract_5w_info(api_base, model, api_key, messages)
            print(f">>> 提取消耗Token: {tokens_used}")
            
            records = parse_5w_json(extracted_json)
            if records:
                formatted_records = format_5w_records(records)
                append_to_log(formatted_records)
                print(f">>> 已提取{len(records)}条记录并保存到日志")
                print(f">>> 内容预览:\n{formatted_records[:200]}...")
            else:
                print(f">>> 未能解析提取结果，保存原始内容")
                append_to_log(extracted_json)
        
        start_time = time.time()
        response = call_llm(api_base, model, api_key, messages)
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        usage = response.get('usage', {})
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        total_tokens = usage.get('total_tokens', 0)
        
        assistant_content = response['choices'][0]['message']['content']
        messages.append({"role": "assistant", "content": assistant_content})
        
        print(f"\nAI: {assistant_content}")
        print(f"\n--- 统计信息 ---")
        print(f"响应时间: {elapsed_time:.2f}秒")
        print(f"Token消耗: 输入={prompt_tokens}, 输出={completion_tokens}, 总计={total_tokens}")
        print(f"当前对话轮数: {turn_count}")
        print(f"--- ---------- ---\n")

if __name__ == '__main__':
    main()
