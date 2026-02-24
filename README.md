# yt Agent Project

This project provides an agentic workflow for the `yt` volumetric data analysis library. It allows users to perform complex data analysis tasks using natural language queries, guided by a curated knowledge base of `yt` best practices.

## Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd yt-agent-project
    ```

2.  **Install dependencies:**
    This project uses `pyproject.toml`. You can install it in editable mode:

    ```bash
    pip install -e .
    ```

    _Note: You will need the `google-genai` and `yt` packages._

3.  **Set up your API Key:**
    The agent uses Google's Gemini models. You need to set your API key as an environment variable:
    ```bash
    export GOOGLE_API_KEY="your_api_key_here"
    ```

## Usage

### Interactive Mode

Start a chat session with the agent:

```bash
python main.py --interactive
```

### Single Query Execution

Run a specific query and immediately execute the generated code:

```bash
python main.py "Load snapshot_001.h5 and print the field list" --execute
```

## Training & Building the Knowledge Base

The agent's "brain" is a collection of Markdown files located in `yt_agent/knowledge_base/`. You can expand its capabilities by adding new topics, examples, and documentation.

### 1. Interactive Training

The easiest way to teach the agent a new concept is to use the interactive training mode. The agent will interview you about a topic and generate the documentation file for you.

```bash
python main.py --train
```

You will be prompted for:

- A filename (e.g., `phase_plots`)
- A title for the topic
- A description of the concept
- A code example

### 2. Ingesting Jupyter Notebooks

If you have existing `yt` analysis notebooks (`.ipynb`), you can automatically convert them into knowledge base entries. The tool extracts Markdown cells and Code cells to preserve the context and logic.

```bash
python main.py --ingest path/to/notebook.ipynb
```

You can also ingest multiple notebooks at once:

```bash
python main.py --ingest notebook1.ipynb notebook2.ipynb
```

### 3. Manual Addition

You can simply create new Markdown (`.md`) files in `yt_agent/knowledge_base/`.
Ensure they follow this structure for best results:

```markdown
# Topic Title

Explanation of the concept...

\`\`\`python
import yt

# Best practice code example

\`\`\`
```
