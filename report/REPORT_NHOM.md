# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Tên nhóm]
**Thành viên:** [Họ tên từng thành viên]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** [ví dụ: Customer support FAQ, Luật Việt Nam, công thức nấu ăn, ...]

**Tại sao nhóm chọn chủ đề này?**
> *Viết 2-3 câu:*

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [ ] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [ ] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `shopee-return-refund-policy` | Định danh duy nhất cho tài liệu gốc; dùng để nhóm các chunk cùng 1 tài liệu và để `delete_document()` xóa đúng bộ chunk. |
| `category` | string (enum) | `returns-policy`, `warranty-policy`, `seller-rules`, `shipping-policy`, `platform-regulation` | Lọc trước khi search (`search_with_filter`) để tránh nhầm giữa các chủ đề có từ khóa trùng lặp (vd: "sản phẩm", "tài khoản" xuất hiện ở nhiều tài liệu) — chính là trường dùng cho câu hỏi 3 cần metadata filter. |
| `audience` | string (enum) | `buyer`, `seller`, `both` | Phân biệt tài liệu dành cho người mua hay người bán — hữu ích khi câu hỏi chỉ liên quan tới một phía (vd: nghĩa vụ của Người Bán). |
| `language` | string | `vi` | Cho phép mở rộng lọc theo ngôn ngữ nếu sau này nhóm thêm tài liệu tiếng Anh. |
| `source_url` | string (URL) | `https://help.shopee.vn/portal/4/article/77251` | Trích dẫn nguồn khi agent trả lời, và để kiểm tra lại tính chính xác của gold answer. |
| `retrieved_at` | date (ISO) | `2026-09-20` | Biết dữ liệu được lấy khi nào — quan trọng vì chính sách TMĐT có thể thay đổi thường xuyên. |
| `document_version` | string (ngày hiệu lực) | `2026-03-04` hoặc `not-stated` | Kiểm tra độ mới; nếu 2 tài liệu mâu thuẫn nhau thì ưu tiên bản có `document_version` mới hơn. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` (chunk_size=500) trên 3 tài liệu đại diện cho 3 category khác nhau — số liệu chạy thật, không phải ước lượng:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `shopee-return-refund-policy.md` (19.410 ký tự) | FixedSizeChunker (`fixed_size`) | 49 | 494.1 | Kém — cắt cứng theo ký tự, dễ cắt ngang giữa các Điều/mục (vd: đứt giữa Điều 7.1 và 7.2). |
| `shopee-return-refund-policy.md` | SentenceChunker (`by_sentences`) | 47 | 410.1 | Trung bình — giữ nguyên câu nhưng nhóm 3 câu bất kỳ, không theo cấu trúc Điều/khoản nên vẫn có thể tách rời 2 điều khoản liên quan. |
| `shopee-return-refund-policy.md` | RecursiveChunker (`recursive`) | 60 | 321.6 | Tốt nhất — ưu tiên tách theo `\n\n`/`\n` nên thường giữ trọn 1 Điều/mục trong 1 chunk (đúng như quan sát ở câu hỏi 5: Điều 7.1/7.2 nằm liền kề nhau trong văn bản gốc). |
| `shopee-warranty-policy.md` (3.132 ký tự) | FixedSizeChunker (`fixed_size`) | 8 | 479.0 | Kém — tài liệu ngắn nhưng vẫn có nguy cơ cắt giữa danh sách điều kiện bảo hành. |
| `shopee-warranty-policy.md` | SentenceChunker (`by_sentences`) | 5 | 624.0 | Tốt — tài liệu ngắn, gộp 3 câu/chunk vẫn giữ được cả đoạn "Điều kiện bảo hành". |
| `shopee-warranty-policy.md` | RecursiveChunker (`recursive`) | 7 | 445.7 | Tốt — chunk ngắn hơn nhưng vẫn theo ranh giới đoạn văn tự nhiên. |
| `shopee-shipping-policy.md` (24.406 ký tự) | FixedSizeChunker (`fixed_size`) | 61 | 498.5 | Kém — tài liệu dài, nhiều danh sách con (a, b, c...), dễ bị cắt giữa danh sách. |
| `shopee-shipping-policy.md` | SentenceChunker (`by_sentences`) | 64 | 375.9 | Trung bình — văn bản luật ít dấu chấm câu rõ ràng trong danh sách gạch đầu dòng nên việc tách câu kém chính xác hơn. |
| `shopee-shipping-policy.md` | RecursiveChunker (`recursive`) | 67 | 362.3 | Tốt nhất — vẫn bám theo cấu trúc đoạn/mục dù tài liệu dài và nhiều tầng danh sách con. |

**Nhận xét chung:** `RecursiveChunker` luôn cho chunk ngắn hơn (avg_length thấp hơn ~15-30%) nhưng giữ ngữ cảnh tốt hơn rõ rệt trên cả 3 tài liệu vì văn bản pháp lý/chính sách Shopee có cấu trúc phân đoạn rõ (`\n\n` giữa các Điều, `\n` giữa các mục con) — đây là lý do nhóm chọn `RecursiveChunker` làm chiến lược mặc định cho toàn bộ pipeline benchmark (`scripts/run_benchmark_demo.py`).

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Nguyễn Thị Hà**
- **Loại chiến lược:** Recursive (`RecursiveChunker`, `chunk_size=500`, separators mặc định `["\n\n", "\n", ". ", " ", ""]`)
- **Mô tả & lý do chọn cho chủ đề này:** Văn bản chính sách Shopee có cấu trúc phân đoạn rõ ràng (mỗi Điều/khoản cách nhau bằng dòng trống, mỗi mục con xuống dòng riêng), nên `RecursiveChunker` tận dụng đúng ranh giới đó để giữ trọn 1 Điều/khoản trong 1 chunk thay vì cắt cứng theo ký tự như `FixedSizeChunker`. Bảng baseline ở trên cho thấy recursive giữ ngữ cảnh tốt nhất trên cả 3 tài liệu thử nghiệm, đặc biệt quan trọng với câu hỏi 5 (cần phân biệt đúng Điều 7.1 vs 7.2 nằm sát nhau).
- **Cách chạy để tái lập:** `python scripts/run_benchmark_demo.py --strategy recursive --chunk-size 500 --member "Nguyễn Thị Hà"`
- **Code snippet (nếu custom):** Không dùng custom chunker cho lần thử này — dùng `RecursiveChunker` có sẵn trong `src/chunking.py`.

**Thành viên 2 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 3 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| | | | | |
| | | | | |
| | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.
>
> Đã chốt đủ 5/5 câu. Cố ý đa dạng hóa theo **loại câu hỏi** (không chỉ theo chủ đề) để bao quát nhiều dạng truy xuất khác nhau — xem ma trận bao phủ bên dưới. Nhóm từng thử một phương án khác cho câu 1 (đổi sang chủ đề `seller-listing-rules` để phủ thêm 1 tài liệu) nhưng đã **loại bỏ sau khi đo bằng embedding thật** — xem mục "So sánh với phương án câu 1 khác" ngay dưới bảng.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Người mua có thể gửi yêu cầu trả hàng/hoàn tiền trong vòng bao lâu kể từ khi đơn hàng giao thành công? | Trong vòng 15 ngày kể từ lúc đơn hàng được cập nhật giao hàng thành công; riêng thực phẩm tươi sống và đông lạnh chỉ có 24 giờ. | `shopee-return-refund-policy.md`, Điều 3.2 (`category: returns-policy`, `audience: buyer`) |
| 2 | Sản phẩm được bảo hành miễn phí khi đáp ứng những điều kiện nào? | Phải đủ 4 điều kiện: (i) lỗi kỹ thuật do nhà sản xuất, (ii) còn trong thời hạn bảo hành, (iii) có hóa đơn điện tử hoặc mã đơn hàng, (iv) với hàng điện gia dụng thì tem/phiếu bảo hành của nhà sản xuất còn nguyên vẹn. | `shopee-warranty-policy.md`, mục 1 "Điều kiện bảo hành" (`category: warranty-policy`, `audience: buyer`) |
| 3 | *(cần lọc metadata)* Người bán vi phạm Chính sách cấm/hạn chế sản phẩm sẽ bị Shopee áp dụng những chế tài nào? | Có thể bị: (i) xóa sản phẩm, (ii) giới hạn quyền tài khoản, (iii) đình chỉ/xóa tài khoản, (iv) cấn trừ số dư & phong tỏa quyền rút tiền, (v) các chế tài khác theo pháp luật (phạt hành chính, xử lý hình sự, bồi thường thiệt hại). | `shopee-prohibited-products.md`, mục 3 "Hành vi vi phạm và biện pháp xử lý" — cần lọc `category: seller-rules` (hoặc `doc_id`) để tránh nhầm với các đoạn "sản phẩm"/"tài khoản" trong các tài liệu buyer-facing khác có từ khóa tương tự |
| 4 | Đơn hàng có giá trị hàng hóa bao nhiêu thì Shopee không hỗ trợ vận chuyển? | Đơn hàng có tổng giá trị hàng hóa lớn hơn 50.000.000 VNĐ (tính theo giá khuyến mãi nếu có, không gồm mã giảm giá, xu, phí vận chuyển). | `shopee-shipping-policy.md`, mục B.1.1.d (`category: shipping-policy`, `audience: both`) |
| 5 | Người bán có phải chịu phí vận chuyển hoàn trả sản phẩm không, nếu đơn giao không thành công do lỗi của đơn vị vận chuyển? | Không. Theo Điều 7.2, Người Bán không phải chịu chi phí vận chuyển chiều hoàn trả trong trường hợp đơn giao không thành công do lỗi của đơn vị vận chuyển (khác với Điều 7.1 — các trường hợp Người Bán *phải* chịu phí). | `shopee-return-refund-policy.md`, Điều 7.1 và 7.2 (`category: returns-policy`, `audience: buyer`) — đòi hỏi phân biệt đúng điều khoản 7.1 (có chịu phí) và 7.2 (không chịu phí), không chỉ khớp từ khóa "phí vận chuyển hoàn trả" |

**Ma trận bao phủ (loại câu hỏi × đặc điểm truy xuất):**

| # | Dạng câu hỏi | Độ khó truy xuất | Ghi chú |
|---|--------------|-------------------|---------|
| 1 | Tra cứu số liệu deadline | Dễ | Baseline, chunk ngắn chứa trực tiếp con số |
| 2 | Liệt kê điều kiện (danh sách nhiều mục) | Trung bình | Cần chunk đủ lớn để không cắt đứt giữa các điều kiện (test độ mạch lạc/chunk coherence) |
| 3 | Liệt kê + **cần lọc metadata** | Khó | Từ khóa "sản phẩm/tài khoản" trùng lặp nhiều tài liệu khác nhau — chỉ semantic search dễ lấy nhầm nguồn |
| 4 | Tra cứu ngưỡng số liệu (threshold) | Dễ | Baseline dạng khác — số tiền thay vì thời gian |
| 5 | Yes/No + phân biệt 2 điều khoản liền kề, trái nghĩa nhau (7.1 vs 7.2) | Khó nhất | Kiểm tra retrieval có lấy đúng điều khoản, không lấy nhầm điều khoản đối lập ngay cạnh nhau — case tốt để phân tích lỗi ở Bài 3.5 nếu agent trả lời sai |

Bộ 5 câu phủ 4 category tài liệu (returns-policy, warranty-policy, seller-rules, shipping-policy) và nhiều dạng truy xuất khác nhau (tra cứu số liệu đơn giản, liệt kê nhiều ý, cần metadata filter, và phân biệt điều khoản đối lập) — không chỉ là 5 câu "trong vòng bao lâu" giống hệt nhau về cấu trúc.

### So sánh với phương án câu 1 khác (đã loại bỏ)

Nhóm từng cân nhắc đổi câu 1 sang chủ đề `shopee-seller-listing-rules.md` ("Người bán cần tuân thủ quy định gì về hình ảnh và tên sản phẩm?") để bộ 5 câu phủ 5/8 tài liệu riêng biệt thay vì 4/8 (hiện `return-refund-policy` được dùng ở cả câu 1 và câu 5, tuy ở 2 Điều khác nhau — Điều 3 và Điều 7). Trước khi chốt, nhóm **chạy thử cả 2 phương án bằng embedding thật (OpenAI)** trên cùng chiến lược `recursive, chunk_size=500` để so sánh bằng số liệu thay vì chỉ suy luận lý thuyết:

| Phương án câu 1 | top-1 hit rate (5 câu) | top-3 hit rate (5 câu) |
|---|---|---|
| "Thời hạn trả hàng/hoàn tiền" (giữ nguyên, dùng `return-refund-policy`) | **4/5** | **5/5** |
| "Quy định hình ảnh + tên sản phẩm" (đổi sang `seller-listing-rules`) | 3/5 | 4/5 |

**Kết quả: phương án đổi sang `seller-listing-rules` cho retrieval TỆ HƠN** — nguyên nhân là câu hỏi ghép 2 ý trong 1 câu ("hình ảnh VÀ tên sản phẩm") khiến vector câu hỏi không khớp rõ với 1 chunk cụ thể; cả 3 kết quả top-3 đều trả về nhầm `shopee-platform-charter` (tài liệu nói chung chung về nghĩa vụ người bán) thay vì đúng `shopee-seller-listing-rules`. Đây là bài học thực tế: **câu hỏi càng ghép nhiều ý, retrieval càng dễ trượt** — dù về lý thuyết phủ được nhiều tài liệu hơn thì đa dạng hơn, hiệu suất truy xuất thực tế lại kém hơn. Nhóm quyết định **giữ nguyên bộ 5 câu ban đầu** (ưu tiên retrieval quality đã kiểm chứng bằng số liệu thật, đúng tinh thần "đo trước khi kết luận" của Bài 3.4/3.5).

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Thời hạn trả hàng/hoàn tiền | Recursive, chunk_size=500 (score top-1 = 0.7887) | Có — đúng chunk chứa "15 ngày" ở hạng 1 | Chưa có số liệu `fixed_size`/`by_sentences` từ thành viên khác để so sánh chéo |
| 2 | Điều kiện bảo hành miễn phí | Recursive, chunk_size=500 (score top-1 = 0.6648) | Có | Đúng tài liệu ngay hạng 1, nhưng nội dung 4 điều kiện có thể nằm rải ở 2 chunk khác nhau trong tài liệu (cần kiểm tra thêm nếu agent trả lời thiếu ý) |
| 3 | Chế tài vi phạm sản phẩm cấm | Recursive, chunk_size=500 + **metadata filter** (score top-1 = 0.7549) | Có | Có lọc `metadata_filter={"audience": "seller"}` — xem câu hỏi bên dưới |
| 4 | Ngưỡng giá trị đơn hàng không hỗ trợ vận chuyển | Recursive, chunk_size=500 (score top-1 = 0.7171) | Có — trúng đúng câu chứa "50.000.000VNĐ" | Câu dễ nhất trong bộ, mọi thứ hoạt động như kỳ vọng |
| 5 | Ai chịu phí hoàn trả khi lỗi vận chuyển (Điều 7.1 vs 7.2) | Recursive, chunk_size=500 — **nhưng vẫn SAI top-1** (score top-1 = 0.6658, sai tài liệu) | Có tính theo doc_id (hạng 3 đúng `return-refund-policy`) nhưng **KHÔNG đúng nội dung** — hạng 3 là Điều 3.1, không phải Điều 7 | Case lỗi thật, dùng cho Bài 3.5 (Phân Tích Lỗi) — xem chi tiết trong `REPORT_CANHAN.md` mục 5 |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có — ở câu 3, dùng `search_with_filter(metadata_filter={"audience": "seller"})` giúp loại các tài liệu buyer-facing (return-refund, warranty) ra khỏi tập ứng viên trước khi tính điểm tương đồng, nên dù từ khóa "sản phẩm"/"tài khoản" rất phổ biến, top-3 vẫn toàn `shopee-prohibited-products`/`shopee-seller-listing-rules` (cả 2 đều seller-facing, đúng ngữ cảnh). Nếu không lọc, nguy cơ lẫn với các đoạn "tài khoản Shopee của Người Mua" bên tài liệu return-refund-policy là có thật (đã thấy hiện tượng tương tự ở câu 5, nơi không lọc và bị lẫn nhầm tài liệu).

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
