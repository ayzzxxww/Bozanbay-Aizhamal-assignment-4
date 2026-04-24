# Telegram Channel Intelligence Analyzer
# Main entry point with LangSmith tracing

import os
import sys
import logging
from dotenv import load_dotenv
from langchain_core.tracers import LangChainTracer

#from models import PipelineState
from graph import build_graph

load_dotenv()

# LangSmith tracing (optional — set in .env)
os.environ["LANGCHAIN_TRACING_V2"]  = os.getenv("LANGSMITH_TRACING", "false")
os.environ["LANGCHAIN_ENDPOINT"]    = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
os.environ["LANGCHAIN_API_KEY"]     = os.getenv("LANGSMITH_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"]     = os.getenv("LANGSMITH_PROJECT", "tg-channel-analyzer")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)


def run_pipeline(channels_file: str) -> dict:
    logging.info("=" * 60)
    logging.info("Telegram Channel Intelligence Analyzer")
    logging.info("=" * 60)
    logging.info("Input: %s", channels_file)

    graph = build_graph()

    callbacks = []
    if os.getenv("LANGSMITH_API_KEY"):
        callbacks.append(LangChainTracer(project_name=os.getenv("LANGSMITH_PROJECT", "tg-channel-analyzer")))

    result = graph.invoke(
        PipelineState(channels_file=channels_file),
        config={"callbacks": callbacks},
    )
    return result


def log_results(result: dict):
    logging.info("")
    logging.info("── Results ──────────────────────────────────────")
    logging.info("Channels analysed : %d", len(result.get("channel_reports", {})))
    logging.info("Posts processed   : %d",
                 sum(len(v) for v in result.get("post_analyses", {}).values()))
    logging.info("Report saved to   : %s", result.get("result_path", "N/A"))
    logging.info("")
    for ch, report in result.get("channel_reports", {}).items():
        logging.info("  [%s]  mood=%s (%s)  top_topic=%s",
                     ch, report.get("overall_mood"), report.get("mood_score"),
                     report.get("top_topic"))


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <channels_file_or_folder>")
        print("")
        print("Accepted inputs:")
        print("  posts.txt          — plain text, channels separated by === @name ===")
        print("  result.json        — Telegram Desktop JSON export")
        print("  result.html        — Telegram Desktop HTML export")
        print("  ./export_folder/   — Telegram Desktop export directory")
        sys.exit(1)

    if not os.getenv("GEMINI_API_KEY"):
        logging.error("GEMINI_API_KEY not set. Add it to your .env file.")
        sys.exit(1)

    try:
        result = run_pipeline(sys.argv[1])
        log_results(result)
    except Exception as e:
        logging.exception("Pipeline failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
