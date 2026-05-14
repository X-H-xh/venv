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

## 使用示例

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

## 目录结构

```
.
├── env.example          # 环境变量模板文件
├── .gitignore           # Git忽略配置
├── venv/                # Python虚拟环境
└── practice01/          # 练习01：LLM基础调用
    └── llm_client.py    # LLM客户端脚本
```

## 教学进度

| 章节 | 主题 | 状态 |
|------|------|------|
| Practice 01 | LLM基础调用与性能统计 | ✅ 完成 |
