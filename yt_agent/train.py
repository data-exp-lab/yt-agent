import os
import pathlib
import json

# Try to import for interactive AI
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None


def get_llm_client():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable not set.")
        return None
    if not genai:
        print("Error: google-genai package not installed.")
        return None

    return genai.Client(api_key=api_key)


def manual_entry_mode():
    print(
        "AI integration unavailable. Create files manually in yt_agent/knowledge_base/"
    )


def interview_mode():
    print("\n--- yt Agent Knowledge Base Builder ---")

    client = get_llm_client()
    if not client:
        manual_entry_mode()
        return

    print("I will help you create a new documentation entry.")
    topic = input(
        "What topic do you want to document? (e.g. 'Phase Plots', 'Halo Finding')\n>> "
    ).strip()
    if not topic:
        return

    model_name = "gemini-2.0-flash-001"

    # Initialize Chat
    chat = client.chats.create(model=model_name)

    # Establish context
    system_prompt = f"""
    You are an expert technical interviewer for 'yt'.
    Your goal is to extract enough information from the user to write a CONCISE, COMPLETE reference doc.
    The user wants to document: {topic}
    
    Ask me 1-3 targeted questions about:
    - What is the specific use case?
    - Are there any specific parameters or gotchas?
    - Do I have a code snippet to include?
    
    Keep it brief.
    If the user has provided enough information, output 'READY_TO_GENERATE' (and nothing else).
    """

    try:
        response = chat.send_message(message=system_prompt)
        print(f"\nAI: {response.text}")

        # Loop for a few turns
        while True:
            user_input = input("\n>> ")
            if user_input.lower() in ("quit", "exit"):
                return

            if user_input.lower() == "done" or user_input.lower() == "generate":
                break

            response = chat.send_message(message=user_input)

            if "READY_TO_GENERATE" in response.text:
                print("\nAI: I have enough information. Generating content...")
                break
            else:
                print(f"\nAI: {response.text}")
                print("(Type 'generate' or 'done' to force generation)")

        # Generate Final Content
        final_prompt = """
        Based on our conversation, generate the final Markdown file content.
        Structure:
        # Title
        
        Concise Description
        
        ```python
        # Code Example
        ```
        
        Return ONLY the markdown content. Do not wrap in ```markdown blocks if possible, just raw text.
        """
        final_resp = chat.send_message(message=final_prompt)
        content = final_resp.text

        # Cleanup markdown fences
        if content.startswith("```markdown"):
            content = content.replace("```markdown", "", 1).rstrip("`")
        elif content.startswith("```"):
            content = content.replace("```", "", 1).rstrip("`")

        # Save to file
        kb_dir = pathlib.Path(__file__).parent / "knowledge_base"
        kb_dir.mkdir(parents=True, exist_ok=True)

        filename_safe = (
            "".join([c if c.isalnum() else "_" for c in topic]).strip("_") + ".md"
        )
        output_file = kb_dir / filename_safe

        output_file.write_text(content, encoding="utf-8")
        print(f"\nSuccess! Documentation saved to: {output_file}")
        print("You can edit this file manually to refine it.")

    except Exception as e:
        print(f"Error during interview: {e}")
