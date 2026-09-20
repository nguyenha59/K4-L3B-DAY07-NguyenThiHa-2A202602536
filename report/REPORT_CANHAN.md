# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Thị Hạ
**Nhóm:** 3in1
**Ngày:** 2026-09-20

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Nghĩa là hai vector embedding chỉ gần như cùng một hướng trong không gian nhiều chiều. Model đang coi hai câu đó nói cùng một ý, dù chữ dùng có khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Người mua có thể yêu cầu trả hàng trong vòng 15 ngày kể từ khi nhận được sản phẩm."
- Câu B: "Trong 15 ngày sau khi nhận hàng, khách hàng được phép gửi yêu cầu hoàn trả sản phẩm."
- Tại sao tương đồng: viết khác nhau nhưng cùng 1 ý (ai, làm gì, trong bao lâu). Chạy `compute_similarity()` thật ra được **0.8123** (bảng ở mục 4), khá khớp với dự đoán.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Shopee áp dụng chính sách bảo hành cho sản phẩm điện gia dụng."
- Câu B: "Hôm nay thời tiết Hà Nội rất đẹp và mát mẻ."
- Tại sao khác: hai câu không liên quan gì đến nhau. Đo được **0.1829**, gần 0 đúng như mong đợi.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Vì cosine chỉ nhìn vào hướng của vector, không quan tâm độ dài của nó. Euclidean thì ngược lại, bị ảnh hưởng bởi magnitude — mà hai câu dài ngắn khác nhau vẫn có thể cùng nghĩa, nên nếu dùng Euclidean dễ bị đánh giá sai là "khác nhau" chỉ vì độ dài văn bản khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> `ceil((10000 - 50) / (500 - 50))` = `ceil(9950/450)` = `ceil(22.11)` = **23 chunks**.
> Kiểm tra lại bằng cách chạy thật `FixedSizeChunker(chunk_size=500, overlap=50).chunk("a"*10000)` trong `src/chunking.py`, ra đúng 23 phần tử nên công thức đúng.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Tính lại: `ceil((10000-100)/(500-100))` = `ceil(9900/400)` = `ceil(24.75)` = **25 chunks** (cũng đã chạy code kiểm tra, đúng 25). Tăng từ 23 lên 25 vì bước nhảy `step = chunk_size - overlap` nhỏ đi nên cần nhiều chunk hơn mới phủ hết tài liệu. Muốn overlap lớn hơn vì tránh trường hợp một câu quan trọng bị cắt đúng vào ranh giới giữa 2 chunk — overlap giúp nội dung cuối chunk này lặp lại ở đầu chunk sau, đỡ mất ý khi retrieval. Đánh đổi là tốn thêm chunk để lưu/tính.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Mình dùng regex `re.split(r"(?<=[.!?])\s+", text.strip())`. Lookbehind để giữ lại dấu câu trong câu vừa tách, không bị mất `.`/`!`/`?`. Sau khi split thì lọc bỏ mấy chuỗi rỗng (`if s.strip()`), vì văn bản có nhiều dòng trống hoặc dấu câu lặp thì split ra sẽ có phần tử rỗng. Cuối cùng gom mỗi `max_sentences_per_chunk` câu lại thành 1 chunk bằng cách slice theo `step`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thử lần lượt từng separator theo thứ tự ưu tiên: `\n\n`, `\n`, `. `, `" "`, `""`. Tách xong thì gộp các phần nhỏ lại gần chunk_size để đỡ vụn, phần nào vẫn dài quá thì đệ quy xuống separator tiếp theo. 2 base case: nếu đoạn text đã đủ ngắn thì trả về luôn, không tách nữa; còn nếu hết separator để thử thì cắt cứng theo ký tự — chỗ này mình gọi lại `FixedSizeChunker(overlap=0)` để không phải viết lại logic cắt.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `add_documents` cho từng `Document` qua `_make_record()`: nhúng nội dung bằng `embedding_fn`, lưu 1 dict `{id, content, metadata, embedding}` vào list `self._store`. `metadata` luôn có thêm `doc_id` để sau này `delete_document` với lọc dùng được. `search` thì nhúng câu hỏi, tính dot product với từng vector đã lưu (không chuẩn hóa lại norm vì embedding đầu vào coi như đã gần chuẩn), sort giảm dần theo score rồi lấy `top_k` đầu.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Lọc trước rồi mới search — duyệt `self._store`, giữ lại record nào khớp hết các cặp key/value trong `metadata_filter`, sau đó mới chạy similarity trên tập đã thu hẹp. Vừa đúng yêu cầu đề bài vừa giảm bớt số lần tính similarity không cần thiết. `delete_document` thì đơn giản hơn: build lại `self._store` chỉ giữ record có `doc_id` khác cái cần xóa, so sánh size trước/sau để biết có xóa được gì không.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Đầu tiên check nếu store rỗng hoặc search không ra gì thì trả lời luôn "không có dữ liệu", tránh gọi LLM không cần thiết. Sau đó ghép các chunk top-k lại, đánh số `[1] (nguồn: doc_id) ...` rồi nối bằng `\n\n`, đưa vào prompt yêu cầu LLM chỉ trả lời dựa trên context, nói rõ nếu không đủ thông tin, và trích số nguồn khi trả lời. Đây là pattern RAG chuẩn: retrieve → build prompt → generate, giúp câu trả lời còn lần ngược lại được chunk gốc.

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

> Chạy bằng `python similarity_predictions.py` — embedding backend `text-embedding-3-small` (OpenAI), dự đoán được ghi **trước khi chạy script** (xem comment trong `similarity_predictions.py`).

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Người mua có thể yêu cầu trả hàng trong vòng 15 ngày kể từ khi nhận được sản phẩm." | "Trong 15 ngày sau khi nhận hàng, khách hàng được phép gửi yêu cầu hoàn trả sản phẩm." | cao (paraphrase cùng nghĩa) | 0.8123 | ✅ Đúng |
| 2 | "Người bán phải chịu chi phí vận chuyển khi hoàn trả sản phẩm." | "Người bán không phải chịu bất kỳ chi phí vận chuyển nào khi hoàn trả sản phẩm." | thấp (trái nghĩa có/không) | 0.8520 | ❌ **Sai** — thực tế lại rất cao |
| 3 | "Shopee áp dụng chính sách bảo hành cho sản phẩm điện gia dụng." | "Hôm nay thời tiết Hà Nội rất đẹp và mát mẻ." | thấp (khác chủ đề hoàn toàn) | 0.1829 | ✅ Đúng |
| 4 | "Đơn hàng có giá trị trên 50 triệu đồng sẽ không được Shopee hỗ trợ vận chuyển." | "Chi phí vận chuyển được Shopee tính dựa trên trọng lượng và kích thước gói hàng." | cao (cùng chủ đề vận chuyển) | 0.6448 | ✅ Đúng |
| 5 | "Sản phẩm bị lỗi kỹ thuật do nhà sản xuất sẽ được bảo hành miễn phí." | (câu giống hệt câu A) | cao (sanity check, kỳ vọng ~1.0) | 1.0000 | ✅ Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 2. Đoán thấp vì hai câu trái nghĩa, nhưng đo ra 0.8520 — cao ngang cặp đồng nghĩa (0.8123). Có thể do embedding bắt chủ đề/từ vựng là chính, chữ "không" không đủ sức kéo vector đi xa. Liên quan tới lỗi câu 5 ở mục dưới — Điều 7.1 và 7.2 chỉ khác từ phủ định mà agent lấy nhầm.

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
| 5 | Người bán có chịu phí hoàn trả khi lỗi đơn vị vận chuyển? | "Tuy nhiên, Người Bán phải gửi khiếu nại đến đơn vị vận chuyển chịu trách nhiệm..." (`shopee-shipping-policy`, sai tài liệu kỳ vọng) | 0.6658 | Không liên quan — lấy nhầm `shopee-shipping-policy` thay vì đúng Điều 7.1/7.2 của `shopee-return-refund-policy`. Hạng 3 tuy đúng tài liệu nhưng là Điều 3.1, vẫn không phải Điều 7 | Agent trả lời sai hướng vì context không có đúng đoạn — ca lỗi thật, nói thêm ở dưới |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** Mình tính là 4/5, không phải 5/5. Script tự động chấm câu 5 là "top-3 hit: YES" nhưng đó chỉ vì nó so khớp `doc_id` thôi, chứ đọc kỹ nội dung chunk thì không liên quan. Chấm tự động kiểu này có giới hạn, phải đọc lại tay như bảng trên mới biết đúng sai.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác:**
> Nhóm không demo trực tiếp nên so bằng số liệu benchmark của từng người. Giang dùng cùng `RecursiveChunker`/500 như mình, chỉ khác embedding (mình OpenAI, Giang sentence-transformers local) — top-1 lệch hẳn (4/5 vs 2/5), top-3 thì gần bằng. Trước giờ cứ nghĩ chunking mới là yếu tố chính, giờ mới thấy embedding ảnh hưởng không kém. Thêm số liệu của Thu (`HeadingChunker` + mock embedding, top-1 = 0/5) càng rõ: so sánh chunking mà không cố định embedding thì dễ quy nhầm nguyên nhân sang chiến lược chunking.

---

## Tự Đánh Giá (Phần Cá Nhân)

> Tự chấm theo đúng tiêu chí `docs/SCORING.md` — mục "Kết quả Truy xuất" dùng thang 2đ/câu (2 = top-3 có chunk liên quan + agent trả lời đúng; 1 = có liên quan nhưng thiếu chi tiết/không ở top-1; 0 = không truy xuất được trong top-3) áp cho 5 câu ở mục 5: Q1=2, Q2=1 (đúng tài liệu nhưng thiếu chi tiết 4 điều kiện), Q3=2, Q4=2, Q5=0 (sai tài liệu ở top-1, nội dung top-3 không liên quan dù trùng `doc_id`) → 7/10.

| Tiêu chí | Điểm tự đánh giá | Lý do |
|----------|-------------------|-------|
| Khởi động (Warm-up) | 5 / 5 | Trả lời đủ cả cosine similarity (có ví dụ đo thật) và toán chunking (đã verify bằng code, không chỉ tính tay) |
| Hướng tiếp cận của tôi (My Approach) | 9 / 10 | Giải thích đúng thuật toán thật của từng hàm (regex, base case đệ quy, pre-filter…), trừ 1đ vì chưa có ví dụ code cụ thể minh họa |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 | `pytest tests/ -v` → 42/42 PASSED |
| Dự đoán độ tương tự (Similarity Predictions) | 4 / 5 | Dự đoán sai 1/5 cặp (cặp 2 — câu trái nghĩa nhưng embedding vẫn cho similarity cao), nhưng phản tư nêu đúng nguyên nhân (embedding không hiểu phủ định) và nối được với ca lỗi thật ở mục 5 |
| Kết quả truy xuất của tôi (Competition Results) | 7 / 10 | Theo thang 2đ/câu của `docs/SCORING.md`: Q1=2, Q2=1, Q3=2, Q4=2, Q5=0 |
| **Tổng phần cá nhân** | **55 / 60** | |
