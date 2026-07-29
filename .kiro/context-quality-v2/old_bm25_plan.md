# Plan: BM25 + Hybrid Search

## Overview
Thêm BM25 keyword search kết hợp semantic search thành hybrid, dùng Reciprocal Rank Fusion (RRF) merge.

## Files sửa
- `requirements.txt` — thêm `rank_bm25`
- `mcp_server.py` — thêm BM25 index + hybrid search

## Chi tiết

### 1. `requirements.txt`
Thêm dòng: `rank_bm25>=0.2.2`

### 2. `mcp_server.py` — thêm BM25 vào `build_db()` (sau dòng 591)
- Tokenize tất cả documents (dùng chung document string đã tạo cho embedding)
- Tạo `BM25Okapi` index
- Lưu `bm25_index.pkl`: `{"bm25": BM25Okapi, "node_ids": list[str]}`

### 3. `mcp_server.py` — thêm helper functions (trước `_vector_search`)
- `_tokenize_for_bm25(text)`: split camelCase/snake_case, lowercase, ≥2 chars
- `_bm25_search(query, top_k)`: BM25 search → `[(node_id, score)]`
- `_rrf_merge(semantic_ids, bm25_ids, k=60)`: RRF → merged list

### 4. `mcp_server.py` — sửa `_vector_search()` (dòng 292-329)
- Chạy semantic search (hiện tại) → pool_idx
- Chạy BM25 search → bm25_ids
- RRF merge 2 kết quả → combined pool
- Lexical re-rank giữ nguyên trên combined pool

### 5. `_State` — thêm `bm25_index` (lazy load)

## Flow mới
```
Query → Semantic (cosine) → Top-K pool
      → BM25 (keyword)    → Top-K pool
      → RRF Merge → combined
      → Lexical re-rank (class name boost)
      → Graph expansion
```

## Không thay đổi
- extract_graph.py, embedding_provider.py
- Graph traversal, output format, incremental rebuild
