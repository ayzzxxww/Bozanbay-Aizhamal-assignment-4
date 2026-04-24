# LangGraph pipeline for Telegram Channel Intelligence Analyzer
#
# Pipeline:
#   Node 1: ingest    — load posts from Telegram export file/folder
#   Node 2: classify  — LLM Call #1: classify each post (topic, sentiment, emotion…)
#   Node 3: report    — LLM Call #2: generate per-channel intelligence report
#   Node 4: export    — write results to Excel

import logging
from datetime import datetime
from typing import Dict, Any

from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

from models import PipelineState
from ingest import load_posts
from llm_functions import classify_post, generate_channel_report
from export import create_excel_report

load_dotenv()


# ============================================================================
# Node 1 — Ingest
# ============================================================================

def n_ingest(state: PipelineState) -> Dict[str, Any]:
    """Load posts from the provided Telegram export."""
    logging.info("[NODE: ingest] Loading posts from: %s", state.channels_file)

    raw_posts = load_posts(state.channels_file, max_posts_per_channel=30)

    total = sum(len(v) for v in raw_posts.values())
    logging.info("[NODE: ingest] Loaded %d posts across %d channel(s)", total, len(raw_posts))

    return {"raw_posts": raw_posts, "progress": 20}


# ============================================================================
# Node 2 — Classify posts  (LLM Call #1)
# ============================================================================

def n_classify(state: PipelineState) -> Dict[str, Any]:
    """Classify every post: topic, sentiment, emotion, breaking flag, keywords."""
    logging.info("[NODE: classify] Starting post classification")

    post_analyses: Dict[str, list] = {}

    for channel, posts in state.raw_posts.items():
        logging.info("[NODE: classify] Channel '%s' — %d posts", channel, len(posts))
        analyses = []
        for idx, post in enumerate(posts, 1):
            try:
                result = classify_post(post)
                analyses.append(result.model_dump())
                logging.debug("  [%d/%d] topic=%s sentiment=%s", idx, len(posts),
                              result.topic, result.sentiment)
            except Exception as e:
                logging.error("  [%d/%d] classification failed: %s", idx, len(posts), e)
                # Fallback — neutral unknown entry so we don't lose the post
                analyses.append({
                    "topic": "Other",
                    "sentiment": "Neutral",
                    "is_breaking": "No",
                    "emotion": "Neutral",
                    "keywords": "",
                })
        post_analyses[channel] = analyses

    total = sum(len(v) for v in post_analyses.values())
    logging.info("[NODE: classify] Classified %d posts total", total)

    return {"post_analyses": post_analyses, "progress": 60}


# ============================================================================
# Node 3 — Generate channel reports  (LLM Call #2)
# ============================================================================

def n_report(state: PipelineState) -> Dict[str, Any]:
    """Generate an aggregated intelligence report for each channel."""
    logging.info("[NODE: report] Generating channel reports")

    channel_reports: Dict[str, dict] = {}

    for channel, analyses in state.post_analyses.items():
        if not analyses:
            logging.warning("[NODE: report] No analyses for '%s', skipping", channel)
            continue
        try:
            report = generate_channel_report(channel, analyses)
            channel_reports[channel] = report.model_dump()
            logging.info("[NODE: report] '%s': mood=%s score=%s",
                         channel, report.overall_mood, report.mood_score)
        except Exception as e:
            logging.error("[NODE: report] Failed for '%s': %s", channel, e)

    return {"channel_reports": channel_reports, "progress": 85}


# ============================================================================
# Node 4 — Export to Excel
# ============================================================================

def n_export(state: PipelineState) -> Dict[str, Any]:
    """Write all results to a timestamped Excel file."""
    logging.info("[NODE: export] Creating Excel report")

    output_path = f"tg_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    create_excel_report(
        result_path=output_path,
        raw_posts=state.raw_posts,
        post_analyses=state.post_analyses,
        channel_reports=state.channel_reports,
    )

    logging.info("[NODE: export] Saved: %s", output_path)
    return {"result_path": output_path, "progress": 100}


# ============================================================================
# Graph builder
# ============================================================================

def build_graph():
    """
    Build and compile the LangGraph StateGraph.

    Structure:
        ingest → classify → report → export → END
    """
    graph = StateGraph(PipelineState)

    graph.add_node("ingest",   n_ingest)
    graph.add_node("classify", n_classify)
    graph.add_node("report",   n_report)
    graph.add_node("export",   n_export)

    graph.set_entry_point("ingest")
    graph.add_edge("ingest",   "classify")
    graph.add_edge("classify", "report")
    graph.add_edge("report",   "export")
    graph.add_edge("export",   END)

    logging.info("[GRAPH] Pipeline built: ingest → classify → report → export")
    return graph.compile()
