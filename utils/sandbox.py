import os
import shutil
import tempfile
import subprocess
from typing import Tuple

class Sandbox:
    """
    Creates an isolated environment for testing generated code fixes.
    """
    def __init__(self, source_dir: str):
        self.source_dir = os.path.abspath(source_dir)
        self.temp_dir = tempfile.mkdtemp(prefix="bugfix_sandbox_")

    def setup(self):
        """Copies the target project into the isolated sandbox."""
        shutil.copytree(self.source_dir, self.temp_dir, dirs_exist_ok=True)
        return self.temp_dir

    def apply_patch(self, relative_filepath: str, new_content: str):
        """Applies the LLM-generated code patch to the sandbox."""
        target_path = os.path.join(self.temp_dir, relative_filepath)
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

    def run_tests(self, test_command: list[str] = ["pytest"]) -> Tuple[bool, str]:
        """Runs the validation tests in the sandboxed environment."""
        try:
            env = os.environ.copy()
            env["PYTHONPATH"] = self.temp_dir
            result = subprocess.run(
                test_command,
                cwd=self.temp_dir,
                capture_output=True,
                text=True,
                check=False,
                env=env
            )
            passed = result.returncode == 0
            output = result.stdout + "\n" + result.stderr
            return passed, output
        except Exception as e:
            return False, f"Exception occurred while running tests: {str(e)}"

    def cleanup(self):
        """Removes the sandbox directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
