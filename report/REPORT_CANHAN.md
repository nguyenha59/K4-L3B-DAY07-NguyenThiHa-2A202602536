# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [Tên sinh viên]
**Nhóm:** [Tên nhóm]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> *Viết 1-2 câu:*

**Ví dụ có độ tương tự CAO:**
- Câu A:
- Câu B:
- Tại sao tương đồng:

**Ví dụ có độ tương tự THẤP:**
- Câu A:
- Câu B:
- Tại sao khác:

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> *Viết 1-2 câu:*

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> *Đáp án:*

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Viết 1-2 câu:*

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> *Viết 2-3 câu: dùng biểu thức chính quy (regex) gì để phát hiện câu? Xử lý trường hợp ngoại lệ (edge case) nào?*

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> *Viết 2-3 câu: thuật toán hoạt động thế nào? Base case (trường hợp cơ sở) là gì?*

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> *Viết 2-3 câu: lưu trữ thế nào? Tính độ tương tự ra sao?*

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> *Viết 2-3 câu: lọc (filter) trước hay sau? Xóa bằng cách nào?*

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> *Viết 2-3 câu: cấu trúc prompt? Cách đưa ngữ cảnh (inject context) vào thế nào?*

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
platform win32 -- Python 3.11.8, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\Admin\AppData\Local\Programs\Python\Python311\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\Admin\K4-L3B-DAY07-NguyenThiHa-2A202602536
plugins: anyio-4.9.0
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                    [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                             [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                      [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                       [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                            [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED            [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                  [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                   [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                 [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                   [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                              [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                          [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED           [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED               [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED         [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED               [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                     [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                       [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                             [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                  [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                    [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED        [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                     [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                              [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                             [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                        [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                    [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED               [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                   [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                         [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                   [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED              [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED             [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED            [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED     [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

42 passed
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | | | cao / thấp | | |
| 2 | | | cao / thấp | | |
| 3 | | | cao / thấp | | |
| 4 | | | cao / thấp | | |
| 5 | | | cao / thấp | | |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Viết 2-3 câu:*

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

**Cách chạy:** `python bench.py --strategy recursive --chunk-size 500 --member "Nguyen Thi Ha"` — embedding backend `text-embedding-3-small` (OpenAI), `EMBEDDING_PROVIDER=openai` trong `.env`. Toàn bộ output đã lưu ở `ket_qua_benchmark.txt`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thời hạn gửi yêu cầu trả hàng/hoàn tiền? | "3.2. Người Mua có thể gửi yêu cầu trả hàng/hoàn tiền trong vòng 15 (mười lăm) ngày kể từ lúc đơn hàng..." (`shopee-return-refund-policy`) | 0.7887 | Có — đúng chunk chứa đáp án | [DEMO LLM] chỉ preview prompt, không phải LLM thật — nhưng context đưa vào đúng |
| 2 | Điều kiện bảo hành miễn phí? | "# Chính sách bảo hành sản phẩm * Chỉ áp dụng cho ngành hàng..." (`shopee-warranty-policy`) | 0.6648 | Có — đúng tài liệu, chunk đầu tài liệu (còn thiếu phần liệt kê chi tiết 4 điều kiện, nằm ở chunk khác cũng lọt top-3) | (tương tự, demo LLM) |
| 3 | Chế tài khi vi phạm sản phẩm cấm/hạn chế? | "# Chính sách cấm hạn chế sản phẩm 1. ĐỐI TƯỢNG ÁP DỤNG..." (`shopee-prohibited-products`, có lọc `audience: seller`) | 0.7549 | Có — đúng tài liệu; lọc metadata giúp loại hẳn các tài liệu buyer-facing khỏi kết quả | (tương tự) |
| 4 | Ngưỡng giá trị đơn hàng không hỗ trợ vận chuyển? | "d. Đơn hàng có giá trị hàng hóa lớn hơn 50.000.000VNĐ..." (`shopee-shipping-policy`) | 0.7171 | Có — trúng đúng câu chứa số liệu | (tương tự) |
| 5 | Người bán có chịu phí hoàn trả khi lỗi đơn vị vận chuyển? | "Tuy nhiên, Người Bán phải gửi khiếu nại đến đơn vị vận chuyển chịu trách nhiệm..." (`shopee-shipping-policy`, SAI tài liệu kỳ vọng) | 0.6658 | **Không thực sự liên quan** — lấy nhầm `shopee-shipping-policy` (nói về khiếu nại vận chuyển) thay vì đúng Điều 7.1/7.2 của `shopee-return-refund-policy`; hạng 3 tuy đúng tài liệu nhưng lại là đoạn Điều 3.1 (điều kiện trả hàng chung), không phải Điều 7 | Agent trả lời sai hướng vì context không có đúng đoạn — đây là ca lỗi thật, đưa vào Bài 3.5 (Phân Tích Lỗi) |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 4 / 5 (câu 5 tính theo đúng nội dung chunk là KHÔNG liên quan, dù script tự động chấm "top-3 hit: YES" vì chỉ so khớp `doc_id`, không so khớp đúng đoạn/Điều — đây là giới hạn của cách chấm tự động, cần đọc thủ công nội dung chunk như bảng trên).

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu — cần chờ demo với các thành viên khác để điền phần này.*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | / 5 |
| Hướng tiếp cận của tôi (My Approach) | / 10 |
| Hoàn thiện code (Core Implementation — tests) | / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | / 5 |
| Kết quả truy xuất của tôi (Competition Results) | / 10 |
| **Tổng phần cá nhân** | **/ 60** |
