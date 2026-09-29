# Multi-Agent Workflow Specification 🤖

This document provides a detailed breakdown of the internal workflow, lifecycle state transitions, data exchange protocols, and decision loops across the four autonomous agents.

---

## 🔄 Agent Workflow & Lifecycle Diagram

```mermaid
stateDiagram-v2
    [*] --> Ingestion: CLI / Interactive Invocation

    state Ingestion {
        [*] --> LoadEnv: Load GROQ_API_KEY from .env
        LoadEnv --> ReadTarget: Read Target Source File
        ReadTarget --> ParseInputs: Ingest Bug Description & Traceback
        ParseInputs --> [*]
    }

    Ingestion --> Phase1_Inspection: Pass Code + Bug Report + Error Logs

    state Phase1_Inspection {
        [*] --> PromptInspector: Synthesize RCA Prompt
        PromptInspector --> QueryGroq_RCA: Call Groq API (gpt-oss-120b)
        QueryGroq_RCA --> ParseRCA: Extract Root Cause Analysis
        ParseRCA --> [*]
    }

    Phase1_Inspection --> Phase2_Development: Pass RCA + Original Code

    state Phase2_Development {
        [*] --> FormatPrompt: Construct System & Developer Prompt
        FormatPrompt --> QueryGroq_Dev: Call Groq API
        QueryGroq_Dev --> ParseBlocks: Extract <<<< SEARCH ==== REPLACE >>>>
        ParseBlocks --> ApplyDiff: In-Memory Patch Application
        ApplyDiff --> [*]
    }

    Phase2_Development --> Phase3_Validation: Candidate Patched Code

    state Phase3_Validation {
        [*] --> CreateSandbox: tempfile.mkdtemp()
        CreateSandbox --> CopyWorkspace: shutil.copytree(source_dir)
        CopyWorkspace --> InjectPatch: Overwrite target file in sandbox
        InjectPatch --> ExecutePytest: subprocess.run(['pytest'], env=PYTHONPATH)
        ExecutePytest --> EvaluateResult: Check returncode == 0
        EvaluateResult --> CleanupSandbox: shutil.rmtree(temp_dir)
        CleanupSandbox --> [*]
    }

    state RetryDecision <<choice>>
    Phase3_Validation --> RetryDecision: Evaluate Outcome

    RetryDecision --> Phase2_Development: ❌ Tests Failed & Retry < 2<br/>(Inject pytest error trace into prompt)
    RetryDecision --> Phase4_Reporting: ✅ Tests Passed
    RetryDecision --> Aborted: ⚠️ Retry limit reached (2 retries exhausted)

    state Phase4_Reporting {
        [*] --> PromptReporter: Synthesize PR Diff & Summary Prompt
        PromptReporter --> QueryGroq_Rep: Call Groq API
        QueryGroq_Rep --> FormatPR: Generate Markdown Summary & Unified Diff
        FormatPR --> ApplyToDisk: Write verified code to original target file
        ApplyToDisk --> [*]
    }

    Phase4_Reporting --> Completed: Success! (Target fixed & documented)
    Completed --> [*]
    Aborted --> [*]
```

---

## 📊 Detailed Agent-by-Agent Workflow

```mermaid
flowchart LR
    subgraph S0["0. Pipeline Controller"]
        direction TB
        M1["main.py"]
        M2["Input Validation"]
        M1 --> M2
    end

    subgraph S1["1. Inspector Agent"]
        direction TB
        I_In["Inputs:<br/>• target_code<br/>• bug_report<br/>• error_logs"]
        I_Proc["Groq Prompt:<br/>Root Cause Analysis"]
        I_Out["Output:<br/><b>RCA Document</b>"]
        I_In --> I_Proc --> I_Out
    end

    subgraph S2["2. Developer Agent"]
        direction TB
        D_In["Inputs:<br/>• original_code<br/>• RCA<br/>• (optional) retry_error"]
        D_Proc["Surgical Diff Engine:<br/>Search/Replace parsing"]
        D_Out["Output:<br/><b>Patched Code</b>"]
        D_In --> D_Proc --> D_Out
    end

    subgraph S3["3. Validator Agent"]
        direction TB
        V_In["Inputs:<br/>• source_dir<br/>• target_file<br/>• patched_code"]
        V_Proc["Sandboxed Pytest:<br/>Isolated temp directory"]
        V_Out["Outputs:<br/>• passed: bool<br/>• error_log: str"]
        V_In --> V_Proc --> V_Out
    end

    subgraph S4["4. Reporter Agent"]
        direction TB
        R_In["Inputs:<br/>• original_code<br/>• patched_code<br/>• target_file"]
        R_Proc["Groq Prompt:<br/>PR Description & Diff"]
        R_Out["Outputs:<br/>• PR Summary<br/>• Saved to Disk"]
        R_In --> R_Proc --> R_Out
    end

    S0 --> S1 --> S2 --> S3
    S3 -- "❌ Retry Loop (≤ 2)" --> S2
    S3 -- "✅ Tests Pass" --> S4
```

---

## 📋 Data Exchange & Schema Protocol

Between each phase, agents exchange strictly defined data artifacts:

| Step | Sender | Receiver | Payload / Data Structure | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **1** | `main.py` | `InspectorAgent` | `bug_report: str`, `error_log: str`, `original_code: str` | Initial problem statement & source code |
| **2** | `InspectorAgent` | `DeveloperAgent` | `rca: str`, `original_code: str` | Pinpointed lines and technical explanation of root cause |
| **3** | `DeveloperAgent` | `ValidatorAgent` | `patched_code: str` | Candidate code containing applied SEARCH/REPLACE blocks |
| **4** | `ValidatorAgent` | `DeveloperAgent` *(on failure)* | `context_rca += "\nPrevious fix failed with: " + current_error` | Iterative retry feedback with exact pytest trace |
| **5** | `ValidatorAgent` | `ReporterAgent` *(on success)* | `passed == True`, `patched_code: str` | Confirmation that all tests passed green |
| **6** | `ReporterAgent` | `User / Disk` | `report: str`, writes to disk at `target_path` | Markdown PR overview and updated production file |

---

## 🛡️ Failure Handling & Self-Healing Policies

1. **Model Fallback**:
   - Primary: `openai/gpt-oss-120b` (robust reasoning for RCA and surgical patching).
   - Fallback: `qwen/qwen3.8-27b` and `openai/gpt-oss-20b` if primary experiences rate-limits or timeouts.
2. **Search/Replace Block Fault Tolerance**:
   - If the Developer Agent returns markdown codeblocks instead of search/replace tags, `DeveloperAgent._apply_blocks()` contains a regex fallback parser to extract raw python code cleanly.
3. **Sandbox Isolation**:
   - Any side effects or broken dependencies generated during validation are discarded when `Sandbox.cleanup()` deletes the temporary directory.
   - The original code is **only** overwritten once `pytest` passes with exit code `0`.
