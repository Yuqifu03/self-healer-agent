# FileAgent-SelfHealer

FileAgent-SelfHealer is an autonomous AI agent that explores, diagnoses, and repairs Python codebases within a secure sandbox. It uses **Google Gemini** for reasoning and **LangGraph** to manage the self-healing loop.


## 🚀 Quick Start

### 1. Prerequisites
- Python 3.11 or 3.12
- A Google Gemini API Key

### 2. Configuration
Create a `.env` file in the project root:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
PROJECT_ROOT=./sandbox/example_project
```

### 3. Installation
```Bash
pip install requirements.txt
```

### 4. Run the Agent
Place your buggy Python files in sandbox/example_project/ and execute:

```Bash
python main.py
```

## 📂 Project Structure

- **main.py**: Entry point that initializes the agent and task.
- **config.py**: Handles API keys and sandbox path settings.
- **state.py**: Defines the data structure for the agent's memory.
- **agent/workflow.py**: Logic for the "Think → Act → Loop" cycle.
- **agent/prompts.py**: System instructions for the agent's "Perception-First" strategy.
- **tools/**
  - **explorer_tools.py**: Tools to list and read files.
  - **editor_tools.py**: Tools to edit or overwrite code.
  - **executor_tools.py**: Tool to run scripts and capture errors.
- **utils/logger.py**: Color-coded console and file logging.
