from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        if self.store.get_collection_size() == 0:
            return "Không có dữ liệu trong knowledge base để trả lời câu hỏi này."

        results = self.store.search(question, top_k=top_k)
        if not results:
            return "Không tìm thấy thông tin liên quan để trả lời câu hỏi này."

        context_blocks = []
        for index, result in enumerate(results, start=1):
            source = result["metadata"].get("doc_id") or result["metadata"].get("source") or "unknown"
            context_blocks.append(f"[{index}] (nguồn: {source}) {result['content']}")
        context = "\n\n".join(context_blocks)

        prompt = (
            "Bạn là trợ lý trả lời câu hỏi chỉ dựa trên ngữ cảnh được cung cấp dưới đây. "
            "Nếu ngữ cảnh không đủ thông tin để trả lời, hãy nói rõ là không tìm thấy thông tin. "
            "Khi trả lời, hãy trích dẫn số nguồn tương ứng, ví dụ [1].\n\n"
            f"Ngữ cảnh:\n{context}\n\n"
            f"Câu hỏi: {question}\n"
            "Trả lời:"
        )
        return self.llm_fn(prompt)
