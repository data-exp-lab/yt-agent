import os
import pathlib
import hashlib
import datetime
from typing import Optional, List, Any

# Try importing google.genai for the newer SDK.
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

from .tools.execution import execute_generated_code


class YtAgent:
    def __init__(
        self,
        model_name: str = "gemini-2.0-flash-001",
        system_instructions: Optional[List[str]] = None,
        use_cache: bool = True,
    ):
        self.model_name = model_name
        # Ensure system instruction is a string or list of strings
        if system_instructions and isinstance(system_instructions, list):
            self.system_instructions = "\n".join(system_instructions)
        else:
            self.system_instructions = (
                "You are an expert assistant for the 'yt' library."
            )

        self.history_file = pathlib.Path("yt_agent_history.log")
        self.knowledge_base_dir = pathlib.Path(__file__).parent / "knowledge_base"

        self.context = ""
        self.use_cache = use_cache
        self.cached_content_name = None
        self.client = None

        self._load_knowledge_base()

        # Configure Client
        api_key = os.environ.get("GOOGLE_API_KEY")
        if genai and api_key:
            try:
                self.client = genai.Client(api_key=api_key)
                self._setup_cache()
            except Exception as e:
                print(f"Warning: Failed to initialize genai.Client: {e}")
        elif not genai:
            print("Warning: google-genai library not found. Agent will be limited.")
        elif not api_key:
            print("Warning: GOOGLE_API_KEY not set. Agent will be limited.")

    def _load_knowledge_base(self):
        """Loads markdown files from the knowledge_base directory."""
        if not self.knowledge_base_dir.exists():
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

    def _setup_cache(self):
        """Sets up the model cache using the new SDK."""
        if not self.use_cache or not self.context:
            return

        # 1. Check if cache exists or needs creation
        # We use a hash of the content to identify the cache
        content_hash = hashlib.md5(self.context.encode("utf-8")).hexdigest()
        display_name = f"yt-agent-kb-{content_hash}"

        try:
            # List existing caches to see if we have a match
            # The SDK likely iterates over all caches
            # Note: client.caches.list() returns an iterator of CachedContent
            existing_cache = None
            try:
                for c in self.client.caches.list():
                    if c.display_name == display_name:
                        existing_cache = c
                        break
            except Exception as list_err:
                print(f"Warning: customized cache list iteration failed: {list_err}")

            if existing_cache:
                print(f"Using existing knowledge base cache: {existing_cache.name}")
                self.cached_content_name = existing_cache.name
                return

            print("Creating new knowledge base cache...")
            print(f"Length of context: {len(self.context)} chars")

            # Simple heuristic check for context length
            # Gemini usually requires ~32k tokens. If context is tiny, cache create might fail or be rejected.
            if len(self.context) < 1000:
                print(
                    "Context very small; skipping cache creation to avoid API overhead."
                )
                return

            try:
                cache_config = types.GenerateContentConfig(
                    system_instruction=self.system_instructions,
                )

                # Create the cache
                # Note: Correct usage for creating cache depends on SDK specificities.
                # Adjusting based on standard pattern:
                cache = self.client.caches.create(
                    model=self.model_name,
                    config=types.CreateCachedContentConfig(
                        display_name=display_name,
                        system_instruction=self.system_instructions,
                        contents=[
                            types.Content(
                                role="user", parts=[types.Part(text=self.context)]
                            )
                        ],
                        ttl="7200s",  # 2 hours
                    ),
                )
                self.cached_content_name = cache.name
                print(f"Cache created: {cache.name}")

            except Exception as create_err:
                print(
                    f"Cache creation returned error (might be too short or quota issue): {create_err}"
                )
                self.cached_content_name = None

        except Exception as e:
            print(f"Cache setup failed ({e}). Proceeding without cache.")
            self.cached_content_name = None

    def generate_code(self, user_query: str) -> str:
        """
        Translates a natural language query into execution-ready Python code.
        """
        if not self.client:
            return "# Error: No LLM client available."

        try:
            # Construct config based on whether we have a cache or not

            # If we have a cache, use it.
            if self.cached_content_name:
                # When using cache, we don't pass the context again, just the query.
                prompt = f"USER REQUEST:\n{user_query}\n\nGenerate valid Python code using 'import yt'."

                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        cached_content=self.cached_content_name,
                        temperature=0.2,
                    ),
                )
            else:
                # Standard context injection (No Cache)
                prompt = f"""
                {self.system_instructions}
                
                CONTEXT:
                {self.context}
                
                USER REQUEST:
                {user_query}
                
                INSTRUCTIONS:
                1. Generate valid Python code.
                2. Assume 'import yt' is needed.
                3. Output ONLY the code block.
                """
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.2),
                )

            return self._extract_code(response.text)

        except Exception as e:
            return f"# Error generating code: {e}"

    def _extract_code(self, text: str) -> str:
        if not text:
            return ""
        if "```python" in text:
            return text.split("```python")[1].split("```")[0].strip()
        elif "```" in text:
            return text.split("```")[1].split("```")[0].strip()
        return text.strip()

    def run(self, user_query: str, auto_execute: bool = False):
        print(f"Agent processing: '{user_query}'...")
        code = self.generate_code(user_query)

        print("\n--- Generated Code ---")
        print(code)
        print("----------------------\n")

        if auto_execute:
            print("Executing...")
            execute_generated_code(code)
        else:
            choice = input("Execute this code? (y/n): ")
            if choice.lower() == "y":
                execute_generated_code(code)
