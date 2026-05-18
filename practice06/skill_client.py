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
        print(f"Warning: Skills directory not found: {SKILLS_DIR}")
        return skills
    
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
                    print(f"Error reading skill {skill_dir}: {e}")
    
    return skills

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

    skills = list_available_skills()
    skills_json = json.dumps({"skills": skills}, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"技能管理系统")
    print(f"{'='*60}")
    print(f"发现 {len(skills)} 个可用技能:")
    for skill in skills:
        print(f"  - {skill['name']}: {skill['description']}")
    print(f"{'='*60}\n")

    system_prompt = f"""
你是一个具备技能调用能力的AI助手。你可以使用以下可用技能：

{skills_json}

当用户的请求需要使用特定技能时，请按照以下格式调用：
<skill>技能名称</skill>

系统会自动加载该技能的详细说明并发送给你。

如果你认为不需要使用任何技能，可以直接回答用户。
"""

    messages = [
        {"role": "system", "content": system_prompt.strip()}
    ]

    while True:
        user_input = input("你: ")
        if user_input.lower() in ['exit', 'quit', '退出']:
            print(" goodbye!")
            break

        messages.append({"role": "user", "content": user_input})

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
        print(f"--- ---------- ---\n")

        if '<skill>' in assistant_content and '</skill>' in assistant_content:
            start_tag = assistant_content.find('<skill>') + 7
            end_tag = assistant_content.find('</skill>')
            skill_name = assistant_content[start_tag:end_tag].strip()
            
            print(f"\n{'='*60}")
            print(f"检测到技能调用: {skill_name}")
            print(f"{'='*60}")
            
            skill_content = load_skill_content(skill_name)
            print(f"技能内容已加载，长度: {len(skill_content)} 字符")
            
            skill_system_prompt = f"""
以下是你需要遵照执行的技能详细说明：

{skill_content}

请根据以上技能说明，处理用户的请求。
"""
            
            messages.append({"role": "system", "content": skill_system_prompt.strip()})
            
            print("技能已加载，继续对话...")
            print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
