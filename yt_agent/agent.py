import os
import pathlib
from typing import Optional, List, Any

# Try importing google.generativeai, but fail gracefully if not installed
try:
    import google.generativeai as genai
except ImportError:
    genai = None

from .tools.execution import execute_generated_code


class YtAgent:
    def __init__(
        self,
        model_name: str = "gemini-pro",
        system_instructions: Optional[List[str]] = None,
    ):
        self.model_name = model_name
        self.context = ""
        self.system_instructions = system_instructions or []
        self.knowledge_base_dir = pathlib.Path(__file__).parent / "knowledge_base"

        # Simple file-based logging for history
        self.history_file = pathlib.Path("yt_agent_history.log")

        self.model = None

        self._load_knowledge_base()

        # Configure API key if available
        api_key = os.environ.get("GOOGLE_API_KEY")
        if genai and api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)

    def _load_knowledge_base(self):
        """Loads markdown files from the knowledge_base directory."""
        if not self.knowledge_base_dir.exists():
            print(f"Warning: Knowledge base not found at {self.knowledge_base_dir}")
            return

        context_parts = []
        for md_file in self.knowledge_base_dir.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                context_parts.append(
                    f"--- Context from {md_file.name} ---\n{content}\n"
                )
            except Exception as e:
                print(f"Warning: Failed to read {md_file}: {e}")

        self.context = "\n".join(context_parts)

    def _log_interaction(self, query: str, code: str, success: bool, output: str):
        try:
            with open(self.history_file, "a", encoding="utf-8") as f:
                f.write(
                    f"--- Interaction ---\nQuery: {query}\nCode:\n{code}\nSuccess: {success}\nOutput:\n{output}\n\n"
                )
        except Exception as e:
            print(f"Warning: Failed to write to history log: {e}")

    def generate_code(self, user_query: str) -> str:
        """
        Translates a natural language query into execution-ready Python code.
        """
        prompt = self._construct_prompt(user_query)

        if self.model:
            try:
                response = self.model.generate_content(prompt)
                return self._extract_code(response.text)
            except Exception as e:
                return f"# Error generating code: {e}"
        else:
            # Fallback mock for testing/scaffolding
            return (
                f"# [Mock Output] Agent received query: '{user_query}'\n"
                f"# Normally this would call the LLM with the context:\n"
                f"# {len(self.context)} characters of documentation loaded.\n"
                f"import yt\n"
                f"print('This is a dummy response. Install google-generativeai and set GOOGLE_API_KEY to run real queries.')"
            )

    def _construct_prompt(self, query: str) -> str:
        return f"""You are an expert assistant for the 'yt' volumetric data analysis library.
        
Use the following documentation context to answer the user's request.
CONTEXT:
{self.context}

USER REQUEST:
{query}

INSTRUCTIONS:
1. Generate valid Python code.
2. Assume 'import yt' is needed.
3. If the request is unclear, generate code that prints a clarification message.
4. Output ONLY the code block.
"""

    def _extract_code(self, text: str) -> str:
        """Simple extractor for markdown code blocks."""
        if "```python" in text:
            return text.split("```python")[1].split("```")[0].strip()
        elif "```" in text:
            return text.split("```")[1].split("```")[0].strip()
        return text.strip()

    def run(self, user_query: str, auto_execute: bool = False):
        """
        Main operation: Interpret -> Generate -> Execute (optional).
        """
        print(f"Agent: Processing '{user_query}'...")

        code = self.generate_code(user_query)

        print("\n--- Generated Code ---\n")
        print(code)
        print("\n----------------------")

        success = False
        output_log = ""

        if auto_execute:
            print("\nAgent: Executing code...")
            stdout, stderr, err = execute_generated_code(code)

            output_log = f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"
            if err:
                output_log += f"\nEXCEPTION:\n{err}"

            if stdout:
                print(f"[STDOUT]\n{stdout}")
            if stderr:
                print(f"[STDERR]\n{stderr}")
            if err:
                print(f"[EXCEPTION]\n{err}")

            if not err:
                success = True
        else:
            print("\n(Execution skipped. Use auto_execute=True to run.)")
            output_log = "(Execution skipped)"

        self._log_interaction(user_query, code, success, output_log)
