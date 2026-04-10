# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Đăng Hải
**Nhóm:** D01
**Ngày:** 10/4/2026

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
| book.md| FixedSizeChunker (`fixed_size`) | 1119 | 499.82 | |
| book.md| SentenceChunker (`by_sentences`) | 3877 | 128.28 | |
| book.md| RecursiveChunker (`recursive`) | 1398 | 358.34 | |
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
| book.md | best baseline: FixedSizeChunker | 1119 | 499.83 | 3.6/10 |
| book.md | best baseline: RecursiveChunker | 1398 | 358 | 3.0/10 |
| book.md | **của tôi: DocumentStructureChunker** | **301** | **1739.23** | **5.6/10 (mock embedding), cao nhất trong lượt chạy** |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Nguyễn Tuấn Hưng | Semantic Chunking | 9.5 | Giữ trọn vẹn ngữ cảnh của từng mục, truy xuất chính xác. | Các chunk có thể rất lớn, không phù hợp với các mô hình có giới hạn context nhỏ. |
| Lê Minh Hoàng | SoftwareEngineeringChunker (Custom RecursiveTrunker) | 9 | Bảo tồn hoàn hảo cấu trúc tài liệu kỹ thuật nhờ ngắt theo Header; Giữ được mối liên kết logic. | Kích thước chunk trung bình lớn, gây tốn context window của mô hình. |
| Nguyễn Xuân Hải | Parent-Child Chunking| 8 |Child nhỏ giúp tìm kiếm vector đúng mục tiêu, ít nhiễu | Gửi cả khối Parent lớn vào Prompt làm tăng chi phí API.
| Tôi | DocumentStructureChunker | 6.3 | Giữ ngữ cảnh theo heading/list/table; grounding tốt cho tài liệu dài | Phức tạp hơn và tốn xử lý hơn; lợi thế giảm khi dữ liệu ít cấu trúc |
|Thái Minh Kiên | Agentic Chunking | 8 | chunk giữ được ý nghĩa trọn vẹn, retrieval chính xác hơn, ít trả về nửa vời, Không cần một rule cố định cho mọi loại dữ liệu | Với dataset lớn cost sẽ tăng mạnh,  chậm hơn pipeline thường, không ổn định tuyệt đối |
Trần Trung Hậu |Token-Based Chunking (Chia theo Token) | 8 | Kiểm soát chính xác tuyệt đối giới hạn đầu vào (context window) và chi phí API của LLM. | Cắt rất máy móc, dễ làm đứt gãy ngữ nghĩa của một từ hoặc một câu giữa chừng.
| Tạ Bảo Ngọc | Sliding Window + Overlap | 7/10 | Giữ vẹn câu/khối logic, tối ưu length | bị trùng dữ liệu -> tăng số chunk |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> `Semantic Chunking` là tốt nhất cho domain này vì nó tôn trọng cấu trúc logic của tài liệu, đảm bảo mỗi chunk là một đơn vị thông tin hoàn chỉnh. Điều này giúp hệ thống RAG truy xuất được ngữ cảnh đầy đủ để trả lời các câu hỏi về các nguyên lý cụ thể một cách chính xác nhất.

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
| 1 | What are the SOLID principles? | SOLID refers to five core object-oriented design principles: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, and Dependency Inversion. |
| 2 | Explain the DRY principle. | Don't Repeat Yourself means the same knowledge or logic should be represented only once in a system. |
| 3 | What is the difference between SRP and ISP? | SRP says a class should have only one reason to change, whereas ISP says clients should not be forced to depend on methods they do not use. |
| 4 | What does KISS stand for? | KISS stands for Keep It Simple, Stupid. |
| 5 | Summarize the main idea of the Open/Closed Principle. | The Open/Closed Principle says software should be designed to extend behavior without changing existing code. |

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
| 2 | Technological waves | [415, 211, 302] | 6 |
| 3 | Global vs IS governance | [164, 355, 181] | 4 |
| 4 | COBIT/ITIL benchmarks | [407, 247, 103] | 0 |
| 5 | Purpose of IS urbanization | [232, 150, 122] | 4 |

#### C) RecursiveChunker (`recursive`)

| # | Query | Top-3 retrieved (chunk index) | Query Score (/10) |
|---|-------|-------------------------------|-------------------|
| 1 | Three key concepts | [169, 284, 22] | 4 |
| 2 | Technological waves | [85, 79, 76] | 6 |
| 3 | Global vs IS governance | [154, 70, 123] | 4 |
| 4 | COBIT/ITIL benchmarks | [144, 48, 190] | 0 |
| 5 | Purpose of IS urbanization | [73, 160, 8] | 7 |

#### D) DocumentStructureChunker (`document_structure`)

| # | Query | Top-3 retrieved (chunk index) | Query Score (/10) |
|---|-------|-------------------------------|-------------------|
| 1 | Three key concepts | [89, 170, 151] | 10 |
| 2 | Technological waves | [184, 268, 82] | 6 |
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
| **DocumentStructureChunker** | **6.3** | **Tốt nhất trong lượt chạy; giữ heading/list/table nên grounding tốt hơn** |

### Kết Luận Retrieval

**Bao nhiêu queries trả về chunk relevant trong top-3?** 4 / 5 (với DocumentStructureChunker)

Trong lần chạy này, DocumentStructureChunker đạt điểm cao nhất trên bộ query đã chọn. Kết quả cho thấy khi dữ liệu có cấu trúc phân cấp rõ (book markdown), strategy dựa trên document structure sẽ hiệu quả hơn chunking tuyến tính theo câu hoặc ký tự.

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Tôi học được cách một strategy chunking tốt không chỉ cần cắt đúng độ dài mà còn phải giữ được cấu trúc nội dung gốc, nhất là với tài liệu Markdown dài như `book.md`. Việc bạn trong nhóm dùng tiêu chí rõ ràng để so sánh các strategy giúp tôi hiểu rằng retrieval quality nên được nhìn cùng lúc với chunk coherence và grounding, không nên chỉ nhìn số lượng chunk.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Qua demo, tôi thấy các nhóm làm tốt thường không chỉ mô tả kết quả mà còn giải thích vì sao strategy của họ phù hợp với domain đã chọn. Điều đó giúp phần trình bày thuyết phục hơn, và cũng cho tôi ý tưởng rằng khi đánh giá retrieval nên dùng cùng một bộ query, cùng top_k và cùng embedding backend để so sánh công bằng hơn.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Nếu làm lại, tôi sẽ thử tách tài liệu theo nhiều mức cấu trúc hơn, ví dụ kết hợp heading-aware chunking với một lớp parent context ngắn gọn để giảm mất mát ngữ cảnh. Tôi cũng sẽ chuẩn hóa lại metadata chi tiết hơn, chẳng hạn thêm chapter hoặc section path, để retrieval và giải thích kết quả rõ ràng hơn khi truy vấn các khái niệm như SOLID, DRY, KISS.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 10 / 10 |
| Chunking strategy | Nhóm | 15 / 15 |
| My approach | Cá nhân | 9 / 10 |
| Similarity predictions | Cá nhân | 4 / 5 |
| Results | Cá nhân | 10 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 5 / 5 |
| **Tổng** | | **83 / 90** |
