import sys
import os
import argparse
from dotenv import load_dotenv

# Ensure safe UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

load_dotenv()

from agents.inspector import InspectorAgent
from agents.developer import DeveloperAgent
from agents.validator import ValidatorAgent
from agents.reporter import ReporterAgent

def main():
    parser = argparse.ArgumentParser(description="Autonomous AI Bug Fixing Pipeline")
    parser.add_argument("--repo_path", type=str, help="Path to the repository to fix")
    parser.add_argument("--target_file", type=str, help="Relative path to the buggy file")
    parser.add_argument("--bug_report", type=str, help="Description of the bug")
    parser.add_argument("--error_log", type=str, help="Error logs (optional)", default="")
    args = parser.parse_args()

    print("🚀 Starting Autonomous AI Bug Fixing Pipeline...\n")
    
    # 1. Accept Source Code Repository and Bug Description
    if not args.repo_path:
        prompt_val = input("Please enter the path to the repository [default: demo_target]: ").strip()
        args.repo_path = prompt_val if prompt_val else "demo_target"
    if not args.target_file:
        prompt_val = input("Please enter the relative path to the buggy file [default: order_processor.py]: ").strip()
        args.target_file = prompt_val if prompt_val else "order_processor.py"
    if not args.bug_report:
        prompt_val = input("Please enter the bug report/description: ").strip()
        args.bug_report = prompt_val if prompt_val else "When an order has customer tier discounts or coupons applied, the sales tax is incorrectly calculated on the gross subtotal instead of the net discounted taxable amount in process_order, resulting in customers being overcharged."
    if not args.error_log:
        prompt_val = input("Please enter any error logs (press Enter to skip): ").strip()
        args.error_log = prompt_val

    repo_dir = args.repo_path
    target_file = args.target_file
    bug_report = args.bug_report
    error_log = args.error_log

    target_path = os.path.join(repo_dir, target_file)
    
    if not os.path.exists(target_path):
        print(f"❌ Error: Target file not found at {target_path}")
        return

    with open(target_path, 'r', encoding='utf-8') as f:
        original_code = f.read()
    
    # Initialize 4-Agent System
    inspector = InspectorAgent()
    developer = DeveloperAgent()
    validator = ValidatorAgent()
    reporter = ReporterAgent()
    
    # --- PHASE 1: INSPECTION ---
    print("🔍 [Inspector Agent] Analyzing codebase and error logs...")
    rca = inspector.analyze(bug_report, error_log, original_code)
    print("✅ Root Cause Analysis Complete.\n")
    
    max_retries = 2
    retry_count = 0
    passed = False
    
    patched_code = original_code
    current_error = error_log
    
    # --- PHASE 2 & 3: DEVELOPMENT & VALIDATION LOOP ---
    while retry_count <= max_retries and not passed:
        print(f"💻 [Developer Agent] Generating code patch (Attempt {retry_count + 1}/{max_retries + 1})...")
        
        # If we failed before, feed the new failure back into the context
        context_rca = rca
        if retry_count > 0:
            context_rca += f"\n\nUpdate: The previous fix failed validation with this error:\n{current_error}"
            
        patched_code = developer.generate_fix(context_rca, original_code)
        
        print("🧪 [Validator Agent] Sandboxing code and running tests...")
        passed, current_error = validator.validate(repo_dir, target_file, patched_code)
        
        if passed:
            print("✅ Validation Successful! All tests passed.\n")
        else:
            print(f"❌ Validation Failed. Retrying...\n--- Error Snippet ---\n{current_error[:300]}...\n---------------------\n")
            retry_count += 1

    # --- PHASE 4: REPORTING ---
    if passed:
        print("📝 [Reporter Agent] Generating PR Summary and Patch Diff...")
        report = reporter.generate_report(original_code, patched_code, target_file)
        
        print("\n" + "="*50)
        print(report)
        print("="*50)
        
        # Apply the fix directly to the demo target so the user sees the result
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(patched_code)
        print(f"\n🎉 Successfully patched {target_path}")
    else:
        print("\n⚠️ Pipeline aborted. Failed to fix the bug within the retry limit.")

if __name__ == "__main__":
    main()
