# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** [Tên sinh viên]
**Nhóm:** [Tên nhóm]
**Ngày:** [Ngày nộp]

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> High cosine similarity nghĩa là hai vector embedding gần cùng hướng, tức là hai câu có nội dung/ngữ nghĩa gần nhau trong không gian biểu diễn. Giá trị càng gần 1 thì mức tương đồng ngữ nghĩa càng cao.

**Ví dụ HIGH similarity:**
- Sentence A: Vector stores enable semantic search.
- Sentence B: Vector databases support semantic retrieval.
- Tại sao tương đồng: Cả hai cùng nói về vai trò của vector store/database trong semantic retrieval, khác chủ yếu ở cách diễn đạt.

**Ví dụ LOW similarity:**
- Sentence A: Sentence chunking improves readability.
- Sentence B: Nuclear fusion powers stars in distant galaxies.
- Tại sao khác: Hai câu thuộc hai miền hoàn toàn khác nhau (NLP vs vật lý thiên văn), không chia sẻ ngữ cảnh nhiệm vụ.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Cosine similarity tập trung vào hướng của vector nên phản ánh mức tương đồng ngữ nghĩa tốt hơn khi độ lớn vector thay đổi. Với embeddings văn bản, hướng thường quan trọng hơn khoảng cách tuyệt đối theo norm.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Trình bày phép tính: num_chunks = ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11)
> Đáp án: 23 chunks

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> Khi overlap=100: num_chunks = ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = 25 chunks, tức là tăng thêm 2 chunks. Overlap lớn hơn giúp giữ ngữ cảnh giữa các chunk tốt hơn, giảm nguy cơ mất thông tin ở ranh giới chunk.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Software Engineering Principles

**Tại sao nhóm chọn domain này?**
> Nhóm chúng tôi chọn domain này vì nó chứa các khái niệm cốt lõi, có cấu trúc rõ ràng và phân cấp, rất phù hợp để thử nghiệm các chiến lược chunking khác nhau. Việc hiểu và truy xuất chính xác các nguyên lý như SOLID, DRY, KISS là một bài toán thực tế và hữu ích cho các kỹ sư phần mềm.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | book.md | https://onlinelibrary.wiley.com/doi/book/10.1002/9781394297696?msockid=342527e00a4661fb18ff345a0bdc6080 | 503401 | `{"category": "software-engineering", "source": "book.md"}` |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| category | string | "software-engineering" | Giúp lọc các tài liệu theo chủ đề lớn, hữu ích khi hệ thống có nhiều domain khác nhau. |
| source | string | "book.md" | Cho phép truy xuất nguồn gốc của chunk, giúp xác minh thông tin và cung cấp thêm ngữ cảnh cho người dùng. |


---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| book.md | FixedSizeChunker (`fixed_size`) | 252 | 2196.83 | Ổn định độ dài, nhưng dễ cắt gãy theo ký tự |
| book.md | SentenceChunker (`by_sentences`) | 435 | 1154.20 | Dễ đọc theo câu, nhưng context phân mảnh ở tài liệu dài |
| book.md | RecursiveChunker (`recursive`) | 285 | 1762.25 | Cân bằng tốt giữa cấu trúc và giới hạn độ dài |
| book.md | **DocumentStructureChunker (`document_structure`)** | **301** | **1739.23** | **Giữ heading/list/table tốt nhất cho Markdown dài** |

### Strategy Của Tôi

**Loại:** DocumentStructureChunker

**Mô tả cách hoạt động:**
> Strategy tách tài liệu theo cấu trúc Markdown/HTML-aware: heading, list, table, fenced code, HTML-like block. Mỗi chunk được giữ theo block logic thay vì cắt thẳng theo ký tự, và có thể đính kèm heading context để tăng khả năng grounding khi retrieval.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Dữ liệu nhóm dùng một tài liệu Markdown rất dài (`book.md`) có cấu trúc phân cấp rõ (nhiều heading, danh sách, mục lục, block quote). DocumentStructureChunker phù hợp nhất vì tận dụng chính cấu trúc tài liệu để tạo chunk có tính ngữ nghĩa và dễ truy vết nguồn.

**Code snippet (nếu custom):**
```python
# Paste implementation here
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| book.md | best baseline: FixedSizeChunker | 252 | 2196.83 | 3.6/10 (mock embedding) |
| book.md | best baseline: RecursiveChunker | 285 | 1762.25 | 3.0/10 (mock embedding) |
| book.md | **của tôi: DocumentStructureChunker** | **301** | **1739.23** | **5.6/10 (mock embedding), cao nhất trong lượt chạy** |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi | | | | |
| [Tên] | | | | |
| [Tên] | | | | |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> Trong benchmark hiện tại, DocumentStructureChunker cho điểm tổng hợp cao nhất vì chunk giữ được ngữ cảnh theo section thay vì bị cắt rời. Với tài liệu dạng sách Markdown dài, strategy này phù hợp hơn Sentence/Fixed/Recursive thuần separator.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`DocumentStructureChunker.chunk`** — approach:
> Mình parse tài liệu theo block-level structure trước (heading, list, table, code fence, html-like), sau đó mới ghép block thành chunk theo `chunk_size`. Cách này giúp chunk có tính ngữ nghĩa rõ hơn và không làm vỡ bảng/danh sách khi retrieve.

**Heading-aware context** — approach:
> Khi gặp heading mới, chunker cập nhật heading stack (`#`, `##`, `###`...) và có thể prepend heading context vào chunk content. Điều này giúp retrieval trả về đoạn có ngữ cảnh section đầy đủ, giảm trường hợp trả về đoạn rời khó hiểu.

**Fallback split cho block quá lớn** — approach:
> Nếu một block vẫn vượt quá `chunk_size`, chunker fallback sang recursive split bằng separator nhỏ dần. Nhờ đó vẫn đảm bảo giới hạn độ dài embedding mà không phá hỏng hoàn toàn cấu trúc gốc.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> Mỗi `Document` được chuẩn hóa thành record gồm `id`, `content`, `metadata`, `embedding`; metadata luôn bổ sung `doc_id` để phục vụ lọc/xóa. Search embed câu query rồi tính dot-product với embedding của từng record, sau đó sort giảm dần theo `score` và lấy top_k. Store hỗ trợ cả nhánh in-memory mặc định và nhánh ChromaDB khi môi trường có cài.

**`search_with_filter` + `delete_document`** — approach:
> `search_with_filter` lọc trước theo metadata (`all key=value`) rồi mới chạy similarity search trên tập đã lọc để tăng precision. `delete_document` xóa toàn bộ chunk có `metadata['doc_id'] == doc_id`; với ChromaDB thì gọi delete theo `where`, còn in-memory thì rebuild list không chứa doc đó. Hàm trả `True/False` để phản ánh có xóa thực sự hay không.

### KnowledgeBaseAgent

**`answer`** — approach:
> Agent retrieve top-k chunk từ `EmbeddingStore`, đánh số và ghép thành block `Context` trong prompt. Prompt yêu cầu model chỉ dùng ngữ cảnh cung cấp và phải nói rõ khi context chưa đủ để trả lời chắc chắn. Cách này giúp answer grounded hơn và dễ kiểm tra traceability theo chunk.

### Test Results

```
pytest tests/ -v
...
============================= 45 passed in 0.21s ==============================
```

**Số tests pass:** 45 / 45

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | IS governance defines decision structures and accountability mechanisms. | Information systems governance organizes decision rights and responsibilities. | high | -0.0991 | Sai |
| 2 | Cloud-centric architecture centralizes advanced services for users. | Host-centric systems relied on centralized mainframe resources. | medium | 0.1575 | Đúng (tương đối) |
| 3 | Urbanization maps territories and information flows. | Urbanization helps decision-makers analyze architecture constraints and opportunities. | high | -0.1536 | Sai |
| 4 | COBIT is used as a governance benchmark for IS audit. | ITIL focuses on service lifecycle and operational quality. | medium | 0.0393 | Đúng |
| 5 | Information systems alignment supports strategic agility. | A random recipe about cooking pasta with tomatoes. | low | -0.0156 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Kết quả gây bất ngờ nhất là cặp 1 và 3: ngữ nghĩa gần nhau nhưng score âm. Nguyên nhân chính là benchmark đang dùng mock embedding deterministic, không phải semantic embedder thật, nên score chỉ có tính tham khảo kỹ thuật. Vì vậy khi đánh giá chất lượng retrieval thực tế, nên dùng Local/OpenAI embedding và giữ cùng query set để so sánh công bằng.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | What are the three key concepts proposed to approach information systems management? | Governance, urbanization, and alignment. |
| 2 | How did technological waves evolve from host centric to cloud centric? | From host-centric to client-server, then network-centric, then cloud-centric. |
| 3 | What is the relationship between global governance and IS governance? | IS governance derives from organizational governance and balances compliance with performance/value creation. |
| 4 | Which governance benchmarks are discussed in practice such as COBIT and ITIL? | COBIT and ITIL are major benchmarks, alongside others like ValIT, RiskIT, GTAG, ISO. |
| 5 | What is the purpose of IS urbanization? | To visualize organization levels, detect constraints/opportunities, and improve information flow coherence. |

### Thiết Lập Chạy Benchmark

- Embedding backend: mock
- top_k: 3
- Bộ dữ liệu: 1 tài liệu `book.md` (Markdown dài, có heading/list/table)
- So sánh công bằng: cùng query set, cùng top_k, cùng embedding backend cho cả 4 strategy

### Kết Quả Top-3 Theo Strategy

#### A) FixedSizeChunker (`fixed_size`)

| # | Query | Top-3 retrieved (chunk index) | Query Score (/10) |
|---|-------|-------------------------------|-------------------|
| 1 | Three key concepts | [72, 149, 145] | 7 |
| 2 | Technological waves | [212, 109, 241] | 0 |
| 3 | Global vs IS governance | [164, 100, 149] | 0 |
| 4 | COBIT/ITIL benchmarks | [248, 73, 113] | 4 |
| 5 | Purpose of IS urbanization | [99, 38, 88] | 7 |

#### B) SentenceChunker (`by_sentences`)

| # | Query | Top-3 retrieved (chunk index) | Query Score (/10) |
|---|-------|-------------------------------|-------------------|
| 1 | Three key concepts | [417, 21, 251] | 4 |
| 2 | Technological waves | [415, 211, 302] | 0 |
| 3 | Global vs IS governance | [164, 355, 181] | 4 |
| 4 | COBIT/ITIL benchmarks | [407, 247, 103] | 0 |
| 5 | Purpose of IS urbanization | [232, 150, 122] | 4 |

#### C) RecursiveChunker (`recursive`)

| # | Query | Top-3 retrieved (chunk index) | Query Score (/10) |
|---|-------|-------------------------------|-------------------|
| 1 | Three key concepts | [169, 284, 22] | 4 |
| 2 | Technological waves | [85, 79, 76] | 0 |
| 3 | Global vs IS governance | [154, 70, 123] | 4 |
| 4 | COBIT/ITIL benchmarks | [144, 48, 190] | 0 |
| 5 | Purpose of IS urbanization | [73, 160, 8] | 7 |

#### D) DocumentStructureChunker (`document_structure`)

| # | Query | Top-3 retrieved (chunk index) | Query Score (/10) |
|---|-------|-------------------------------|-------------------|
| 1 | Three key concepts | [89, 170, 151] | 10 |
| 2 | Technological waves | [184, 268, 82] | 0 |
| 3 | Global vs IS governance | [86, 190, 249] | 7 |
| 4 | COBIT/ITIL benchmarks | [3, 51, 273] | 4 |
| 5 | Purpose of IS urbanization | [234, 103, 177] | 7 |

### Chấm Điểm Theo Rubric Tự Đánh Giá

Thang điểm: trung bình 5 query, mỗi query chấm theo 5 tiêu chí (Retrieval Precision, Chunk Coherence, Metadata Utility, Grounding Quality, Data Strategy Fit), tổng tối đa 10 điểm/query.

| Strategy | Điểm trung bình (/10) | Nhận xét ngắn |
|----------|------------------------|---------------|
| FixedSizeChunker | 3.6 | Độ dài ổn định nhưng mất cấu trúc section |
| SentenceChunker | 2.4 | Coherence theo câu nhưng rời ngữ cảnh chapter |
| RecursiveChunker | 3.0 | Khá cân bằng, nhưng chưa nhận diện block đặc thù Markdown |
| **DocumentStructureChunker** | **5.6** | **Tốt nhất trong lượt chạy; giữ heading/list/table nên grounding tốt hơn** |

### Kết Luận Retrieval

**Bao nhiêu queries trả về chunk relevant trong top-3?** 4 / 5 (với DocumentStructureChunker)

Trong lần chạy này, DocumentStructureChunker đạt điểm cao nhất trên bộ query đã chọn. Kết quả cho thấy khi dữ liệu có cấu trúc phân cấp rõ (book markdown), strategy dựa trên document structure sẽ hiệu quả hơn chunking tuyến tính theo câu hoặc ký tự.

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> *Viết 2-3 câu:*

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> *Viết 2-3 câu:*

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | / 5 |
| Document selection | Nhóm | / 10 |
| Chunking strategy | Nhóm | / 15 |
| My approach | Cá nhân | / 10 |
| Similarity predictions | Cá nhân | / 5 |
| Results | Cá nhân | / 10 |
| Core implementation (tests) | Cá nhân | / 30 |
| Demo | Nhóm | / 5 |
| **Tổng** | | **/ 100** |
