import os
import pathlib
import json


def interview_mode():
    print("\n--- yt Agent Knowledge Base Builder ---")
    print("I will ask you a few questions to build a new topic for the agent.")

    topic_slug = input("Topic/Filename (e.g. 'phase_plots'): ").strip()
    if not topic_slug.endswith(".md"):
        topic_slug += ".md"

    title = input("Title of this topic (e.g. 'Creating Phase Plots'): ").strip()

    print("\nDescription (Enter your text, press Enter twice to finish):")
    description_lines = []
    while True:
        line = input()
        if not line:
            break
        description_lines.append(line)
    description = "\n".join(description_lines)

    print("\nCode Example (Enter code, press Enter twice to finish):")
    code_lines = []
    while True:
        line = input()
        if not line:
            break
        code_lines.append(line)
    code = "\n".join(code_lines)

    content = f"# {title}\n\n{description}\n\n```python\n{code}\n```\n"

    # Save to knowledge base
    kb_dir = pathlib.Path(__file__).parent / "knowledge_base"
    kb_dir.mkdir(parents=True, exist_ok=True)
    file_path = kb_dir / topic_slug

    print(f"\nPreview of {topic_slug}:\n")
    print("--------------------------------------------------")
    print(content)
    print("--------------------------------------------------")

    confirm = input("Save this file? (y/n): ").lower()
    if confirm == "y":
        file_path.write_text(content, encoding="utf-8")
        print(f"Saved to {file_path}")
    else:
        print("Discarded.")


if __name__ == "__main__":
    interview_mode()
