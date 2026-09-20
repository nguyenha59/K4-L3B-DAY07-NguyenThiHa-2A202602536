#!/usr/bin/env python3
"""Bai 1.1 / 3.3 -- compute_similarity() on 5 sentence pairs with a real
embedding backend (same EMBEDDING_PROVIDER selection as main.py / bench.py).

Predictions below were written BEFORE running this script (see comments) --
that is the point of the exercise: compare your intuition to the actual
cosine similarity score.

Usage: python similarity_predictions.py
"""
from __future__ import annotations

import os
import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from dotenv import load_dotenv

from src.chunking import compute_similarity
from src.embeddings import EMBEDDING_PROVIDER_ENV, OPENAI_EMBEDDING_MODEL, OpenAIEmbedder, _mock_embed

load_dotenv(override=False)
provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
if provider == "openai":
    embedder = OpenAIEmbedder(model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL))
else:
    embedder = _mock_embed

print(f"Embedding backend: {getattr(embedder, '_backend_name', embedder.__class__.__name__)} ({provider})\n")

# (sentence_a, sentence_b, my prediction written BEFORE running: "cao" | "thap")
PAIRS = [
    (
        "Người mua có thể yêu cầu trả hàng trong vòng 15 ngày kể từ khi nhận được sản phẩm.",
        "Trong 15 ngày sau khi nhận hàng, khách hàng được phép gửi yêu cầu hoàn trả sản phẩm.",
        "cao",  # paraphrase cùng nghĩa
    ),
    (
        "Người bán phải chịu chi phí vận chuyển khi hoàn trả sản phẩm.",
        "Người bán không phải chịu bất kỳ chi phí vận chuyển nào khi hoàn trả sản phẩm.",
        "thap",  # trái nghĩa nhau (có/không) -> dự đoán thấp vì ý nghĩa đối lập
    ),
    (
        "Shopee áp dụng chính sách bảo hành cho sản phẩm điện gia dụng.",
        "Hôm nay thời tiết Hà Nội rất đẹp và mát mẻ.",
        "thap",  # khác chủ đề hoàn toàn
    ),
    (
        "Đơn hàng có giá trị trên 50 triệu đồng sẽ không được Shopee hỗ trợ vận chuyển.",
        "Chi phí vận chuyển được Shopee tính dựa trên trọng lượng và kích thước gói hàng.",
        "cao",  # cùng chủ đề vận chuyển nhưng nội dung cụ thể khác nhau
    ),
    (
        "Sản phẩm bị lỗi kỹ thuật do nhà sản xuất sẽ được bảo hành miễn phí.",
        "Sản phẩm bị lỗi kỹ thuật do nhà sản xuất sẽ được bảo hành miễn phí.",
        "cao",  # câu giống hệt nhau -> sanity check, kỳ vọng gần 1.0
    ),
]

print(f"{'#':<3}{'Dự đoán':<10}{'Điểm thực tế':<15}{'Đúng?':<8}Câu A / Câu B")
for i, (a, b, prediction) in enumerate(PAIRS, start=1):
    score = compute_similarity(embedder(a), embedder(b))
    bucket = "cao" if score >= 0.5 else "thap"
    correct = "yes" if bucket == prediction else "NO"
    print(f"{i:<3}{prediction:<10}{score:<15.4f}{correct:<8}A: {a}")
    print(f"{'':<28}B: {b}")
