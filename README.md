```bash
FileAgent-SelfHealer/
├── main.py                 # 项目入口，初始化 Graph 并运行
├── state.py                # 定义 AgentState（状态机的数据结构）
├── config.py               # 配置文件（API Keys, 模型参数, 根目录设置）
│
├── agent/
│   ├── workflow.py         # 核心！使用 LangGraph 定义节点和边（Router, Loop）
│   └── prompts.py          # 系统提示词（包含探索逻辑、ReAct 指令、反思引导）
│
├── tools/
│   ├── __init__.py         # 导出所有工具
│   ├── explorer_tools.py   # 搜索类：ls, grep, find, read_header
│   ├── editor_tools.py     # 编辑类：write_file, patch_file (正则替换)
│   └── executor_tools.py   # 执行类：run_python_script (核心自愈工具)
│
├── sandbox/                # (可选) 用于存放测试用的代码片段
│   └── example_project/    # 准备一个有 Bug 的 Python 项目用于 Demo 展示
│
├── utils/
│   └── logger.py           # 记录 Agent 的思考轨迹 (Traceability)
│
├── requirements.txt        # langgraph, langchain, openai/anthropic, etc.
└── README.md               # 亮点说明：架构图、自愈逻辑、如何运行 Demo
```