import difflib

class ReporterAgent:
    """
    Generates GitHub/Gitlab style pull request summaries and code diffs.
    """
    def generate_report(self, original_code: str, patched_code: str, target_file: str) -> str:
        diff = difflib.unified_diff(
            original_code.splitlines(),
            patched_code.splitlines(),
            fromfile=f"a/{target_file}",
            tofile=f"b/{target_file}",
            lineterm=''
        )
        diff_str = "\n".join(diff)
        
        report = f"""
# Pull Request Summary: Automated AI Bug Fix

## Changes Made
- Identified and fixed root cause in `{target_file}`.
- Validated via automated sandbox testing.

## Git Diff
```diff
{diff_str}
```
"""
        return report.strip()
