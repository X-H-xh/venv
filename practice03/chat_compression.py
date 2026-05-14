import os
import json
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

MAX_TURNS = 5
MAX_TOKENS = 3000
TOKEN_ESTIMATE_RATIO = 4

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

def estimate_tokens(text):
    return len(text) // TOKEN_ESTIMATE_RATIO

def estimate_messages_tokens(messages):
    total = 0
    for msg in messages:
        content = msg.get('content', '')
        if isinstance(content, str):
            total += estimate_tokens(content)
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'text':
                    total += estimate_tokens(item.get('text', ''))
    return total

def count_turns(messages):
    turns = 0
    for msg in messages:
        if msg['role'] == 'user':
            turns += 1
    return turns

def should_summarize(messages):
    if count_turns(messages) > MAX_TURNS:
        return True
    if estimate_messages_tokens(messages) > MAX_TOKENS:
        return True
    return False

def split_messages_for_summary(messages, preserve_ratio=0.3):
    total_msgs = len(messages)
    preserve_count = max(1, int(total_msgs * preserve_ratio))
    summarize_count = total_msgs - preserve_count
    
    return messages[:summarize_count], messages[summarize_count:]

def summarize_conversation(api_base, model, api_key, messages_to_summarize):
    url = f"{api_base.rstrip('/')}/chat/completions"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    conversation_text = "\n".join([
        f"{msg['role']}: {msg.get('content', '')}" 
        for msg in messages_to_summarize 
        if msg.get('content') and isinstance(msg.get('content'), str)
    ])
    
    summary_prompt = f"""请将以下对话历史进行压缩总结，保留关键信息和要点，删除冗余内容。

对话历史：
{conversation_text}

请生成一个简洁的摘要，包含：
1. 对话的主要话题和目的
2. 关键信息和结论
3. 未解决的问题或后续行动

摘要格式：
[对话摘要] 主要话题：... 关键信息：... 未解决问题：... [/对话摘要]"""

    payload = {
        'model': model,
        'messages': [
            {"role": "user", "content": summary_prompt}
        ],
        'temperature': 0.3,
        'max_tokens': 500
    }
    
    req = Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
    with urlopen(req, timeout=60) as response:
        result = json.loads(response.read().decode('utf-8'))
        summary = result['choices'][0]['message']['content']
        usage = result.get('usage', {})
        return summary, usage.get('total_tokens', 0)

def compress_conversation(api_base, model, api_key, messages):
    if not should_summarize(messages):
        return messages, "No compression needed"
    
    old_turns = count_turns(messages)
    old_tokens = estimate_messages_tokens(messages)
    
    summarize_msgs, preserve_msgs = split_messages_for_summary(messages, preserve_ratio=0.3)
    
    print(f"\n{'='*60}")
    print(f"聊天记录压缩触发")
    print(f"{'='*60}")
    print(f"当前轮数: {old_turns} (阈值: {MAX_TURNS})")
    print(f"估算Token数: {old_tokens} (阈值: {MAX_TOKENS})")
    print(f"需要压缩的消息数: {len(summarize_msgs)}")
    print(f"保留原文的消息数: {len(preserve_msgs)}")
    print(f"压缩比例: 前70%压缩，保留后30%原文")
    print(f"{'='*60}")
    
    summary, summary_tokens = summarize_conversation(api_base, model, api_key, summarize_msgs)
    
    print(f"摘要生成完成，消耗Token: {summary_tokens}")
    print(f"摘要内容: {summary}")
    print(f"{'='*60}")
    
    new_messages = [
        {"role": "system", "content": messages[0]['content'] if messages and messages[0]['role'] == 'system' else ""},
        {"role": "user", "content": f"[之前的对话已压缩为摘要]\n{summary}\n[/摘要]"},
        {"role": "assistant", "content": "[已理解摘要内容]"}
    ]
    
    for msg in preserve_msgs:
        new_messages.append(msg)
    
    new_turns = count_turns(new_messages)
    new_tokens = estimate_messages_tokens(new_messages)
    
    print(f"压缩后轮数: {new_turns}")
    print(f"压缩后估算Token数: {new_tokens}")
    print(f"Token减少: {old_tokens - new_tokens} (减少 {((old_tokens - new_tokens) / old_tokens * 100):.1f}%)")
    print(f"{'='*60}\n")
    
    return new_messages, f"Compressed from {old_tokens} to {new_tokens} tokens"

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

    print(f"\n{'='*60}")
    print(f"聊天压缩演示程序")
    print(f"触发条件: 超过{MAX_TURNS}轮对话 或 上下文超过{MAX_TOKENS}Token")
    print(f"压缩策略: 前70%内容压缩，最后30%保留原文")
    print(f"{'='*60}")
    print(f"当前轮数: 0")
    print(f"{'='*60}\n")

    while True:
        user_input = input("你: ")
        if user_input.lower() in ['exit', 'quit', '退出']:
            print(" goodbye!")
            break
        
        messages.append({"role": "user", "content": user_input})
        
        current_turns = count_turns(messages)
        current_tokens = estimate_messages_tokens(messages)
        
        print(f"\n>>> 发送消息前检查...")
        print(f">>> 当前轮数: {current_turns}, 估算Token: {current_tokens}")
        
        if should_summarize(messages):
            messages, status = compress_conversation(api_base, model, api_key, messages)
            print(f">>> {status}")
        
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
        print(f"当前对话轮数: {count_turns(messages)}")
        print(f"当前估算Token: {estimate_messages_tokens(messages)}")
        print(f"--- ---------- ---\n")

if __name__ == '__main__':
    main()
