"""
Summarization evaluation (backend env) — ZERO database writes.

Runs the PRODUCTION pipeline fully in-memory:
    cleaning → type detection → sliding-window hierarchical Map-Reduce
    → overview → structured extraction

Scores with:
    - ROUGE-1 / ROUGE-2 / ROUGE-L vs the human AMI reference summary
    - deterministic metrics (compression, number preservation, keyword coverage)
    - optional LLM judge

Usage:
    python eval_summarization.py <chunks.json> --name ami_1 \
        --reference-summary <ref.txt> [--no-judge]

Outputs (backend/eval_results/<name>/):
    summary_eval.json, generated_summary.txt, cleaned_transcript.txt
"""
import asyncio
import argparse
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, ".")

STOPWORDS = {
    "about", "because", "before", "being", "between", "could", "would",
    "should", "there", "these", "those", "which", "while", "where",
    "think", "really", "actually", "going", "gonna", "wanna", "right",
    "okay", "yeah", "um", "uh", "know", "like", "just", "that", "this",
    "with", "have", "from", "they", "them", "were", "what", "when",
}

JUDGE_SYSTEM = """You are an expert evaluation judge for meeting summarization systems.
You receive the full reference transcript of a meeting and a machine-generated summary.
Score the summary from 1 to 5 on each dimension:
- coverage: are the main discussion points, decisions and outcomes included?
- accuracy: is everything in the summary supported by the transcript (no hallucinations)?
- coherence: does it read as a clear, well-organized summary?
- conciseness: is it free of redundancy and unnecessary detail?
Output ONLY valid JSON:
{"coverage": 5, "accuracy": 4, "coherence": 5, "conciseness": 4, "notes": "one sentence"}"""


def tokenize_words(text: str) -> list:
    return re.findall(r"[a-z']+", text.lower())


def extract_numbers(text: str) -> set:
    return set(re.findall(r"\d+(?:[.,]\d+)?", text))


async def judge_summary(transcript: str, overview: str, structured: str) -> dict:
    from app.ai.ollama_client import ollama
    prompt = (
        f"REFERENCE TRANSCRIPT:\n{transcript}\n\n"
        f"GENERATED OVERVIEW:\n{overview}\n\n"
        f"GENERATED STRUCTURED FIELDS:\n{structured}\n\nScore now."
    )
    try:
        raw = await ollama.generate(prompt, system_prompt=JUDGE_SYSTEM)
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        return json.loads(m.group(0)) if m else {"error": raw[:200]}
    except Exception as e:
        return {"error": str(e)}


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("chunks")
    ap.add_argument("--name", required=True)
    ap.add_argument("--reference-summary", default=None)
    ap.add_argument("--no-judge", action="store_true")
    args = ap.parse_args()

    chunks = json.loads(Path(args.chunks).read_text())
    out_dir = Path("eval_results") / args.name
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── 1. In-memory cleaning (NO DB) ─────────────────────────────
    from app.services.cleaning import clean_chunks_in_memory
    chunks_data = [
        {"chunk_id": c["chunk_id"], "raw_text": c["raw_text"]} for c in chunks
    ]
    t0 = time.time()
    cleaned = await clean_chunks_in_memory(chunks_data)
    clean_s = round(time.time() - t0, 1)
    (out_dir / "cleaned_transcript.txt").write_text("\n\n".join(cleaned))

    # ── 2. In-memory summarization (NO DB) ────────────────────────
    from app.services.summarization.type_detector import detect_meeting_type
    from app.services.summarization.hierarchical import run_hierarchical
    from app.services.summarization.overview import generate_overview
    from app.services.summarization.extractor import extract_structured_info

    chunk_texts = [t for t in cleaned if t.strip()]
    t0 = time.time()
    meeting_type = await detect_meeting_type(chunk_texts[:3])
    reduced = await run_hierarchical(chunk_texts)
    overview = await generate_overview(reduced)
    extracted = await extract_structured_info(overview)
    summ_s = round(time.time() - t0, 1)

    structured_text = " ".join(
        extracted["key_topics"] + extracted["decisions"] + extracted["action_items"]
    )
    hypothesis = overview + " " + structured_text

    (out_dir / "generated_summary.txt").write_text(
        f"TYPE: {meeting_type}\n\nOVERVIEW:\n{overview}\n\n"
        "KEY TOPICS:\n" + "\n".join(f"- {t}" for t in extracted["key_topics"])
        + "\n\nDECISIONS:\n" + "\n".join(f"- {d}" for d in extracted["decisions"])
        + "\n\nACTION ITEMS:\n" + "\n".join(f"- {a}" for a in extracted["action_items"])
    )

    # ── 3. ROUGE vs human reference summary ───────────────────────
    rouge = None
    if args.reference_summary:
        from rouge_score import rouge_scorer
        reference = Path(args.reference_summary).read_text()
        scorer = rouge_scorer.RougeScorer(
            ["rouge1", "rouge2", "rougeL"], use_stemmer=True
        )
        s = scorer.score(reference, hypothesis)
        rouge = {
            k: {"precision": round(v.precision, 4),
                "recall": round(v.recall, 4),
                "fmeasure": round(v.fmeasure, 4)}
            for k, v in s.items()
        }

        # ── 4. Deterministic metrics vs transcript ────────────────────
    from app.services.cleaning.text_utils import strip_speaker_labels

    transcript_text = " ".join(chunk_texts)
    # Strip [speaker N] labels so label IDs don't pollute the metrics
    metrics_transcript = strip_speaker_labels(transcript_text)

    tr_tokens = tokenize_words(metrics_transcript)
    sm_tokens = tokenize_words(hypothesis)
    sm_set = set(sm_tokens)

    compression = round(len(sm_tokens) / max(1, len(tr_tokens)), 4)

    # Normalize number formatting ("12.50" == "1250")
    def norm_num(n: str) -> str:
        return n.replace(",", "").replace(".", "")

    tr_nums = {norm_num(n) for n in extract_numbers(metrics_transcript)}
    sm_nums = {norm_num(n) for n in extract_numbers(hypothesis)}
    number_preservation = round(len(tr_nums & sm_nums) / max(1, len(tr_nums)), 4)

    top_words = [
        w for w, _ in Counter(
            w for w in tr_tokens if len(w) > 4 and w not in STOPWORDS
        ).most_common(30)
    ]
    keyword_coverage = round(
        sum(1 for w in top_words if w in sm_set) / max(1, len(top_words)), 4
    )

    # ── 5. Optional LLM judge ─────────────────────────────────────
    judge = None
    if not args.no_judge:
        print("⚖️  Running LLM judge...")
        judge = await judge_summary(transcript_text, overview, structured_text)

    results = {
        "name": args.name,
        "meeting_type": meeting_type,
        "rouge": rouge,
        "metrics": {
            "compression_ratio": compression,
            "number_preservation": number_preservation,
            "keyword_coverage": keyword_coverage,
            "judge": judge,
        },
        "timings": {"cleaning_s": clean_s, "summarization_s": summ_s},
        "structure": {
            "key_topics": len(extracted["key_topics"]),
            "decisions": len(extracted["decisions"]),
            "action_items": len(extracted["action_items"]),
        },
        "overview": overview,
    }
    (out_dir / "summary_eval.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False)
    )

    print(f"\n{'=' * 60}")
    print(f"SUMMARY EVAL — {args.name}  (NO DB writes)")
    print(f"{'=' * 60}")
    if rouge:
        print(f"ROUGE-1 F: {rouge['rouge1']['fmeasure']:.3f} | "
              f"ROUGE-2 F: {rouge['rouge2']['fmeasure']:.3f} | "
              f"ROUGE-L F: {rouge['rougeL']['fmeasure']:.3f}")
    print(f"Compression: {compression:.2%} | Numbers: {number_preservation:.2%} "
          f"| Keywords: {keyword_coverage:.2%}")
    if judge:
        print(f"Judge: {judge}")
    print(f"Cleaning: {clean_s}s | Summarization: {summ_s}s")
    print(f"\nOverview:\n  {overview}\n")
    print(f"💾 Saved to {out_dir}/")


if __name__ == "__main__":
    asyncio.run(main())