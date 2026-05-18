import os
import json
import time
import re
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.agents', 'skills')
PRACTICE07_DIR = os.path.dirname(__file__)

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

def list_files(directory):
    result = []
    try:
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isfile(item_path):
                stat = os.stat(item_path)
                result.append({
                    'name': item,
                    'type': 'file',
                    'size': stat.st_size,
                    'mtime': time.ctime(stat.st_mtime)
                })
            elif os.path.isdir(item_path):
                result.append({
                    'name': item,
                    'type': 'directory'
                })
        return json.dumps({"success": True, "files": result}, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

def rename_file(directory, old_name, new_name):
    try:
        old_path = os.path.join(directory, old_name)
        new_path = os.path.join(directory, new_name)
        os.rename(old_path, new_path)
        return json.dumps({"success": True, "message": f"File renamed from {old_name} to {new_name}"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

def delete_file(directory, filename):
    try:
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
            return json.dumps({"success": True, "message": f"File {filename} deleted"}, ensure_ascii=False)
        elif os.path.isdir(file_path):
            os.rmdir(file_path)
            return json.dumps({"success": True, "message": f"Directory {filename} deleted"}, ensure_ascii=False)
        else:
            return json.dumps({"success": False, "error": f"File {filename} not found"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

def create_file(directory, filename, content):
    try:
        file_path = os.path.join(directory, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return json.dumps({"success": True, "message": f"File {filename} created"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

def read_file(directory, filename):
    try:
        file_path = os.path.join(directory, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return json.dumps({"success": True, "content": content}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

def fetch_url(url):
    try:
        req = Request(url)
        with urlopen(req, timeout=30) as response:
            content = response.read().decode('utf-8', errors='ignore')
            status_code = response.status
            content_type = response.headers.get('Content-Type', '')
            content_length = len(content)
            truncated = False
            if len(content) > 5000:
                content = content[:5000] + "\n...[内容已截断]"
                truncated = True
            return json.dumps({
                "success": True,
                "status_code": status_code,
                "content_type": content_type,
                "content_length": content_length,
                "content": content,
                "truncated": truncated
            }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

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

class ChainedCallContext:
    def __init__(self, max_iterations=10):
        self.steps = []
        self.variables = {}
        self.max_iterations = max_iterations
        self.current_iteration = 0
    
    def add_step(self, tool_name, arguments, result):
        self.steps.append({
            'tool_name': tool_name,
            'arguments': arguments,
            'result': result,
            'iteration': self.current_iteration
        })
    
    def get_steps_summary(self):
        summary = []
        for i, step in enumerate(self.steps):
            summary.append(f"{i+1}. {step['tool_name']}({step['arguments']}) -> {'成功' if 'success' in step['result'] and step['result'].get('success') else '失败'}")
        return "\n".join(summary)
    
    def get_variables(self):
        return self.variables
    
    def set_variable(self, name, value):
        self.variables[name] = value
    
    def increment_iteration(self):
        self.current_iteration += 1
    
    def should_stop(self):
        return self.current_iteration >= self.max_iterations

def extract_json_from_response(content):
    if content is None:
        return None
    
    content = content.strip()
    
    if content.startswith('```json'):
        content = content[7:]
        end_index = content.find('```')
        if end_index != -1:
            content = content[:end_index].strip()
    
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return None

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
                "name": "list_files",
                "description": "列出指定目录下的所有文件和子目录",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {"type": "string", "description": "目录路径"}
                    },
                    "required": ["directory"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "读取指定文件的内容",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {"type": "string", "description": "目录路径"},
                        "filename": {"type": "string", "description": "文件名"}
                    },
                    "required": ["directory", "filename"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_file",
                "description": "创建新文件并写入内容",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {"type": "string", "description": "目录路径"},
                        "filename": {"type": "string", "description": "文件名"},
                        "content": {"type": "string", "description": "文件内容"}
                    },
                    "required": ["directory", "filename", "content"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "delete_file",
                "description": "删除指定文件或空目录",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {"type": "string", "description": "目录路径"},
                        "filename": {"type": "string", "description": "文件名"}
                    },
                    "required": ["directory", "filename"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "rename_file",
                "description": "重命名指定文件",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {"type": "string", "description": "目录路径"},
                        "old_name": {"type": "string", "description": "旧文件名"},
                        "new_name": {"type": "string", "description": "新文件名"}
                    },
                    "required": ["directory", "old_name", "new_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "fetch_url",
                "description": "访问指定URL并返回网页内容",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "网页URL"}
                    },
                    "required": ["url"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "list_available_skills",
                "description": "列出所有可用的技能",
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
                "description": "加载指定技能的内容",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "skill_name": {"type": "string", "description": "技能名称"}
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

def execute_single_tool(tool_name, arguments):
    try:
        if tool_name == 'list_files':
            return list_files(arguments.get('directory', ''))
        elif tool_name == 'read_file':
            return read_file(arguments.get('directory', ''), arguments.get('filename', ''))
        elif tool_name == 'create_file':
            return create_file(arguments.get('directory', ''), arguments.get('filename', ''), arguments.get('content', ''))
        elif tool_name == 'delete_file':
            return delete_file(arguments.get('directory', ''), arguments.get('filename', ''))
        elif tool_name == 'rename_file':
            return rename_file(arguments.get('directory', ''), arguments.get('old_name', ''), arguments.get('new_name', ''))
        elif tool_name == 'fetch_url':
            return fetch_url(arguments.get('url', ''))
        elif tool_name == 'list_available_skills':
            return list_available_skills()
        elif tool_name == 'load_skill_content':
            return load_skill_content(arguments.get('skill_name', ''))
        else:
            return json.dumps({"success": False, "error": f"Unknown tool: {tool_name}"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

def build_analysis_prompt(user_request, context):
    steps_summary = context.get_steps_summary()
    
    prompt = f"""
你是一个具备链式工具调用能力的AI助手。请根据用户的请求和已执行的步骤历史，决定下一步操作。

## 用户请求
{user_request}

## 已执行步骤
{steps_summary if steps_summary else '暂无'}

## 可用工具
1. list_files(directory) - 列出目录下的文件
2. read_file(directory, filename) - 读取文件内容
3. create_file(directory, filename, content) - 创建文件
4. delete_file(directory, filename) - 删除文件
5. rename_file(directory, old_name, new_name) - 重命名文件
6. fetch_url(url) - 访问网页
7. list_available_skills() - 列出可用技能
8. load_skill_content(skill_name) - 加载技能内容

## 决策规则
- 如果任务已完成或不需要工具调用，输出完成状态和最终回答
- 如果需要继续调用工具，选择合适的工具并提供正确的参数
- 可以使用上一步工具的输出结果作为下一步工具的输入参数
- 尽量减少不必要的步骤

## 输出格式
请严格按照JSON格式输出：

完成任务时：
{{"done": true, "answer": "最终回答内容"}}

继续调用工具时：
{{"done": false, "tool_call": {{"name": "工具名称", "arguments": {{"参数名": "参数值"}}}}}}

## 示例
用户请求："列出当前目录下的文件"
输出：{{"done": false, "tool_call": {{"name": "list_files", "arguments": {{"directory": "."}}}}}}

用户请求："读取文件内容并总结"（已读取文件）
输出：{{"done": true, "answer": "文件内容总结..."}}
"""
    
    return prompt.strip()

def execute_chained_tool_call(api_base, model, api_key, user_request, max_iterations=10):
    context = ChainedCallContext(max_iterations=max_iterations)
    
    system_prompt = """
你是一个具备链式工具调用能力的AI助手。你可以按照以下规则进行多步骤的工具调用：

## 链式调用规则
1. 你可以连续调用多个工具，前一个工具的输出可以作为后一个工具的输入
2. 每次调用后，系统会记录执行结果，你可以根据中间结果决定下一步操作
3. 当你认为任务已经完成时，请输出最终回答
4. 如果遇到错误或无法继续，请说明原因

## 工具调用顺序示例
示例1：读取文件并处理
1. list_files("practice06") -> 获取文件列表
2. read_file("practice06", "tool_client.py") -> 读取文件内容
3. 总结内容并输出最终回答

示例2：网页处理
1. fetch_url("https://example.com") -> 获取网页内容
2. create_file("output", "result.txt", "总结内容") -> 保存结果
3. 输出最终回答

## 上下文变量
你可以引用之前步骤的结果：
- 使用工具执行结果中的数据
- 根据文件内容进行判断和处理
- 将处理结果传递给下一个工具

## 注意事项
- 目录路径使用绝对路径或相对于当前脚本的路径
- 如果需要创建文件，确保目录存在
- 注意处理中文文件名和内容的编码问题
"""
    
    messages = [{"role": "system", "content": system_prompt.strip()}]
    
    print(f"\n{'='*60}")
    print(f"链式工具调用执行开始")
    print(f"{'='*60}")
    print(f"用户请求: {user_request}")
    print(f"最大迭代次数: {max_iterations}")
    print(f"{'='*60}\n")
    
    total_tokens = 0
    total_time = 0
    
    while not context.should_stop():
        context.increment_iteration()
        print(f"\n--- 第 {context.current_iteration} 轮 ---")
        
        analysis_prompt = build_analysis_prompt(user_request, context)
        messages.append({"role": "user", "content": analysis_prompt})
        
        start_time = time.time()
        response = call_llm(api_base, model, api_key, messages)
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        total_time += elapsed_time
        
        usage = response.get('usage', {})
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        total_tokens += prompt_tokens + completion_tokens
        
        print(f"LLM调用时间: {elapsed_time:.2f}秒")
        print(f"Token消耗: 输入={prompt_tokens}, 输出={completion_tokens}")
        
        message = response['choices'][0]['message']
        content = message.get('content', '')
        tool_calls = message.get('tool_calls', [])
        
        parsed_json = None
        if content:
            parsed_json = extract_json_from_response(content)
        
        if tool_calls:
            for tool_call in tool_calls:
                tool_name = tool_call['function']['name']
                arguments = json.loads(tool_call['function']['arguments'])
                
                print(f"工具调用: {tool_name}({arguments})")
                
                tool_result = execute_single_tool(tool_name, arguments)
                
                print(f"工具执行结果:")
                try:
                    result_json = json.loads(tool_result)
                    print(json.dumps(result_json, ensure_ascii=False, indent=2)[:500] + "..." if len(tool_result) > 500 else tool_result)
                except:
                    print(tool_result[:500] + "..." if len(tool_result) > 500 else tool_result)
                
                context.add_step(tool_name, arguments, json.loads(tool_result) if tool_result else {})
                
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
        
        elif parsed_json and isinstance(parsed_json, dict):
            if parsed_json.get('done'):
                print(f"\n{'='*60}")
                print(f"任务完成！")
                print(f"{'='*60}")
                print(f"最终回答: {parsed_json.get('answer', '')}")
                print(f"{'='*60}")
                print(f"总耗时: {total_time:.2f}秒")
                print(f"总Token消耗: {total_tokens}")
                return parsed_json.get('answer', '')
            elif 'tool_call' in parsed_json:
                tool_call_info = parsed_json['tool_call']
                tool_name = tool_call_info['name']
                arguments = tool_call_info.get('arguments', {})
                
                print(f"工具调用: {tool_name}({arguments})")
                
                tool_result = execute_single_tool(tool_name, arguments)
                
                print(f"工具执行结果:")
                try:
                    result_json = json.loads(tool_result)
                    print(json.dumps(result_json, ensure_ascii=False, indent=2)[:500] + "..." if len(tool_result) > 500 else tool_result)
                except:
                    print(tool_result[:500] + "..." if len(tool_result) > 500 else tool_result)
                
                context.add_step(tool_name, arguments, json.loads(tool_result) if tool_result else {})
                
                messages.append({
                    "role": "assistant",
                    "content": json.dumps(parsed_json, ensure_ascii=False)
                })
        
        else:
            print(f"LLM直接回复: {content[:200]}..." if len(content) > 200 else content)
            messages.append({"role": "assistant", "content": content})
    
    print(f"\n{'='*60}")
    print(f"达到最大迭代次数，任务终止")
    print(f"{'='*60}")
    print(f"已执行步骤:")
    print(context.get_steps_summary())
    print(f"总耗时: {total_time:.2f}秒")
    print(f"总Token消耗: {total_tokens}")
    return f"任务未完成，已执行 {context.current_iteration} 轮。已执行步骤:\n{context.get_steps_summary()}"

def main():
    config = load_env()
    api_base = config.get('OPENAI_API_BASE', '')
    model = config.get('OPENAI_API_MODEL', '')
    api_key = config.get('OPENAI_API_KEY', '')

    if not all([api_base, model, api_key]):
        print('Error: Please configure .env file with OPENAI_API_BASE, OPENAI_API_MODEL, OPENAI_API_KEY')
        return

    print(f"\n{'='*60}")
    print(f"链式工具调用演示系统")
    print(f"{'='*60}")
    print(f"可用工具: list_files, read_file, create_file, delete_file, rename_file, fetch_url, list_available_skills, load_skill_content")
    print(f"{'='*60}\n")

    print("选择测试场景:")
    print("1. 文件搜索链式调用 - 查找practice06目录下包含'def'关键词的文件")
    print("2. 多文件操作 - 读取1.txt和2.txt并求和写入result.txt")
    print("3. 网页处理链式调用 - 访问网页并保存摘要")
    print("4. 自定义输入")
    
    choice = input("\n请输入选择(1-4): ")
    
    if choice == '1':
        user_request = "请查找 practice06 目录下所有包含'def'关键词的文件，并总结这些文件的主要内容"
    elif choice == '2':
        user_request = f"读取 {PRACTICE07_DIR}\\1.txt 和 {PRACTICE07_DIR}\\2.txt 两个文件，文件内容都是正整数，把两个数相加的和写入 result.txt 文件"
    elif choice == '3':
        user_request = "访问 https://www.nsu.edu.cn/HTML/news/2024/06/article_3974.html 并总结页面内容，保存到 practice07/summary.txt"
    else:
        user_request = input("请输入你的请求: ")
    
    result = execute_chained_tool_call(api_base, model, api_key, user_request)
    print(f"\n最终结果: {result}")

if __name__ == '__main__':
    main()
