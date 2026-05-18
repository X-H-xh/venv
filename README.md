# AI智能体开发教学项目

## 项目简介

这是一个基于Python的AI智能体开发教学项目，旨在帮助学习者掌握如何使用Python与LLM（大语言模型）进行交互。

## 环境配置

### 1. 激活虚拟环境
```powershell
.\venv\Scripts\Activate.ps1
```

### 2. 配置环境变量
复制 `env.example` 文件为 `.env` 并填写正确的配置参数：
```powershell
copy env.example .env
```

`.env` 文件内容：
```
OPENAI_API_BASE=https://your-api-endpoint.com/v1
OPENAI_API_MODEL=your-model-name
OPENAI_API_KEY=your-api-key-here
```

## 代码文件说明

### practice01/llm_client.py

**功能用途：**
- 读取项目根目录的 `.env` 文件，加载LLM配置参数
- 使用Python标准HTTP库（urllib）访问OpenAI兼容协议的LLM
- 发送聊天请求并获取响应
- 统计token消耗、请求时间和处理速度

**教学目标：**
1. 学习如何读取和解析环境变量配置文件
2. 掌握使用Python标准库发送HTTP POST请求
3. 理解OpenAI API的JSON请求/响应格式
4. 学习如何测量API调用的性能指标（耗时、token速度）
5. 了解LLM API的token计费机制

### practice02/tool_client.py

**功能用途：**
- 实现5文件操作工具函数：
  - `list_files(directory)` - 列出目录下的文件及其属性（名称、类型、大小、修改时间）
  - `rename_file(directory, old_name, new_name)` - 重命名文件
  - `delete_file(directory, filename)` - 删除文件或空目录
  - `create_file(directory, filename, content)` - 创建新文件并写入内容
  - `read_file(directory, filename)` - 读取文件内容
- 实现网络访问工具函数：
  - `fetch_url(url)` - 通过HTTP/HTTPS协议获取网页内容，返回状态码、内容类型和网页内容
- 将工具定义作为系统提示词发送给LLM
- 支持自动工具调用和结果总结

**教学目标：**
1. 学习如何定义和实现工具函数
2. 理解OpenAI工具调用的JSON格式
3. 掌握工具调用的请求构建方法
4. 学习如何解析LLM的工具调用响应
5. 理解工具执行结果的处理和总结流程
6. 掌握多轮对话中的工具调用模式
7. 学习HTTP请求的发送和响应处理

### practice03/chat_compression.py

**功能用途：**
- 实现聊天记录自动压缩功能
- 监控对话轮数（超过5轮触发压缩）
- 监控Token数量（超过3000触发压缩）
- 对前70%对话进行LLM摘要压缩
- 保留后30%对话原文
- 实时显示压缩统计信息

**教学目标：**
1. 学习聊天上下文管理策略
2. 理解对话轮数和Token估算方法
3. 掌握历史消息分割技术
4. 学习使用LLM进行对话摘要
5. 理解上下文压缩的实用价值

### practice03/chat_history.py

**功能用途：**
- **5W信息提取**：每5次对话自动提取关键信息（Who, What, When, Where, Why）
- **增量日志记录**：将提取的信息追加到 `D:\chat-log\log.txt`
- **聊天历史搜索**：支持 `/search` 命令和关键词搜索历史记录
- **智能搜索检测**：自动识别用户搜索意图

**教学目标：**
1. 学习5W信息提取方法
2. 掌握增量文件写入技术
3. 理解意图识别与搜索结合
4. 学习结合历史记录的上下文对话

### practice04/chat_client.py

**功能用途：**
- **AnythingLLM集成**：使用subprocess调用curl访问AnythingLLM API
- **文档仓库查询**：支持查询本地文档仓库中的知识
- **智能触发**：当用户提到"文档仓库"、"文件仓库"、"仓库"时自动触发

**配置要求：**
- 在.env文件中配置 `ANYTHINGLLM_API_KEY` 和 `ANYTHINGLLM_WORKSPACE_SLUG`
- 确保AnythingLLM运行在 `http://localhost:3001`

**教学目标：**
1. 学习subprocess模块调用外部命令
2. 理解API认证和HTTP请求构造
3. 掌握文档仓库RAG应用开发

### practice06/skill_client.py

**功能用途：**
- **技能列表管理**：自动扫描 `.agents/skills` 目录下的所有技能
- **YAML Front Matter解析**：提取每个技能的name和description字段
- **技能正文加载**：当LLM需要使用技能时，加载该技能的完整内容
- **动态技能注入**：将技能列表以JSON格式发送给LLM

**教学目标：**
1. 学习目录扫描和文件遍历技术
2. 掌握YAML front matter解析方法
3. 理解动态技能加载机制

### practice06/tool_client.py

**功能用途：**
- **工具调用版技能管理**：使用标准Function Call机制调用技能
- **支持多种工具**：list_available_skills、load_skill_content
- **自动工具选择**：LLM根据请求自动选择并调用工具

**教学目标：**
1. 学习OpenAI标准工具调用格式
2. 掌握工具定义和参数传递
3. 理解工具调用响应处理流程

### practice07/tool_client.py

**功能用途：**
- **链式工具调用**：前一个工具的输出作为后一个工具的输入
- **智能决策循环**：LLM根据中间结果自主决定下一步操作
- **上下文管理**：记录每一步调用和结果，存储中间变量
- **防无限循环**：设置最大迭代次数限制（默认10次）

**核心组件：**
| 组件 | 功能 |
|------|------|
| `ChainedCallContext` | 链式调用上下文管理器 |
| `execute_chained_tool_call` | 链式调用执行函数 |
| `build_analysis_prompt` | 分析提示词构建函数 |
| `extract_json_from_response` | JSON响应解析函数 |

**支持的工具：**
- `list_files(directory)` - 列出目录文件
- `read_file(directory, filename)` - 读取文件内容
- `create_file(directory, filename, content)` - 创建文件
- `delete_file(directory, filename)` - 删除文件
- `rename_file(directory, old_name, new_name)` - 重命名文件
- `fetch_url(url)` - 访问网页
- `list_available_skills()` - 列出技能
- `load_skill_content(skill_name)` - 加载技能内容

**输出格式：**
```json
{"done": true, "answer": "最终回答内容"}
{"done": false, "tool_call": {"name": "工具名称", "arguments": {...}}}
```

**教学目标：**
1. 理解链式工具调用的概念和应用场景
2. 掌握上下文管理器的设计和实现
3. 学习多轮工具调用的循环控制
4. 理解如何让LLM根据中间结果做决策

## 使用示例

### Practice 01 - LLM基础调用
```powershell
python practice01/llm_client.py
```

输出示例：
```
Model: gpt-3.5-turbo
API Base: https://api.openai.com/v1
--------------------------------------------------
Response: Hello! I'm doing well, thank you for asking. How can I assist you today?
--------------------------------------------------
Prompt Tokens: 16
Completion Tokens: 24
Total Tokens: 40
Time Elapsed: 1.23 seconds
Token/s Speed: 19.51
```

### Practice 02 - 工具调用
```powershell
python practice02/tool_client.py
```

输入示例：
```
请输入你的请求: 请访问 https://httpbin.org/html 并返回网页内容
```

输出示例：
```
Model: gpt-3.5-turbo
API Base: https://api.openai.com/v1
--------------------------------------------------
用户请求: 请访问 https://httpbin.org/html 并返回网页内容
--------------------------------------------------
LLM响应时间: 0.95秒
Token消耗: 输入=156, 输出=38, 总计=194
处理速度: 40.00 token/s
--------------------------------------------------
工具调用: fetch_url({"url": "https://httpbin.org/html"})
工具执行结果:
{
  "status_code": 200,
  "content_type": "text/html; charset=utf-8",
  "content_length": 644,
  "content": "<html>\n<head>\n<title>HTTP Mirror</title>\n</head>\n<body>HCP Mirror</body>\n</html>",
  "truncated": false
}
--------------------------------------------------
最终回复: 网页访问成功！

- 状态码：200
- 内容类型：text/html; charset=utf-8
- 网页内容：<html><head><title>HCP Mirror</title></head><body>HCP Mirror</body></html>

### Practice 03 - 聊天记录压缩
```powershell
python practice03/chat_compression.py
```

**功能说明：**
- 触发条件：超过5轮对话或上下文超过3000 Token
- 压缩策略：前70%内容压缩，最后30%保留原文
- 自动检测并触发压缩，保持对话上下文精简

输入示例：
```
你: Hello AI, how are you?
你: Can you help me with coding?
你: What is Python?
你: Tell me about functions.
你: How to define a class?
你: Explain inheritance.
```

输出示例：
```
============================================================
聊天记录压缩触发
============================================================
当前轮数: 6 (阈值: 5)
估算Token数: 3200 (阈值: 3000)
需要压缩的消息数: 4
保留原文的消息数: 2
压缩比例: 前70%压缩，保留后30%原文
============================================================
摘要生成完成，消耗Token: 150
摘要内容: [对话摘要] 主要话题：Python编程基础 关键信息：... [/摘要]
============================================================
Token减少: 2100 (减少 65.6%)
============================================================

AI: [AI回复内容]
```

### Practice 03 - 聊天历史管理
```powershell
python practice03/chat_history.py
```

**功能1: 5W信息提取**
- 每5轮对话自动提取关键信息并存入日志
- 日志文件位置: `D:\chat-log\log.txt`

输入示例：
```
你: 我今天要去超市买苹果
你: 然后去图书馆还书
你: 下午要开会讨论项目进度
你: 晚上约了朋友吃饭
你: 回家后要整理房间
```

输出示例：
```
>>> 当前对话轮数: 5
>>> 达到5轮，开始提取5W关键信息...
>>> 提取消耗Token: 180
>>> 已提取3条记录并保存到日志
>>> 内容预览:
记录1: 谁=用户;做了什么=去超市买苹果;何时=今天;何地=超市;为何=未提及;
记录2: 谁=用户;做了什么=还书;何时=下午;何地=图书馆;为何=未提及;
...
```

**功能2: 聊天历史搜索**

方式1 - 使用 /search 命令：
```
你: /search 今天做了什么
```

方式2 - 表达搜索意图：
```
你: 查找之前聊过的内容
```

输出示例：
```
>>> 检测到搜索请求: 今天做了什么
>>> 正在搜索聊天历史...

AI: 根据聊天历史记录，您今天进行了以下活动：
1. 上午去超市买苹果
2. 下午去图书馆还书
3. 晚上约了朋友吃饭
```

## 目录结构

```
.
├── env.example          # 环境变量模板文件
├── .gitignore           # Git忽略配置
├── venv/                # Python虚拟环境
├── .agents/             # 技能目录
│   └── skills/          # 技能列表
│       └── init-article/ # 示例技能
├── practice01/          # 练习01：LLM基础调用
│   └── llm_client.py    # LLM客户端脚本
├── practice02/          # 练习02：工具调用
│   └── tool_client.py   # 工具调用客户端脚本
├── practice03/          # 练习03：聊天记录管理与历史
│   ├── chat_compression.py  # 聊天压缩客户端脚本
│   └── chat_history.py      # 聊天历史管理脚本
├── practice04/          # 练习04：AnythingLLM集成
│   └── chat_client.py   # AnythingLLM集成脚本
├── practice06/          # 练习06：技能管理系统
│   ├── skill_client.py  # 标签触发版技能管理
│   └── tool_client.py   # Function Call版技能管理
└── practice07/          # 练习07：链式工具调用
    ├── tool_client.py   # 链式工具调用实现
    ├── 1.txt            # 测试文件1
    └── 2.txt            # 测试文件2
```

## 教学进度

| 章节 | 主题 | 状态 |
|------|------|------|
| Practice 01 | LLM基础调用与性能统计 | ✅ 完成 |
| Practice 02 | 工具调用功能实现 | ✅ 完成 |
| Practice 03 | 聊天记录压缩与历史管理 | ✅ 完成 |
| Practice 04 | AnythingLLM文档仓库集成 | ✅ 完成 |
| Practice 06 | 技能管理系统 | ✅ 完成 |
| Practice 07 | 链式工具调用 | ✅ 完成 |
