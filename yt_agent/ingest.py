import json
import pathlib
import argparse
import os
import sys

# Try to import genai to use for summarization
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


def analyze_and_summarize(notebook_content: str, client):
    """
    Asks the LLM to summarize the notebook and identify ambiguity.
    """
    model_name = "gemini-2.0-flash-001"
    prompt = f"""
    You are an expert developer for the 'yt' library. 
    Analyze the following Jupyter Notebook content (provided as JSON text).
    
    Your goal is to convert this into a concise, high-quality reference documentation file (Markdown).
    
    First, identifying the core concept.
    Second, identify any parts that are unclear, ambiguous, or where the code might be too specific to a local machine (e.g. hardcoded paths) and needs generalization.
    
    Output a JSON object with this structure:
    {{
        "summary": "Brief description of what this notebook teaches",
        "questions": ["List of clarifying questions to ask the author to improve the documentation", "Question 2..."]
    }}
    
    NOTEBOOK CONTENT:
    {notebook_content[:30000]}  # Truncate to avoid context limits if huge
    """

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        # Handle parsed response or raw text
        if hasattr(response, "parsed") and response.parsed:
            return response.parsed
        return json.loads(response.text)
    except Exception as e:
        print(f"LLM Analysis failed: {e}")
        return None


def generate_final_doc(notebook_content: str, user_answers: str, client):
    model_name = "gemini-2.0-flash-001"
    prompt = f"""
    You are an expert technical writer for the 'yt' library.
    Create a final Knowledge Base entry (Markdown) based on the original notebook and the user's clarifications.
    
    GUIDELINES:
    1. Be TERSE and CONCISE. Focus on the code patterns and "how-to".
    2. Remove conversational filler or verify basic steps unless critical.
    3. Generalize hardcoded paths (e.g., replace "/home/user/data/snap_001" with "ds = yt.load('snapshot_fn')").
    4. Use H1 for the Title.
    5. Ensure valid python code blocks.
    
    ORIGINAL NOTEBOOK CONTENT:
    {notebook_content[:30000]}
    
    USER CLARIFICATIONS:
    {user_answers}
    """

    try:
        response = client.models.generate_content(model=model_name, contents=prompt)
        return response.text
    except Exception as e:
        print(f"LLM Generation failed: {e}")
        return None


def ingest_notebook(
    notebook_path: pathlib.Path, output_dir: pathlib.Path, interactive: bool = True
):
    """
    Ingests a notebook, optionally querying the LLM to summarize/clarify content.
    If no LLM available or interactive=False, performs raw copy.
    """
    try:
        with open(notebook_path, "r", encoding="utf-8") as f:
            nb_data = json.load(f)
            nb_content = json.dumps(nb_data)  # Use string for LLM
    except Exception as e:
        print(f"Error reading {notebook_path}: {e}")
        return

    client = get_llm_client()

    if interactive and client:
        print(f"\n--- Analyzing {notebook_path.name} with AI ---")
        try:
            analysis = analyze_and_summarize(nb_content, client)

            if not analysis:
                print("Skipping AI analysis (failed). Falling back to raw copy.")
            else:
                print(f"\nSummary: {analysis.get('summary')}")
                questions = analysis.get("questions", [])

                user_answers_context = ""
                if questions:
                    print("\nI have some questions to make this documentation better:")
                    q_list = []
                    for i, q in enumerate(questions, 1):
                        ans = input(f"{i}. {q}\n>> ")
                        q_list.append(f"Q: {q}\nA: {ans}")
                    user_answers_context = "\n".join(q_list)

                print("\nGenerating concise documentation...")
                final_md = generate_final_doc(nb_content, user_answers_context, client)

                # Clean up markdown block markers
                if final_md:
                    if "```markdown" in final_md:
                        final_md = final_md.split("```markdown")[1].split("```")[0]
                    elif final_md.strip().startswith("```"):
                        final_md = final_md.strip().split("\n", 1)[1].rsplit("\n", 1)[0]

                    output_filename = notebook_path.stem + ".md"
                    output_path = output_dir / output_filename
                    output_path.write_text(final_md, encoding="utf-8")
                    print(f"Saved optimized docs to {output_path}")
                    return

        except Exception as e:
            print(f"LLM processing failed ({e}). Falling back to raw copy.")

    # Fallback to raw copy logic
    content_lines = []
    title = notebook_path.stem.replace("_", " ").title()
    content_lines.append(f"# {title} (Imported from Notebook)\n")

    for cell in nb_data.get("cells", []):
        cell_type = cell.get("cell_type")
        source = "".join(cell.get("source", []))

        if not source.strip():
            continue

        if cell_type == "markdown":
            content_lines.append(source)
            content_lines.append("\n")
        elif cell_type == "code":
            content_lines.append("```python")
            content_lines.append(source)
            content_lines.append("```\n")

    output_content = "\n".join(content_lines)
    output_filename = notebook_path.stem + ".md"
    output_path = output_dir / output_filename
    output_path.write_text(output_content, encoding="utf-8")
    print(f"Converted {notebook_path.name} -> {output_path}")
