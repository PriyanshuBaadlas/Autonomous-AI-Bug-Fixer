# Autonomous AI Bug Fixing Pipeline — Architecture 🏗️

This document details the multi-agent design, component interactions, and execution flow of the **Autonomous AI Bug Fixing Pipeline**.

> 💡 For the step-by-step lifecycle state machine and data exchange protocols, see [AGENT_WORKFLOW.md](AGENT_WORKFLOW.md).

---

## 📊 High-Level Architecture Diagram

```mermaid
flowchart TD
    subgraph Inputs["1. Ingestion & Context"]
        A1["📄 Target Source Code"]
        A2["📝 Bug Report / Description"]
        A3["⚠️ Error Logs / Traceback"]
    end

    subgraph Phase1["2. Inspection Phase"]
        B["🔍 Inspector Agent"]
        LLM1[("Groq API<br/>gpt-oss-120b / qwen3.8-27b")]
        RCA["📋 Root Cause Analysis (RCA)"]
    end

    subgraph Phase23["3. Development & Validation Loop"]
        C["💻 Developer Agent"]
        LLM2[("Groq API<br/>Patch Synthesis")]
        Patch["✂️ Search/Replace Blocks"]
        
        subgraph Sandbox["Isolated Sandbox (tempfile)"]
            S1["📁 Clone Target Dir"]
            S2["🧩 Apply Patch"]
            S3["🧪 Run pytest Suite"]
        end
        
        Decision{"Tests Passed?"}
        Retry["🔁 Feedback Loop<br/>(Append error trace, retry up to 2x)"]
    end

    subgraph Phase4["4. Reporting & Application"]
        D["📝 Reporter Agent"]
        LLM3[("Groq API<br/>PR Synthesis")]
        PR["📄 PR Summary & Unified Diff"]
        Disk["🎉 Update Target File on Disk"]
    end

    A1 & A2 & A3 --> B
    B <--> LLM1
    B --> RCA

    RCA --> C
    C <--> LLM2
    C --> Patch

    Patch --> S1 --> S2 --> S3 --> Decision
    Decision -- "❌ Failed" --> Retry
    Retry --> C
    Decision -- "✅ Passed" --> D

    D <--> LLM3
    D --> PR --> Disk
```

---

## 🧩 Agent Roles & Responsibilities

### 1. 🔍 Inspector Agent (`agents/inspector.py`)
- **Input**: Bug report, error logs/traceback, and original target source code.
- **Role**: Performs systematic Root Cause Analysis (RCA). Identifies specifically which functions, logic blocks, or boundary conditions are failing and explains the technical reason for the failure.
- **Output**: Detailed Root Cause Analysis (RCA) document passed to the Developer Agent.

### 2. 💻 Developer Agent (`agents/developer.py`)
- **Input**: RCA from the Inspector Agent, plus failure feedback from previous validation attempts (if any).
- **Role**: Synthesizes surgical code modifications without hallucinating or rewriting unchanged parts of the file.
- **Mechanism**: Enforces exact `SEARCH/REPLACE` blocks:
  ```text
  <<<<
  [exact lines from original code]
  ====
  [new replacement lines]
  >>>>
  ```
- **Output**: Patch representation that can be reliably mapped and applied onto the target file.

### 3. 🧪 Validator Agent (`agents/validator.py` & `utils/sandbox.py`)
- **Input**: Source directory, relative file path, and candidate patch.
- **Role**: Validates fixes in complete isolation before modifying the actual working tree.
- **Mechanism**:
  1. Creates an isolated temporary directory via Python's `tempfile.mkdtemp()`.
  2. Copies target project files into the sandbox.
  3. Applies the candidate patch to the sandboxed file.
  4. Configures `PYTHONPATH` and runs `pytest`.
  5. Tears down and cleans up sandbox resources (`shutil.rmtree`).
- **Feedback Loop**: If tests fail, captures the standard error / failure output and routes it back to the Developer Agent for iterative correction (up to 2 automatic retries).

### 4. 📝 Reporter Agent (`agents/reporter.py`)
- **Input**: Original code, final passing code, and target filename.
- **Role**: Generates a clean Pull Request summary containing:
  - High-level explanation of the bug and fix.
  - Standard unified git diff (`--- a/... +++ b/...`).
- **Disk Persistence**: Once verified, commits the validated patch directly to the target file on disk.

---

## 🔄 Execution Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User as User / CLI
    participant Main as Pipeline Orchestrator (main.py)
    participant Insp as Inspector Agent
    participant Dev as Developer Agent
    participant Val as Validator Agent (Sandbox)
    participant Rep as Reporter Agent
    participant LLM as Groq LLM API

    User->>Main: Provide repo_path, target_file, bug_report, error_log
    Main->>Insp: Request Root Cause Analysis
    Insp->>LLM: Send code, error logs, and bug description
    LLM-->>Insp: Return RCA
    Insp-->>Main: RCA complete

    loop Retries (Up to 2x if tests fail)
        Main->>Dev: Request code fix with RCA (+ previous error if retry)
        Dev->>LLM: Request SEARCH/REPLACE blocks
        LLM-->>Dev: Return patch blocks
        Dev-->>Main: Patched candidate code
        Main->>Val: Validate patch
        Val->>Val: Clone to temp sandbox & run pytest
        alt Tests Fail
            Val-->>Main: Return passed=False + error snippet
        else Tests Pass
            Val-->>Main: Return passed=True
        end
    end

    Main->>Rep: Generate PR Summary & Diff
    Rep->>LLM: Synthesize PR documentation
    LLM-->>Rep: Return markdown summary & diff
    Rep-->>Main: Final report
    Main->>User: Display report & write patch to target file
```

---

## ⚡ Key Architectural Advantages

- **Zero Full-File Rewrites**: Search/Replace patching prevents LLMs from hallucinating imports, dropping existing methods, or modifying formatting outside the bug scope.
- **Isolated Sandboxing**: Prevents broken patches from polluting the local workspace or triggering regressions until tests demonstrably pass.
- **Autonomous Feedback Loop**: If the LLM's first fix contains an edge-case failure, the raw pytest failure trace is immediately fed back into context for self-correction.
- **Fast Inference**: Powered by ultra-low-latency Groq LPUs (`openai/gpt-oss-120b` and `qwen/qwen3.8-27b`).
