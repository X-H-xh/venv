import os
import json
import time
import stat
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

def list_files(directory):
    if not os.path.isdir(directory):
        return f"Error: {directory} is not a valid directory"
    
    files_info = []
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        try:
            file_stat = os.stat(filepath)
            file_size = file_stat.st_size
            file_mtime = time.ctime(file_stat.st_mtime)
            file_mode = file_stat.st_mode
            
            if os.path.isdir(filepath):
                file_type = "directory"
            elif os.path.isfile(filepath):
                file_type = "file"
            else:
                file_type = "other"
            
            files_info.append({
                "name": filename,
                "type": file_type,
                "size": file_size,
                "size_human": f"{file_size} bytes" if file_size < 1024 else f"{file_size/1024:.2f} KB",
                "modified_time": file_mtime,
                "path": filepath
            })
        except Exception as e:
            files_info.append({
                "name": filename,
                "error": str(e)
            })
    
    return json.dumps(files_info, ensure_ascii=False, indent=2)

def rename_file(directory, old_name, new_name):
    old_path = os.path.join(directory, old_name)
    new_path = os.path.join(directory, new_name)
    
    if not os.path.exists(old_path):
        return f"Error: File {old_name} does not exist in {directory}"
    
    if os.path.exists(new_path):
        return f"Error: File {new_name} already exists in {directory}"
    
    try:
        os.rename(old_path, new_path)
        return f"Success: File renamed from {old_name} to {new_name}"
    except Exception as e:
        return f"Error: {str(e)}"

def delete_file(directory, filename):
    filepath = os.path.join(directory, filename)
    
    if not os.path.exists(filepath):
        return f"Error: File {filename} does not exist in {directory}"
    
    try:
        if os.path.isdir(filepath):
            os.rmdir(filepath)
        else:
            os.remove(filepath)
        return f"Success: File {filename} deleted"
    except Exception as e:
        return f"Error: {str(e)}"

def create_file(directory, filename, content):
    filepath = os.path.join(directory, filename)
    
    if os.path.exists(filepath):
        return f"Error: File {filename} already exists in {directory}"
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Success: File {filename} created with content"
    except Exception as e:
        return f"Error: {str(e)}"

def read_file(directory, filename):
    filepath = os.path.join(directory, filename)
    
    if not os.path.exists(filepath):
        return f"Error: File {filename} does not exist in {directory}"
    
    if not os.path.isfile(filepath):
        return f"Error: {filename} is not a file"
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error: {str(e)}"

def fetch_url(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        req = Request(url, headers=headers, method='GET')
        with urlopen(req, timeout=30) as response:
            content = response.read().decode('utf-8', errors='replace')
            content_type = response.headers.get('Content-Type', '')
            status_code = response.status
            
            result = {
                "status_code": status_code,
                "content_type": content_type,
                "content_length": len(content),
                "content": content[:5000] if len(content) > 5000 else content
            }
            
            if len(content) > 5000:
                result["truncated"] = True
                result["note"] = f"内容已截断，原长度 {len(content)} 字符"
            
            return json.dumps(result, ensure_ascii=False, indent=2)
    except HTTPError as e:
        return json.dumps({"error": f"HTTP Error: {e.code} - {e.reason}"}, ensure_ascii=False, indent=2)
    except URLError as e:
        return json.dumps({"error": f"URL Error: {str(e.reason)}"}, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Error: {str(e)}"}, ensure_ascii=False, indent=2)

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
                "description": "列出指定目录下的所有文件及其属性",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "要列出文件的目录路径"
                        }
                    },
                    "required": ["directory"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "rename_file",
                "description": "重命名指定目录下的文件",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "文件所在的目录路径"
                        },
                        "old_name": {
                            "type": "string",
                            "description": "原文件名"
                        },
                        "new_name": {
                            "type": "string",
                            "description": "新文件名"
                        }
                    },
                    "required": ["directory", "old_name", "new_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "delete_file",
                "description": "删除指定目录下的文件或空目录",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "文件所在的目录路径"
                        },
                        "filename": {
                            "type": "string",
                            "description": "要删除的文件名"
                        }
                    },
                    "required": ["directory", "filename"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_file",
                "description": "在指定目录下创建新文件并写入内容",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "要创建文件的目录路径"
                        },
                        "filename": {
                            "type": "string",
                            "description": "新文件名"
                        },
                        "content": {
                            "type": "string",
                            "description": "要写入文件的内容"
                        }
                    },
                    "required": ["directory", "filename", "content"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "读取指定目录下文件的内容",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "文件所在的目录路径"
                        },
                        "filename": {
                            "type": "string",
                            "description": "要读取的文件名"
                        }
                    },
                    "required": ["directory", "filename"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "fetch_url",
                "description": "通过HTTP/HTTPS协议获取网页内容，类似curl功能",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "要访问的网页URL地址"
                        }
                    },
                    "required": ["url"]
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
    
    if function_name == 'list_files':
        return list_files(arguments.get('directory', ''))
    elif function_name == 'rename_file':
        return rename_file(arguments.get('directory', ''), arguments.get('old_name', ''), arguments.get('new_name', ''))
    elif function_name == 'delete_file':
        return delete_file(arguments.get('directory', ''), arguments.get('filename', ''))
    elif function_name == 'create_file':
        return create_file(arguments.get('directory', ''), arguments.get('filename', ''), arguments.get('content', ''))
    elif function_name == 'read_file':
        return read_file(arguments.get('directory', ''), arguments.get('filename', ''))
    elif function_name == 'fetch_url':
        return fetch_url(arguments.get('url', ''))
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

    system_prompt = """
你是一个具备文件操作能力和网络访问能力的AI助手。你可以使用以下工具来完成各种任务：

文件操作工具：
1. list_files(directory) - 列出指定目录下的所有文件及其属性（名称、类型、大小、修改时间）
2. rename_file(directory, old_name, new_name) - 重命名指定目录下的文件
3. delete_file(directory, filename) - 删除指定目录下的文件或空目录
4. create_file(directory, filename, content) - 在指定目录下创建新文件并写入内容
5. read_file(directory, filename) - 读取指定目录下文件的内容

网络工具：
6. fetch_url(url) - 通过HTTP/HTTPS协议获取网页内容，返回状态码、内容类型和网页内容

请根据用户的请求，决定是否需要调用工具。如果需要调用工具，请按照JSON格式输出工具调用。

当收到工具执行结果后，请总结结果给用户。
"""

    user_prompt = input("请输入你的文件操作请求: ")
    
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
