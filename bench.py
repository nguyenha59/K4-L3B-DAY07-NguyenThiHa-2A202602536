#!/usr/bin/env python3
"""Run the group's 5 gold-answer benchmark queries end to end and print a
comparable report to the terminal.

Why this script exists
-----------------------
Bai 3.1 / 3.4 in exercises.md ask each member to run the SAME 5 benchmark
queries on the SAME document set, but with their OWN chunking strategy, and
then compare results as a group. This script standardizes that run so every
member's output has the same shape (same table columns, same metrics) and can
be dropped side by side.

Usage
-----
    python bench.py
    python bench.py --strategy fixed_size --chunk-size 300 --overlap 50
    python bench.py --strategy by_sentences --max-sentences 4
    python bench.py --strategy recursive --chunk-size 500
    python bench.py --top-k 5

Embedding backend is selected the same way as main.py: set EMBEDDING_PROVIDER
in your .env (mock | local | openai | gemini). Defaults to mock if unset or
if the real backend fails to initialize (e.g. missing API key) -- this is
clearly printed so nobody mistakes mock-embedding numbers for real ones.

Each member should paste their own printed "SUMMARY" block (strategy, params,
hit-rate) into report/REPORT_NHOM.md section 2/3 for group comparison.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

# Make the repo root importable regardless of the current working directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Windows consoles often default stdout to a legacy codepage (e.g. cp1252)
# that cannot encode Vietnamese text; force UTF-8 so this always prints
# cleanly regardless of terminal (cmd.exe, PowerShell, git bash, piped file).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from dotenv import load_dotenv

from src.agent import KnowledgeBaseAgent
from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    GEMINI_EMBEDDING_MODEL,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    GeminiEmbedder,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)
from src.models import Document
from src.store import EmbeddingStore

DATA_DIR = Path(__file__).resolve().parent / "data" / "ecommerce"

# ---------------------------------------------------------------------------
# The group's 5 gold-answer benchmark queries (kept in sync with
# report/REPORT_NHOM.md section 3). expected_doc_id is used for an automatic,
# coarse "did we retrieve the right document" check; final relevance judgment
# for scoring (docs/SCORING.md) is still a human call based on the printed
# chunk content and gold answer.
# ---------------------------------------------------------------------------
BENCHMARK_QUERIES = [
    {
        "id": 1,
        "query": "Người mua có thể gửi yêu cầu trả hàng/hoàn tiền trong vòng bao lâu kể từ khi đơn hàng giao thành công?",
        "gold_answer": "Trong vòng 15 ngày kể từ lúc đơn hàng cập nhật giao thành công; riêng thực phẩm tươi sống/đông lạnh chỉ 24 giờ.",
        "expected_doc_id": "shopee-return-refund-policy",
        "metadata_filter": None,
    },
    {
        "id": 2,
        "query": "Sản phẩm được bảo hành miễn phí khi đáp ứng những điều kiện nào?",
        "gold_answer": "Lỗi kỹ thuật do nhà sản xuất; còn hạn bảo hành; có hóa đơn điện tử hoặc mã đơn hàng; với hàng điện gia dụng thì tem/phiếu bảo hành còn nguyên vẹn.",
        "expected_doc_id": "shopee-warranty-policy",
        "metadata_filter": None,
    },
    {
        "id": 3,
        "query": "Người bán vi phạm Chính sách cấm/hạn chế sản phẩm sẽ bị Shopee áp dụng những chế tài nào?",
        "gold_answer": "Xóa sản phẩm; giới hạn quyền tài khoản; đình chỉ/xóa tài khoản; cấn trừ số dư & phong tỏa quyền rút tiền; các chế tài pháp luật khác.",
        "expected_doc_id": "shopee-prohibited-products",
        # This is the query the assignment requires to need metadata filtering
        # (K4_VARIANT.md: metadata_filter={"audience": "buyer"|"seller"}):
        # "sản phẩm" / "tài khoản" appear across many buyer-facing docs too.
        "metadata_filter": {"audience": "seller"},
    },
    {
        "id": 4,
        "query": "Đơn hàng có giá trị hàng hóa bao nhiêu thì Shopee không hỗ trợ vận chuyển?",
        "gold_answer": "Trên 50.000.000 VNĐ (giá khuyến mãi nếu có, không gồm mã giảm giá/xu/phí vận chuyển).",
        "expected_doc_id": "shopee-shipping-policy",
        "metadata_filter": None,
    },
    {
        "id": 5,
        "query": "Người bán có phải chịu phí vận chuyển hoàn trả sản phẩm không, nếu đơn giao không thành công do lỗi của đơn vị vận chuyển?",
        "gold_answer": "Không. Điều 7.2: Người Bán không phải chịu phí vận chuyển hoàn trả khi đơn giao không thành công do lỗi của đơn vị vận chuyển (khác với Điều 7.1).",
        "expected_doc_id": "shopee-return-refund-policy",
        "metadata_filter": None,
    },
]

STRATEGIES = ("fixed_size", "by_sentences", "recursive")

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
FRONTMATTER_LINE_RE = re.compile(r'^([a-zA-Z0-9_]+):\s*"?([^"\n]*)"?\s*$')


def parse_frontmatter(raw_text: str) -> tuple[dict, str]:
    """Parse the simple `key: "value"` YAML frontmatter used in data/ecommerce/*.md.

    Deliberately dependency-free (no pyyaml) since requirements.txt only
    ships pytest + python-dotenv for the core lab.
    """
    match = FRONTMATTER_RE.match(raw_text)
    if not match:
        return {}, raw_text

    frontmatter_block, body = match.groups()
    metadata: dict[str, str] = {}
    for line in frontmatter_block.splitlines():
        line_match = FRONTMATTER_LINE_RE.match(line.strip())
        if line_match:
            key, value = line_match.groups()
            metadata[key] = value
    return metadata, body.strip()


def load_ecommerce_documents() -> list[dict]:
    """Load raw (doc_id, metadata, body_text) for every file in data/ecommerce/."""
    docs = []
    for path in sorted(DATA_DIR.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(raw)
        doc_id = metadata.get("doc_id", path.stem)
        docs.append({"doc_id": doc_id, "metadata": metadata, "body": body, "path": path})
    return docs


def build_chunker(strategy: str, args: argparse.Namespace):
    if strategy == "fixed_size":
        return FixedSizeChunker(chunk_size=args.chunk_size, overlap=args.overlap)
    if strategy == "by_sentences":
        return SentenceChunker(max_sentences_per_chunk=args.max_sentences)
    if strategy == "recursive":
        return RecursiveChunker(chunk_size=args.chunk_size)
    raise ValueError(f"Unknown strategy: {strategy}")


def resolve_embedder():
    """Same provider-selection logic as main.py, for consistent behavior."""
    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    if provider == "local":
        try:
            return LocalEmbedder(model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL)), provider
        except Exception as exc:
            print(f"[warn] LocalEmbedder failed to init ({exc}); falling back to mock.")
            return _mock_embed, "mock"
    if provider == "openai":
        try:
            return OpenAIEmbedder(model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL)), provider
        except Exception as exc:
            print(f"[warn] OpenAIEmbedder failed to init ({exc}); falling back to mock.")
            return _mock_embed, "mock"
    if provider == "gemini":
        try:
            return GeminiEmbedder(model_name=os.getenv("GEMINI_EMBEDDING_MODEL", GEMINI_EMBEDDING_MODEL)), provider
        except Exception as exc:
            print(f"[warn] GeminiEmbedder failed to init ({exc}); falling back to mock.")
            return _mock_embed, "mock"
    return _mock_embed, "mock"


def demo_llm(prompt: str) -> str:
    """Deterministic stand-in for a real LLM call (no API key wiring in this repo).

    Swap this for a real completion call (Anthropic/OpenAI/Gemini chat API) if
    your team has a key configured -- the KnowledgeBaseAgent only needs any
    Callable[[str], str].
    """
    preview = prompt[-260:].replace("\n", " ")
    return f"[DEMO LLM - not a real model] ...{preview}"


def print_baseline_comparison(all_text: str, chunk_size: int) -> None:
    from src.chunking import ChunkingStrategyComparator

    print("\n=== BASELINE: ChunkingStrategyComparator (all 8 docs concatenated) ===")
    print(f"{'strategy':<14} {'count':>7} {'avg_length':>12}")
    result = ChunkingStrategyComparator().compare(all_text, chunk_size=chunk_size)
    for name in STRATEGIES:
        stats = result[name]
        print(f"{name:<14} {stats['count']:>7} {stats['avg_length']:>12.1f}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--strategy", choices=STRATEGIES, default="recursive", help="Chunking strategy to benchmark (default: recursive)")
    parser.add_argument("--chunk-size", type=int, default=500, help="chunk_size for fixed_size/recursive (default: 500)")
    parser.add_argument("--overlap", type=int, default=50, help="overlap for fixed_size (default: 50)")
    parser.add_argument("--max-sentences", type=int, default=3, help="max_sentences_per_chunk for by_sentences (default: 3)")
    parser.add_argument("--top-k", type=int, default=3, help="top_k results per query (default: 3)")
    parser.add_argument("--member", default=os.getenv("USERNAME") or os.getenv("USER") or "unknown", help="Your name, printed in the summary so results are attributable")
    args = parser.parse_args()

    print("=" * 78)
    print("Day 7 Lab -- Group Benchmark Demo")
    print("=" * 78)
    print(f"Member       : {args.member}")
    print(f"Strategy     : {args.strategy}")
    if args.strategy in ("fixed_size", "recursive"):
        print(f"chunk_size   : {args.chunk_size}" + (f", overlap={args.overlap}" if args.strategy == "fixed_size" else ""))
    if args.strategy == "by_sentences":
        print(f"max_sentences: {args.max_sentences}")
    print(f"top_k        : {args.top_k}")

    raw_docs = load_ecommerce_documents()
    if not raw_docs:
        print(f"\n[error] No .md files found in {DATA_DIR}. Nothing to benchmark.")
        return 1
    print(f"\nLoaded {len(raw_docs)} source documents from {DATA_DIR}:")
    for d in raw_docs:
        print(f"  - {d['doc_id']} (category={d['metadata'].get('category')}, audience={d['metadata'].get('audience')}, {len(d['body'])} chars)")

    # Baseline comparison across all 3 built-in strategies (bai 3.1, buoc 1).
    all_text = "\n\n".join(d["body"] for d in raw_docs)
    print_baseline_comparison(all_text, args.chunk_size)

    # Chunk with the CHOSEN strategy and ingest into the store.
    chunker = build_chunker(args.strategy, args)
    embedder, provider_used = resolve_embedder()
    print(f"\nEmbedding backend: {getattr(embedder, '_backend_name', embedder.__class__.__name__)} ({provider_used})")
    if provider_used == "mock":
        print("[warn] Using MockEmbedder (hash-based, NOT semantically meaningful).")
        print("       Retrieval scores below are for pipeline sanity-checking only --")
        print("       set EMBEDDING_PROVIDER=local|openai|gemini in .env for real numbers.")

    store = EmbeddingStore(collection_name="benchmark_demo", embedding_fn=embedder)
    all_chunks: list[Document] = []
    for d in raw_docs:
        chunks = chunker.chunk(d["body"])
        for i, chunk_text in enumerate(chunks):
            chunk_metadata = dict(d["metadata"])
            chunk_metadata["doc_id"] = d["doc_id"]
            chunk_metadata["chunk_index"] = i
            all_chunks.append(Document(id=f"{d['doc_id']}__chunk{i}", content=chunk_text, metadata=chunk_metadata))
    store.add_documents(all_chunks)
    print(f"Ingested {store.get_collection_size()} chunks from {len(raw_docs)} documents ({args.strategy}).")

    agent = KnowledgeBaseAgent(store=store, llm_fn=demo_llm)

    print("\n" + "=" * 78)
    print("BENCHMARK QUERIES")
    print("=" * 78)

    hits_top1 = 0
    hits_top3 = 0
    per_query_latency_ms = []

    for item in BENCHMARK_QUERIES:
        print(f"\n--- Q{item['id']}: {item['query']}")
        print(f"    Gold answer : {item['gold_answer']}")
        if item["metadata_filter"]:
            print(f"    Metadata filter applied: {item['metadata_filter']}")

        start = time.perf_counter()
        if item["metadata_filter"]:
            results = store.search_with_filter(item["query"], top_k=args.top_k, metadata_filter=item["metadata_filter"])
        else:
            results = store.search(item["query"], top_k=args.top_k)
        elapsed_ms = (time.perf_counter() - start) * 1000
        per_query_latency_ms.append(elapsed_ms)

        retrieved_doc_ids = [r["metadata"].get("doc_id") for r in results]
        top1_hit = bool(retrieved_doc_ids) and retrieved_doc_ids[0] == item["expected_doc_id"]
        top3_hit = item["expected_doc_id"] in retrieved_doc_ids
        hits_top1 += int(top1_hit)
        hits_top3 += int(top3_hit)

        print(f"    Expected doc: {item['expected_doc_id']}  |  top-1 hit: {'YES' if top1_hit else 'no'}  |  top-{args.top_k} hit: {'YES' if top3_hit else 'no'}  |  {elapsed_ms:.1f} ms")
        for rank, r in enumerate(results, start=1):
            preview = r["content"][:100].replace("\n", " ")
            print(f"      [{rank}] score={r['score']:.4f} doc_id={r['metadata'].get('doc_id')} :: {preview}...")

        answer = agent.answer(item["query"], top_k=args.top_k)
        print(f"    Agent answer: {answer[:160].replace(chr(10), ' ')}...")

    n = len(BENCHMARK_QUERIES)
    print("\n" + "=" * 78)
    print("SUMMARY (paste this block into report/REPORT_NHOM.md for comparison)")
    print("=" * 78)
    print(f"member          : {args.member}")
    print(f"strategy        : {args.strategy}"
          + (f" (chunk_size={args.chunk_size}, overlap={args.overlap})" if args.strategy == "fixed_size" else "")
          + (f" (chunk_size={args.chunk_size})" if args.strategy == "recursive" else "")
          + (f" (max_sentences={args.max_sentences})" if args.strategy == "by_sentences" else ""))
    print(f"embedding       : {provider_used}")
    print(f"total_chunks    : {store.get_collection_size()}")
    print(f"top1_hit_rate   : {hits_top1}/{n}")
    print(f"top{args.top_k}_hit_rate   : {hits_top3}/{n}")
    print(f"avg_latency_ms  : {sum(per_query_latency_ms) / n:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
