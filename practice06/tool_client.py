import os
import json
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.agents', 'skills')

def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    config = {}
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key] = value.strip()
    return config

def parse_yaml_front_matter(content):
    if content.startswith('---'):
        end_index = content.find('---', 3)
        if end_index != -1:
            yaml_content = content[3:end_index].strip()
            data = {}
            for line in yaml_content.split('\n'):
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    data[key.strip()] = value.strip().strip('"').strip("'")
            return data, content[end_index+3:].strip()
    return None, content

def list_available_skills():
    skills = []
    
    if not os.path.isdir(SKILLS_DIR):
        return json.dumps({"error": f"Skills directory not found: {SKILLS_DIR}"}, ensure_ascii=False)
    
    for skill_dir in os.listdir(SKILLS_DIR):
        skill_path = os.path.join(SKILLS_DIR, skill_dir)
        if os.path.isdir(skill_path):
            skill_file = os.path.join(skill_path, 'SKILL.md')
            if os.path.isfile(skill_file):
                try:
                    with open(skill_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    front_matter, _ = parse_yaml_front_matter(content)
                    if front_matter and 'name' in front_matter:
                        skills.append({
                            'name': front_matter['name'],
                            'description': front_matter.get('description', '')
                        })
                except Exception as e:
                    pass
    
    return json.dumps(skills, ensure_ascii=False, indent=2)

def load_skill_content(skill_name):
    if not os.path.isdir(SKILLS_DIR):
        return f"Error: Skills directory not found: {SKILLS_DIR}"
    
    for skill_dir in os.listdir(SKILLS_DIR):
        skill_path = os.path.join(SKILLS_DIR, skill_dir)
        if os.path.isdir(skill_path):
            skill_file = os.path.join(skill_path, 'SKILL.md')
            if os.path.isfile(skill_file):
                try:
                    with open(skill_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    front_matter, body = parse_yaml_front_matter(content)
                    if front_matter and front_matter.get('name') == skill_name:
                        return body
                except Exception as e:
                    return f"Error loading skill {skill_name}: {e}"
    
    return f"Error: Skill '{skill_name}' not found"

def call_llm(api_base, model, api_key, messages):
    url = f"{api_base.rstrip('/')}/chat/completions"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "list_available_skills",
                "description": "列出所有可用的技能，返回技能名称和描述列表",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "load_skill_content",
                "description": "加载指定技能的完整内容，当需要执行某个技能时调用此函数",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "skill_name": {
                            "type": "string",
                            "description": "要加载的技能名称"
                        }
                    },
                    "required": ["skill_name"]
                }
            }
        }
    ]
    
    payload = {
        'model': model,
        'messages': messages,
        'tools': tools,
        'tool_choice': 'auto'
    }
    
    req = Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
    with urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode('utf-8'))

def execute_tool_call(tool_call):
    function_name = tool_call['function']['name']
    arguments = json.loads(tool_call['function']['arguments'])
    
    if function_name == 'list_available_skills':
        return list_available_skills()
    elif function_name == 'load_skill_content':
        return load_skill_content(arguments.get('skill_name', ''))
    else:
        return f"Error: Unknown function {function_name}"

def main():
    config = load_env()
    api_base = config.get('OPENAI_API_BASE', '')
    model = config.get('OPENAI_API_MODEL', '')
    api_key = config.get('OPENAI_API_KEY', '')

    if not all([api_base, model, api_key]):
        print('Error: Please configure .env file with OPENAI_API_BASE, OPENAI_API_MODEL, OPENAI_API_KEY')
        return

    skills = list_available_skills()
    
    print(f"\n{'='*60}")
    print(f"技能管理系统 (Tool Call版)")
    print(f"{'='*60}")
    try:
        skills_list = json.loads(skills)
        if isinstance(skills_list, list):
            print(f"发现 {len(skills_list)} 个可用技能:")
            for skill in skills_list:
                print(f"  - {skill['name']}: {skill['description']}")
        else:
            print(f"技能列表: {skills}")
    except:
        print(f"技能列表: {skills}")
    print(f"{'='*60}\n")

    system_prompt = """你是一个具备技能调用能力的AI助手。你有以下可用工具：

1. list_available_skills() - 列出所有可用的技能
2. load_skill_content(skill_name) - 加载指定技能的完整内容

当用户请求需要使用技能时，请调用相应工具获取技能信息，然后按照技能内容执行。

请根据用户的请求，决定是否需要调用工具。如果需要调用工具，请按照JSON格式输出工具调用。

当收到工具执行结果后，请根据结果继续处理用户请求。"""

    user_prompt = input("请输入你的请求: ")
    
    messages = [
        {"role": "system", "content": system_prompt.strip()},
        {"role": "user", "content": user_prompt}
    ]

    print(f"\nModel: {model}")
    print(f"API Base: {api_base}")
    print("-" * 50)
    print(f"用户请求: {user_prompt}")
    print("-" * 50)

    start_time = time.time()
    
    response = call_llm(api_base, model, api_key, messages)
    end_time = time.time()
    
    elapsed_time = end_time - start_time
    
    usage = response.get('usage', {})
    prompt_tokens = usage.get('prompt_tokens', 0)
    completion_tokens = usage.get('completion_tokens', 0)
    total_tokens = usage.get('total_tokens', 0)
    tokens_per_second = (completion_tokens / elapsed_time) if elapsed_time > 0 else 0

    print(f"LLM响应时间: {elapsed_time:.2f}秒")
    print(f"Token消耗: 输入={prompt_tokens}, 输出={completion_tokens}, 总计={total_tokens}")
    print(f"处理速度: {tokens_per_second:.2f} token/s")
    print("-" * 50)

    tool_calls = response['choices'][0]['message'].get('tool_calls', [])
    
    if tool_calls:
        for tool_call in tool_calls:
            function_name = tool_call['function']['name']
            arguments = json.loads(tool_call['function']['arguments'])
            
            print(f"工具调用: {function_name}({arguments})")
            
            tool_result = execute_tool_call(tool_call)
            
            print(f"工具执行结果:")
            print(tool_result)
            print("-" * 50)
            
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [tool_call]
            })
            messages.append({
                "role": "tool",
                "content": tool_result,
                "tool_call_id": tool_call['id']
            })

            response = call_llm(api_base, model, api_key, messages)
            final_response = response['choices'][0]['message']['content']
            print(f"最终回复: {final_response}")
    else:
        content = response['choices'][0]['message']['content']
        print(f"LLM回复: {content}")

if __name__ == '__main__':
    main()
