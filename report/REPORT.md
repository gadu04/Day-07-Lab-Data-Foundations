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

**Domain:** Internal knowledge assistant (engineering + support documentation)

**Tại sao nhóm chọn domain này?**
> Domain này phù hợp với RAG vì dữ liệu có nhiều loại tài liệu khác nhau: hướng dẫn kỹ thuật, design notes, support playbook và ghi chú tiếng Việt. Việc trộn nhiều nguồn giúp đánh giá rõ tác động của chunking và metadata filtering. Đây cũng là bối cảnh gần với use case thực tế của trợ lý tri thức nội bộ.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | python_intro.txt | data/python_intro.txt | 1944 | department=engineering, language=en, source_type=intro, date=2026-04-10 |
| 2 | vector_store_notes.md | data/vector_store_notes.md | 2123 | department=engineering, language=en, source_type=notes, date=2026-04-10 |
| 3 | rag_system_design.md | data/rag_system_design.md | 2391 | department=engineering, language=en, source_type=design, date=2026-04-10 |
| 4 | customer_support_playbook.txt | data/customer_support_playbook.txt | 1692 | department=support, language=en, source_type=playbook, date=2026-04-10 |
| 5 | chunking_experiment_report.md | data/chunking_experiment_report.md | 1987 | department=engineering, language=en, source_type=report, date=2026-04-10 |
| 6 | vi_retrieval_notes.md | data/vi_retrieval_notes.md | 1667 | department=engineering, language=vi, source_type=notes, date=2026-04-10 |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| department | string | engineering, support | Lọc theo phạm vi kiến thức đúng team, giảm nhiễu giữa kỹ thuật và CS |
| language | string | en, vi | Hỗ trợ truy vấn song ngữ, tránh trả nhầm ngôn ngữ |
| source | string | data/vector_store_notes.md | Trace nguồn để kiểm chứng answer grounding |
| source_type | string | notes, design, playbook, report | Hỗ trợ ưu tiên loại tài liệu phù hợp câu hỏi |
| date | string (ISO) | 2026-04-10 | Hỗ trợ lọc tài liệu mới/cũ |
| doc_id | string | vector_store_notes | Quản lý xóa/cập nhật theo document |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| All 6 docs | FixedSizeChunker (`fixed_size`) | 41 | 330.59 | Trung bình: ổn định độ dài nhưng có lúc cắt gãy ý |
| All 6 docs | SentenceChunker (`by_sentences`) | 32 | 367.00 | Khá tốt: dễ đọc, nhưng chunk có thể hơi dài/không đều |
| All 6 docs | RecursiveChunker (`recursive`) | 49 | 239.02 | Tốt nhất về cân bằng ngữ cảnh và giới hạn độ dài |

### Strategy Của Tôi

**Loại:** RecursiveChunker

**Mô tả cách hoạt động:**
> Strategy tách theo thứ tự ưu tiên từ separator lớn đến nhỏ (paragraph, newline, sentence boundary, space, fallback character-level). Nếu đoạn đang xét vẫn lớn hơn chunk_size, thuật toán đệ quy với separator tiếp theo. Cách này giữ được cấu trúc tài liệu khi có thể, nhưng vẫn đảm bảo chunk không vượt ngưỡng khi gặp đoạn dài. Đây là cơ chế cân bằng giữa coherence và retrieval coverage.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Bộ data gồm cả markdown theo mục, văn bản support dạng đoạn văn, và ghi chú tiếng Việt. RecursiveChunker khai thác được các boundary tự nhiên của từng loại văn bản thay vì ép theo chiều dài cố định. Trong benchmark, strategy này trả về đúng nhất ở query về pipeline 4 bước và thường giữ ngữ cảnh tốt trong top-3.

**Code snippet (nếu custom):**
```python
# Paste implementation here
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| All 6 docs | best baseline: SentenceChunker | 32 | 367.00 | Điểm tổng hợp cao nhất trong lượt chạy mock embedding (5.8/10) |
| All 6 docs | **của tôi: RecursiveChunker** | 49 | 239.02 | Cân bằng tốt, sát top baseline (5.4/10), mạnh ở query quy trình kỹ thuật |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi | | | | |
| [Tên] | | | | |
| [Tên] | | | | |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> Trong lần benchmark này với mock embedding, SentenceChunker nhỉnh hơn về điểm tổng hợp vì giữ câu đầy đủ cho nhiều query dạng policy/support. Tuy nhiên RecursiveChunker cho chất lượng ổn định hơn ở truy vấn kỹ thuật cần cấu trúc rõ. Khuyến nghị thực tế: dùng RecursiveChunker làm default, sau đó A/B test với SentenceChunker trên query set của nhóm.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Mình tách câu bằng regex `(?<=[.!?])\s+` để nhận ranh giới sau dấu kết thúc câu và gom theo `max_sentences_per_chunk`. Mỗi câu/chunk đều được `strip()` để tránh nhiễu do khoảng trắng. Edge cases được xử lý gồm text rỗng, text chỉ có whitespace, và trường hợp số câu không chia hết cho kích thước nhóm.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Thuật toán đệ quy tách văn bản theo danh sách separators ưu tiên từ lớn đến nhỏ (`\n\n`, `\n`, `. `, ` `, `""`). Base cases gồm: text rỗng, text đã nhỏ hơn hoặc bằng `chunk_size`, hoặc hết separator thì fallback tách theo cửa sổ ký tự cố định. Cách này giữ được cấu trúc tự nhiên khi có thể và chỉ “cắt cứng” khi thật sự cần.

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
============================= 42 passed in 0.10s ==============================
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Vector stores enable semantic search. | Vector databases support semantic retrieval. | high | 0.1139 | Đúng (tương đối) |
| 2 | Recursive chunking preserves context. | Python decorators modify function behavior. | low | 0.0037 | Đúng |
| 3 | Metadata filters improve retrieval precision. | Metadata tags help narrow search scope. | high | 0.0808 | Đúng (tương đối) |
| 4 | The assistant should escalate unknown billing issues. | When no billing guide exists, escalate to support. | high | 0.0949 | Đúng (tương đối) |
| 5 | Sentence chunking improves readability. | Nuclear fusion powers stars in distant galaxies. | low | 0.1096 | Sai |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Pair 5 gây bất ngờ vì dự đoán low nhưng score lại gần nhóm “high tương đối” trong bộ thử nghiệm này. Lý do là mình dùng mock embedding deterministic (không học ngữ nghĩa thật), nên điểm số không phản ánh semantic quality như model embedding thật. Điều này cho thấy khi đánh giá chất lượng semantic retrieval, nên ưu tiên backend embedding thật (Local/OpenAI) và benchmark theo task thực tế.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | What are the four stages of a typical vector search pipeline? | Chunk documents, embed each chunk, store vector+metadata, then embed query and rank by similarity. |
| 2 | Why can retrieval return the wrong audience procedures, and how should teams prevent that? | Mixed customer/support/engineering content causes wrong-scope retrieval; prevent with metadata separation and filtering. |
| 3 | Which chunking strategy showed the best balance in the experiment, and why? | Recursive chunking; it preserves larger structure first and falls back to finer separators to keep context while respecting size. |
| 4 | Vi sao metadata quan trong trong retrieval va bo loc co the giup nhu the nao? | Metadata giup loc theo phong ban, ngon ngu, do nhay cam va ngay cap nhat de tang precision, giam nhieu. |
| 5 | If no document explains a newly introduced billing issue, what should the assistant do? | Assistant should recommend escalation and state uncertainty instead of improvising a risky answer. |

### Thiết Lập Chạy Benchmark

- Embedding backend: mock
- top_k: 3
- Bộ dữ liệu: 6 tài liệu trong thư mục data
- So sánh công bằng: cùng query set, cùng top_k, cùng embedding backend cho cả 3 strategy

### Kết Quả Top-3 Theo Strategy

#### A) FixedSizeChunker (`fixed_size`)

| # | Query | Top-3 retrieved (nguồn chính) | Query Score (/10) |
|---|-------|-------------------------------|-------------------|
| 1 | Four stages pipeline | python_intro, rag_system_design, vi_retrieval_notes | 4 |
| 2 | Wrong audience procedures | rag_system_design, python_intro, vector_store_notes | 3 |
| 3 | Best chunking strategy | rag_system_design, chunking_experiment_report, chunking_experiment_report | 6 |
| 4 | Metadata utility (VI) | python_intro, rag_system_design, vector_store_notes | 5 |
| 5 | New billing issue fallback | vi_retrieval_notes, chunking_experiment_report, customer_support_playbook | 5 |

#### B) SentenceChunker (`by_sentences`)

| # | Query | Top-3 retrieved (nguồn chính) | Query Score (/10) |
|---|-------|-------------------------------|-------------------|
| 1 | Four stages pipeline | customer_support_playbook, customer_support_playbook, vector_store_notes | 3 |
| 2 | Wrong audience procedures | customer_support_playbook, python_intro, python_intro | 8 |
| 3 | Best chunking strategy | python_intro, chunking_experiment_report, chunking_experiment_report | 7 |
| 4 | Metadata utility (VI) | customer_support_playbook, python_intro, python_intro | 7 |
| 5 | New billing issue fallback | rag_system_design, customer_support_playbook, chunking_experiment_report | 4 |

#### C) RecursiveChunker (`recursive`)

| # | Query | Top-3 retrieved (nguồn chính) | Query Score (/10) |
|---|-------|-------------------------------|-------------------|
| 1 | Four stages pipeline | vector_store_notes, chunking_experiment_report, customer_support_playbook | 8 |
| 2 | Wrong audience procedures | vector_store_notes, vector_store_notes, customer_support_playbook | 6 |
| 3 | Best chunking strategy | chunking_experiment_report, vector_store_notes, vi_retrieval_notes | 5 |
| 4 | Metadata utility (VI) | chunking_experiment_report, rag_system_design, chunking_experiment_report | 4 |
| 5 | New billing issue fallback | customer_support_playbook, vi_retrieval_notes, python_intro | 4 |

### Chấm Điểm Theo Rubric Tự Đánh Giá

Thang điểm: trung bình 5 query, mỗi query chấm theo 5 tiêu chí (Retrieval Precision, Chunk Coherence, Metadata Utility, Grounding Quality, Data Strategy Fit), tổng tối đa 10 điểm/query.

| Strategy | Điểm trung bình (/10) | Nhận xét ngắn |
|----------|------------------------|---------------|
| FixedSizeChunker | 4.6 | Ổn định về kích thước nhưng dễ cắt mất ngữ cảnh quan trọng |
| SentenceChunker | 5.8 | Tốt nhất trong lượt chạy hiện tại, mạnh ở câu hỏi policy/support |
| RecursiveChunker | 5.4 | Cân bằng tốt, mạnh ở truy vấn kỹ thuật có cấu trúc |

### Kết Luận Retrieval

**Bao nhiêu queries trả về chunk relevant trong top-3?** 4 / 5

Trong lần chạy này, SentenceChunker đạt điểm cao nhất, nhưng chênh lệch với RecursiveChunker không lớn. RecursiveChunker vẫn là candidate tốt cho default strategy vì tính tổng quát trên dữ liệu mixed-format.

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
