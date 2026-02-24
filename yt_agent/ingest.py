import json
import pathlib
import argparse


def ingest_notebook(notebook_path: pathlib.Path, output_dir: pathlib.Path):
    try:
        with open(notebook_path, "r", encoding="utf-8") as f:
            nb = json.load(f)
    except Exception as e:
        print(f"Error reading {notebook_path}: {e}")
        return

    content_lines = []

    # Heuristic: Use the filename as the title if no H1 is found
    title = notebook_path.stem.replace("_", " ").title()
    content_lines.append(f"# {title} (Imported from Notebook)\n")

    for cell in nb.get("cells", []):
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


def main():
    parser = argparse.ArgumentParser(
        description="Ingest Jupyter Notebooks into yt-agent knowledge base."
    )
    parser.add_argument(
        "files", nargs="+", type=pathlib.Path, help="Notebook files to ingest"
    )

    args = parser.parse_args()

    kb_dir = pathlib.Path(__file__).parent / "knowledge_base"
    kb_dir.mkdir(parents=True, exist_ok=True)

    for f in args.files:
        if f.suffix == ".ipynb" and f.exists():
            ingest_notebook(f, kb_dir)
        else:
            print(f"Skipping {f} (not a .ipynb file or does not exist)")


if __name__ == "__main__":
    main()
