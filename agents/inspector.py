from utils.llm_client import get_llm_response

class InspectorAgent:
    """
    Analyzes the bug report, logs, and code to determine the root cause.
    """
    def analyze(self, bug_report: str, error_log: str, code_content: str) -> str:
        prompt = f"""
        Analyze the following bug report, error log, and code snippet.
        Identify the root cause of the bug.

        # Bug Report
        {bug_report}

        # Error Log
        {error_log}

        # Source Code
        ```python
        {code_content}
        ```
        
        Provide a detailed Root Cause Analysis (RCA). Explain exactly what lines are failing and why.
        """
        system_instruction = "You are an expert Python software engineer acting as an Inspector Agent. Your job is to find the root cause of software defects accurately and concisely."
        
        return get_llm_response(prompt, system_instruction=system_instruction)
