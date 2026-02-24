import argparse
import sys
import os
import pathlib

# Try importing local modules for training/ingestion
try:
    from yt_agent import train
    from yt_agent import ingest
except ImportError:
    train = None
    ingest = None

from yt_agent.agent import YtAgent


def main():
    parser = argparse.ArgumentParser(
        description="yt Agent CLI - Natural Language Data Analysis"
    )
    # Core function arguments
    parser.add_argument("query", nargs="?", help="Process a single query and exit.")
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Start an interactive session."
    )
    parser.add_argument(
        "--execute",
        "-x",
        action="store_true",
        help="Automatically execute generated code.",
    )

    # Knowledge Base arguments
    parser.add_argument(
        "--train",
        action="store_true",
        help="Launch interactive training mode to add knowledge.",
    )
    parser.add_argument(
        "--ingest",
        nargs="+",
        help="Ingest one or more .ipynb files into the knowledge base.",
    )

    args = parser.parse_args()

    # --- Mode: Interactive Training ---
    if args.train:
        if train:
            train.interview_mode()
        else:
            print("Error: train module not found.")
        return

    # --- Mode: Notebook Ingestion ---
    if args.ingest:
        if ingest:
            kb_dir = pathlib.Path(__file__).parent / "yt_agent" / "knowledge_base"
            kb_dir.mkdir(parents=True, exist_ok=True)
            for f_path in args.ingest:
                p = pathlib.Path(f_path)
                if p.exists() and p.suffix == ".ipynb":
                    print(f"Ingesting {p}...")
                    ingest.ingest_notebook(p, kb_dir)
                else:
                    print(f"Skipping {f_path}: File not found or not .ipynb")
        else:
            print("Error: ingest module not found.")
        return

    # --- Mode: Agent Execution (Standard) ---
    print("Initializing yt Agent...")
    try:
        agent = YtAgent(model_name="gemini-2.0-flash-001")
        print(
            f"Loaded knowledge base from: {agent.knowledge_base_dir if hasattr(agent, 'knowledge_base_dir') else 'local resources'}"
        )
    except Exception as e:
        print(f"Failed to initialize agent: {e}")
        return

    if args.query:
        agent.run(args.query, auto_execute=args.execute)
        return

    if args.interactive or not args.query:
        print("\n--- yt Agent Interactive Mode ---")
        print("Type your query (or 'exit' to quit).")
        while True:
            try:
                user_input = input("\n>> ")
                if user_input.lower() in ("exit", "quit"):
                    break

                agent.run(user_input, auto_execute=args.execute)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    main()
