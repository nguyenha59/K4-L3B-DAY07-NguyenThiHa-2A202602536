# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** 3in1
**Thành viên:** Phạm Hương Giang; Nguyễn Thị Hạ; Ngô Minh Thu
**Ngày:** 2026-09-20

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Chính sách Trả hàng và Hoàn tiền trên Shopee

**Tại sao nhóm chọn chủ đề này?**

> Nhóm chọn corpus này vì tài liệu có cấu trúc điều/mục rõ ràng, phù hợp để so sánh nhiều chiến lược chunking. Corpus cũng có metadata `audience`, tạo được tình huống kiểm chứng retrieval có lọc đối tượng.

### Danh sách tài liệu (Data Inventory)

| #   | Tên tài liệu                     | Nguồn (Source URL)                    | Ngày lấy / Phiên bản    | Số ký tự | Metadata đã gán |
| --- | -------------------------------- | ------------------------------------- | ----------------------- | -------- | --------------- |
| 1   | `shopee-return-refund-policy.md` | help.shopee.vn/portal/4/article/77251 | 2026-09-20 / 2026-09-15 | 19,610   | buyer           |
| 2   | `shopee-warranty-policy.md`      | help.shopee.vn/portal/4/article/79046 | 2026-09-20 / 2026-09-15 | 4,403    | buyer           |
| 3   | `shopee-prohibited-products.md`  | help.shopee.vn/portal/4/article/77247 | 2026-09-20 / 2026-09-15 | 14,879   | seller          |
| 4   | `shopee-shipping-policy.md`      | help.shopee.vn/portal/4/article/77250 | 2026-09-20 / 2026-09-15 | 24,598   | both            |
| 5   | `shopee-platform-charter.md`     | help.shopee.vn/portal/4/article/77245 | 2026-09-20 / 2026-09-15 | 25,925   | both            |

Corpus benchmark thực tế gồm 8 file Markdown chính trong `data/ecommerce`, gồm cả 5 tài liệu nêu trên và `shopee-mall-terms.md`, `shopee-return-refund-general.md`, `shopee-seller-listing-rules.md`.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**

- [x] Tập tài liệu chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu benchmark có `source_url`, `retrieved_at`, `document_version` trong frontmatter.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata                                  | Kiểu   | Ví dụ giá trị             | Tại sao hữu ích cho truy xuất (retrieval)?                           |
| ------------------------------------------------ | ------ | ------------------------- | ---------------------------------------------------------------------|
| `audience`                                       | string | `buyer`, `seller`, `both` | Lọc đúng đối tượng khi hai tài liệu cùng chủ đề có đáp án khác nhau. |
| `source_url`, `retrieved_at`, `document_version` | string | URL, ngày lấy, phiên bản  | Truy vết nguồn và thời điểm của quy định.                            |
| `doc_id`                                         | string | tên file gốc              | Xóa toàn bộ chunk của một tài liệu và hiển thị nguồn.                |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

Benchmark chạy trên toàn bộ 8 tài liệu sau khi bỏ frontmatter, với `chunk_size=500`. Ba lần chạy cho thấy số lượng chunk khác nhau theo cấu hình và cách tiền xử lý:

| Strategy     | Ngô Minh Thu: count / avg length | Phạm Hương Giang: count / avg length | Nguyễn Thị Hạ: count / avg length |
| ------------ | --------------------------------:| -------------------------------------:| ----------------------------------:|
| fixed_size   |                      402 / 499.7 |                          444 / 499.1 |                       393 / 499.0 |
| by_sentences |                      513 / 388.3 |                          479 / 413.2 |                       388 / 401.1 |
| recursive    |                      556 / 358.9 |                          555 / 357.1 |                       439 / 355.5 |

Run của Thu dùng mock embedding và chiến lược cá nhân `HeadingChunker(chunk_size=1200)`; bảng baseline vẫn dùng `chunk_size=500` theo yêu cầu comparator. Run của Giang dùng local multilingual embedding, còn Hạ dùng OpenAI embedding. Chênh lệch cần được giữ nguyên trong báo cáo thay vì gộp thành một con số duy nhất; muốn so sánh tuyệt đối phải cố định phiên bản corpus và cách tiền xử lý.

| Quan sát     | Nhận xét                                                                                                          |
| ------------ | --------------------------------------------------------------------------------------------------------------- |
| fixed-size   | Độ dài gần sát 500 ký tự và số chunk thấp hơn, nhưng dễ cắt giữa điều khoản.                                     |
| by-sentences | Giữ ranh giới câu nhưng có thể gom các câu thuộc nhiều mục khác nhau.                                            |
| recursive    | Chunk ngắn hơn và mạch lạc hơn theo đoạn/dòng, nhưng có thể mất heading nếu không gắn lại metadata hoặc tiêu đề. |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Ngô Minh Thu**

- **Loại chiến lược:** custom — `HeadingChunker`
- **Mô tả & lý do chọn cho chủ đề này:** Tách trước mỗi heading Markdown để mỗi mục quy định là một chunk ngữ nghĩa. Nếu mục quá dài, chunker recursive chia tiếp nhưng gắn lại heading vào mọi mảnh con, nên mảnh sau không mất ngữ cảnh. Đây là chiến lược phù hợp với tài liệu chính sách và điều khoản vì ranh giới của các mục đã có ý nghĩa ngữ nghĩa rõ ràng.
- **Code snippet (nếu custom):**

```python
class HeadingChunker:
    """Split Markdown sections at headings, then recursively split long ones."""

    HEADING_RE = re.compile(r"(?m)^(#{1,6}\s+.+?)\s*$")

    def __init__(self, chunk_size: int = 1200) -> None:
        self.chunk_size = chunk_size
        self._fallback = RecursiveChunker(chunk_size=chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text.strip():
            return []

        matches = list(self.HEADING_RE.finditer(text))
        if not matches:
            return self._fallback.chunk(text)

        sections: list[tuple[str, str]] = []
        if text[: matches[0].start()].strip():
            sections.append(("", text[: matches[0].start()].strip()))

        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            sections.append((match.group(1).strip(), text[match.end() : end].strip()))

        chunks: list[str] = []
        for heading, body in sections:
            section = "\n".join(part for part in (heading, body) if part).strip()
            if not section:
                continue
            if len(section) <= self.chunk_size or not heading:
                chunks.extend([section] if len(section) <= self.chunk_size else self._fallback.chunk(section))
                continue

            # Split only the body, then prepend the heading to every fragment.
            for fragment in self._fallback.chunk(body):
                chunks.append(f"{heading}\n{fragment}".strip())
        return chunks
```

**Thành viên 2 — Phạm Hương Giang**

- **Loại chiến lược:** `RecursiveChunker`, `chunk_size=500`, `top_k=3`.
- **Embedding:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` chạy local, 384 chiều.
- **Mô tả & lý do chọn:** Recursive chunking ưu tiên tách theo đoạn, dòng và câu trước khi cắt theo ký tự. Cách này giữ được đoạn văn tự nhiên hơn fixed-size, phù hợp với tài liệu tiếng Việt dài và có nhiều mục điều khoản.
- **Kết quả chính:** 558 chunk, overlap 0; top-1 đúng tài liệu 2/5, top-3 đúng tài liệu 4/5. Evidence đầy đủ ở Q1, Q2 và Q4.

**Thành viên 3 — Nguyễn Thị Hạ**

- **Loại chiến lược:** `RecursiveChunker`, `chunk_size=500`, `top_k=3`.
- **Embedding:** `text-embedding-3-small` của OpenAI.
- **Mô tả & lý do chọn:** Văn bản chính sách Shopee có cấu trúc phân đoạn rõ ràng: mỗi Điều/khoản cách nhau bằng dòng trống và mỗi mục con xuống dòng riêng. Vì vậy, `RecursiveChunker` tận dụng đúng các ranh giới này để giữ trọn một Điều/khoản trong một chunk thay vì cắt cứng theo ký tự như `FixedSizeChunker`. Bảng baseline cho thấy recursive giữ ngữ cảnh tốt nhất trên cả ba tài liệu thử nghiệm, đặc biệt quan trọng với câu hỏi 5 vì cần phân biệt đúng Điều 7.1 và 7.2 nằm sát nhau.
- **Cách chạy để tái lập:** `python bench.py --strategy recursive --chunk-size 500 --member "Nguyễn Thị Hạ"`.
- **Kết quả chính:** 442 chunk; top-1 đúng tài liệu 4/5, top-3 đúng tài liệu 5/5; latency trung bình 362.81 ms.

### So Sánh Giữa Các Thành Viên

| Thành viên       | Chiến lược (Strategy)                     | Kết quả chính                              | Điểm mạnh                                                | Điểm yếu                                    |
| ---------------- | ------------------------------------------| ------------------------------------------ | --------------------------------------------------------| ---------------------------------------------|
| Ngô Minh Thu     | HeadingChunker, 1200, mock                | 0/5 evidence trong top-3; 198 chunk        | Giữ heading và ngữ cảnh mục                              | Mock embedding không phản ánh ngữ nghĩa     |
| Phạm Hương Giang | RecursiveChunker, 500, local multilingual | 2/5 top-1 doc; 4/5 top-3 doc; 3/5 evidence | Chạy local, phù hợp tiếng Việt, Q1/Q2 mạnh               | Q3 lấy sai section; Q5 thất bại             |
| Nguyễn Thị Hạ    | RecursiveChunker, 500, OpenAI             | 4/5 top-1 doc; 5/5 top-3 doc; 362.81 ms    | Top-1/top-3 tốt nhất trong hai benchmark embedding thật  | Phụ thuộc API và latency; Q5 vẫn chưa top-1 |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**

> Với corpus chính sách, hướng tốt nhất là kết hợp recursive chunking với embedding ngữ nghĩa thật, vì kết quả của Hạ cho thấy 4/5 top-1 và 5/5 top-3 đúng tài liệu. Tuy vậy, `HeadingChunker` vẫn có giá trị ở chỗ giữ tên mục; giải pháp hoàn thiện hơn là bảo toàn heading trong từng mảnh recursive và rerank theo mục/điều khoản để xử lý Q3 và Q5.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| #   | Câu hỏi (Query)                                                                                                           | Câu trả lời chuẩn (Gold Answer)                                                                                                                        | Chunk nào chứa thông tin?                                        |
| --- | --------------------------------------------------------------------------------------------------------------------------| ---------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------|
| 1   | Người mua có thể yêu cầu trả hàng/hoàn tiền trong vòng bao lâu kể từ khi đơn hàng giao thành công?                        | Trong vòng 15 ngày kể từ lúc đơn hàng cập nhật giao thành công; riêng thực phẩm tươi sống/đông lạnh chỉ 24 giờ.                                        | `shopee-return-refund-policy.md`, mục 3.2; không lọc               |
| 2   | Sản phẩm được bảo hành miễn phí khi đáp ứng những điều kiện nào?                                                          | Lỗi kỹ thuật do nhà sản xuất; còn hạn bảo hành; có hóa đơn điện tử hoặc mã đơn hàng; với hàng điện gia dụng thì tem/phiếu bảo hành còn nguyên vẹn.     | `shopee-warranty-policy.md`, mục 1; không lọc                      |
| 3   | Người bán vi phạm Chính sách cấm/hạn chế sản phẩm sẽ bị Shopee áp dụng những chế tài nào?                                 | Xóa sản phẩm; giới hạn quyền tài khoản; đình chỉ/xóa tài khoản; cấn trừ số dư và phong tỏa quyền rút tiền; các chế tài pháp luật khác.                 | `shopee-prohibited-products.md`, mục 3; filter `audience=seller`   |
| 4   | Đơn hàng có giá trị hàng hóa bao nhiêu thì Shopee không hỗ trợ vận chuyển?                                                | Trên 50.000.000 VNĐ, không bao gồm mã giảm giá, xu và phí vận chuyển.                                                                                  | `shopee-shipping-policy.md`, mục B.1; không lọc                    |
| 5   | Người bán có phải chịu phí vận chuyển hoàn trả sản phẩm không nếu đơn giao không thành công do lỗi của đơn vị vận chuyển? | Không phải trong các trường hợp được nêu tại Điều 7.2; chính sách quy định các trường hợp Người Bán không phải chịu chi phí vận chuyển chiều hoàn trả. | `shopee-return-refund-policy.md`, Điều 7.2; không lọc               |

Các gold answer trong `bench.py` đã được chuẩn hóa thành đoạn trích/paraphrase sát trực tiếp từ các mục tương ứng trong corpus; benchmark chạy trên cùng 5 query này.

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| #   | Câu hỏi                                    | Hạ: doc/evidence | Giang: doc/evidence | Thu: doc/evidence | Nhận xét                                                               |
| --- | --------------------------------------------| ------------------| ---------------------| --------------------| -------------------------------------------------------------------------|
| 1   | Thời hạn trả hàng/hoàn tiền                | 1 / 1             | 1 / 1                | 3 / -               | Thu có đúng tài liệu nhưng không có marker bằng chứng.                  |
| 2   | Điều kiện bảo hành miễn phí                | 1 / 1             | 1 / 1                | - / -               | Hai embedding thật đưa đúng tài liệu và evidence lên top-1.              |
| 3   | Chế tài sản phẩm cấm/hạn chế               | 1 / chưa có log   | 2-3 / -              | - / -               | Filter seller giúp Hạ lấy đúng tài liệu, nhưng chưa chắc đúng section.  |
| 4   | Ngưỡng giá trị đơn không hỗ trợ vận chuyển | 1 / 1             | 3 / 3                | - / -               | Giang có đáp án ở top-3; Hạ đưa đáp án lên top-1.                       |
| 5   | Phí hoàn trả khi lỗi đơn vị vận chuyển     | 3 / -             | - / -                | - / -               | Đây là failure case của retrieval; cần rerank theo Điều 7.2.            |

`doc` là hạng của tài liệu gold; `evidence` là hạng của chunk chứa marker bằng chứng. Dấu `-` nghĩa là không xuất hiện trong top-3. Với Q3, log của Hạ chỉ xác nhận đúng tài liệu ở top-1; chưa có `evidence_rank` nên không được tính như evidence hit.

Kết quả ngày 2026-09-20 gồm ba lần chạy cá nhân. Thu dùng `HeadingChunker(chunk_size=1200)` với mock embedding và 198 chunk; Giang dùng recursive/local với 558 chunk; Hạ dùng recursive/OpenAI với 442 chunk. Do backend và kích thước chunk khác nhau, nhóm chỉ dùng hai kết quả embedding thật để so sánh retrieval; kết quả mock của Thu chỉ dùng để kiểm tra pipeline và minh họa failure case.

### CP6 — Chấm theo nội dung và A/B metadata filter

`bench.py` kiểm tra đồng thời `doc_rank` (tài liệu gold) và `evidence_rank` (chunk top-3 có chứa marker bằng chứng). Điểm CP6 dùng `evidence_rank`: hạng 1 = 2 điểm, hạng 2/3 = 1 điểm, không có = 0 điểm.

| Query / log Thu dùng mock         | Fixed: A/B evidence/doc | Sentence: A/B evidence/doc | Recursive: A/B evidence/doc |
| ---------------------------------- | ------------------------| ----------------------------| ------------------------------|
| Q3 — chế tài sản phẩm cấm/hạn chế | A: -/-; B: -/-          | A: -/1; B: -/1              | A: -/-; B: -/-                |

Trong bảng, A là không lọc và B là lọc theo `audience`; mỗi ô ghi `evidence_rank/doc_rank`. A/B của Thu đã chạy trên cả ba baseline chunker và cho thấy sentence chunker giữ đúng document ở hạng 1 cả trước và sau filter, nhưng không có evidence. Như vậy filter không tự tạo ra evidence nếu chunk đúng section chưa được chọn. Log A/B tương ứng của Giang và Hạ chưa có trong các artifact hiện tại, nên nhóm không suy diễn số liệu cho hai backend thật; cần bổ sung trước khi khẳng định so sánh A/B giữa các thành viên.

### Failure case và đề xuất sửa

Q3 và Q5 là hai failure case quan trọng. Ở Q3, filter `audience=seller` giúp đưa đúng tài liệu vào kết quả nhưng chưa đưa đúng section chế tài lên đầu. Ở Q5, các chunk về vận chuyển có điểm cao hơn dù điều kiện pháp lý nằm ở Điều 7.2. Nguyên nhân là similarity tổng quát chưa đủ nhạy với số điều, điều kiện phủ định và cụm từ pháp lý. Đề xuất: giữ heading/section trong chunk, dùng hybrid keyword + vector search, tăng `top_k` rồi rerank theo số điều và các cụm bằng chứng như `7.2`, `không phải chịu phí`.

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**

> Q3 là câu bắt buộc cần filter `{"audience": "seller"}`. Kết quả của Hạ cho thấy filter giúp tài liệu `shopee-prohibited-products` lên top-1, nhưng đoạn mở đầu vẫn được chọn thay vì mục chế tài. Vì vậy metadata filter có ích ở cấp document, nhưng cần kết hợp với section-aware retrieval để trả lời chính xác ở cấp evidence.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

> Nhóm không tổ chức buổi thuyết trình/demo trực tiếp với các nhóm khác — phần này ghi lại bài học rút ra từ việc **so sánh nội bộ giữa 3 thành viên** (bằng dữ liệu benchmark thật, không phải suy đoán), thay cho phần trình bày miệng.

**Những phân tích (insights) hay nhất của nhóm:**

> - Recursive chunking kết hợp OpenAI embedding cho kết quả tài liệu tốt nhất trong benchmark: 4/5 top-1 và 5/5 top-3.
> - Heading chunking giữ tên mục trong mọi chunk con, còn metadata filter giúp thu hẹp đúng audience nhưng chưa đủ để chọn đúng section.
> - Mock embedding chỉ kiểm tra pipeline; không thể dùng để kết luận chất lượng ngữ nghĩa tiếng Việt.

**Bài học rút ra khi so sánh trong nhóm:**

> Fixed-size tạo chunk đều nhưng dễ cắt giữa điều khoản. Sentence giữ ranh giới câu nhưng có thể gom nhiều mục; recursive cân bằng tốt giữa độ dài và mạch lạc. Embedding backend ảnh hưởng rõ đến retrieval: cùng recursive và `chunk_size=500`, Hạ đạt 4/5 top-1 trong khi Giang đạt 2/5, nhưng đây là so sánh thực nghiệm giữa hai backend khác nhau chứ chưa phải thí nghiệm cô lập hoàn toàn.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**

> Nếu làm lại, nhóm sẽ chạy cùng một chunker trên cả local và OpenAI, ghi latency cho mọi thành viên, bổ sung đánh giá evidence/agent answer riêng với doc-level hit, và dùng hybrid retrieval có rerank theo heading, số điều và từ khóa phủ định. Nhóm cũng sẽ cố định phiên bản corpus, cache embedding và chuẩn hóa gold answer bằng trích dẫn nguyên văn.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí                                 | Điểm tự đánh giá | Lý do |
| ----------------------------------------- | ----------------- | ----- |
| Lựa chọn tài liệu (Document Set Quality)  | 9 / 10             | 8 tài liệu public-source, đủ `source_url`/`retrieved_at`/`document_version`, metadata schema có `audience` |
| Thiết kế chiến lược (Strategy Design)     | 14 / 15            | Baseline 3 chiến lược × 3 lần chạy thật, có code `HeadingChunker` đầy đủ, so sánh 3 thành viên bằng số liệu thật (doc_rank/evidence_rank) |
| Chất lượng truy xuất (Retrieval Quality)  | 8 / 10             | Q1, Q2, Q4 đạt evidence hạng 1; Q3 đạt doc-level nhờ filter nhưng chưa evidence; Q5 là failure case thật (cần rerank theo Điều 7.2) |
| Thuyết trình (Demo)                       | 2 / 5              | Nhóm không tổ chức demo/thuyết trình trực tiếp với nhóm khác nên không đáp ứng đủ tiêu chí gốc; chỉ có phần viết insight + bài học so sánh nội bộ 3 thành viên, chưa có phần trình bày/thảo luận trực tiếp |
| **Tổng phần nhóm**                        | **33 / 40**        | |
