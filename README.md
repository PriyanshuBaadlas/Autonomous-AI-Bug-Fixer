# Autonomous AI Bug Fixing Pipeline 🚀

This is a multi-agent AI coding pipeline that automatically ingests a bug report and error log, finds the root cause, generates a patch, validates it in an isolated sandbox, and outputs a clean Git diff.

It fulfills all the core requirements of an automated bug-fixing system:
1. **Multi-agent architecture:** (Inspector, Developer, Validator, Reporter).
2. **LLM Powered:** Uses the Groq API (`llama3-70b-8192`) for rapid, free logic resolution.
3. **Diff-based Patching:** Modifies code surgically using Search/Replace blocks instead of replacing entire files, which minimizes hallucinations.
4. **Isolated Sandboxing:** Runs `pytest` automated validations in isolated temporary directories.
5. **Interactive & CLI Support:** Run via command line arguments or interactive prompts.

## ⚙️ Setup

1. Clone the repository.
2. Install the requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory and add your Groq API key:
   ```env
   GROQ_API_KEY="your_api_key_here"
   ```

## 🚀 Usage

You can run the script interactively by simply running:
```bash
python main.py
```
It will prompt you for the repository path, the target file, and the bug report.

Alternatively, you can provide the arguments directly via the CLI:
```bash
python main.py \
  --repo_path "demo_target" \
  --target_file "calculator.py" \
  --bug_report "The calculator add function is failing when we try to add two positive numbers." \
  --error_log "AssertionError: assert 5 == -1"
```

## 🧩 How it works

1. **🔍 Inspector Agent**: Analyzes the bug report and the original code to deduce the root cause.
2. **💻 Developer Agent**: Outputs exact `SEARCH/REPLACE` blocks to fix the code.
3. **🧪 Validator Agent**: Copies the repository to a temporary directory, applies the patch, configures `PYTHONPATH`, and executes `pytest`. If it fails, the error is fed back to the Developer Agent for a retry.
4. **📝 Reporter Agent**: Once tests pass, it generates a clean Pull Request summary and unified diff.
