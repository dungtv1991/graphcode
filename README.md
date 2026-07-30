# 🧠 Flutter Context MCP Server

Knowledge Graph + Semantic Search cho hệ thống AI Agent phát triển KHLC Mobile.

---

## Tổng quan

MCP Server cung cấp context chính xác cho AI Agent khi code Flutter:
- **Semantic search** — tìm file theo ý nghĩa (tiếng Việt + Anh)
- **Knowledge Graph** — trace dependency, blast radius, cross-repo imports
- **Auto-update** — watch daemon tự rebuild khi code thay đổi

```
User Query → Vector Search → Graph Expand → Context cho Agent
```

---

## Cài đặt

```bash
# 1. Clone và setup
cd /Users/dungtv54/FPT/graphcode
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Build knowledge graph (lần đầu)
python3 extract_graph.py

# 3. Build vector DB
# Gọi tool build_db() qua MCP, hoặc:
python3 -c "from mcp_server import build_db; print(build_db())"
```

---

## Chạy server

### Stdio (mặc định — dùng với Kiro/IDE)
```bash
python3 mcp_server.py
```

### SSE (nhiều client cùng lúc)
```bash
FLUTTER_CONTEXT_TRANSPORT=sse FLUTTER_CONTEXT_PORT=8765 python3 mcp_server.py
```

### Với auto-rebuild (watch daemon)
```bash
FLUTTER_CONTEXT_WATCH=1 python3 mcp_server.py
```

---

## Cấu hình MCP trong Kiro

File `~/.kiro/settings/mcp.json`:
```json
{
  "mcpServers": {
    "flutter-context": {
      "command": "/Users/dungtv54/FPT/graphcode/venv/bin/python3",
      "args": ["/Users/dungtv54/FPT/graphcode/mcp_server.py"],
      "env": {},
      "disabled": false,
      "autoApprove": [
        "query_context", "get_file_content", "grep_in_files",
        "search_by_filename", "search_by_api_path", "search_by_error_type",
        "list_nodes", "build_db", "get_blast_radius", "get_change_impact",
        "find_similar_modules", "detect_communities",
        "get_architecture_overview", "get_repo_coupling"
      ]
    }
  }
}
```

---

## Tools

| Tool | Mô tả |
|------|--------|
| `query_context` | Semantic search + graph trace — entry point chính |
| `get_file_content` | Đọc file với line numbers, jump đến class |
| `grep_in_files` | Full-text search trong source code |
| `search_by_filename` | Tìm file theo tên |
| `search_by_api_path` | Tìm code xử lý API endpoint |
| `search_by_error_type` | Tìm nơi throw/catch exception |
| `get_blast_radius` | Phân tích ảnh hưởng khi sửa 1 class |
| `get_change_impact` | Đánh giá impact từ `git diff --name-only` → verdict + repos bị ảnh hưởng |
| `find_similar_modules` | Tìm module tương tự làm template |
| `detect_communities` | Phát hiện nhóm code liên quan |
| `get_architecture_overview` | Hub nodes, bridge nodes, coupling |
| `get_repo_coupling` | Dependency matrix giữa repos + circular detection |
| `list_nodes` | Liệt kê nodes trong graph |
| `build_db` | Rebuild vector DB (incremental) |
| `init_steering` | Tạo steering files cho project mới |
| `check_steering` | Kiểm tra steering đã có chưa |
| `call_api` | Gọi HTTP API test |

---

## Thêm repo mới

Khi có repo `khlc-*` mới cần index:

### 1. Clone repo vào đúng vị trí
```bash
cd /Users/dungtv54/FPT
git clone <url> khlc-ten-repo
```

> ⚠️ Repo phải nằm cùng cấp với các `khlc-*` khác trong `/Users/dungtv54/FPT/`

### 2. Rebuild knowledge graph
```bash
cd /Users/dungtv54/FPT/graphcode
python3 extract_graph.py
```

Script tự scan tất cả `khlc-*/lib/` directories, parse AST, tạo nodes + edges.

### 3. Rebuild vector DB

Gọi tool `build_db()` qua MCP (trong Kiro chat), hoặc:
```bash
python3 -c "from mcp_server import build_db; print(build_db())"
```

### 4. Reconnect MCP server

Trong Kiro: `Cmd+Shift+P` → "Reconnect MCP Servers"

### Checklist repo mới
- [ ] Repo tên `khlc-*` và nằm trong `/Users/dungtv54/FPT/`
- [ ] Có folder `lib/` chứa source code
- [ ] Có `pubspec.yaml` với field `name:` (để resolve cross-repo imports)
- [ ] Chạy `python3 extract_graph.py` thành công
- [ ] Chạy `build_db()` thành công
- [ ] `query_context("tên feature trong repo mới")` trả kết quả

---

## Cập nhật khi code thay đổi

### Tự động (khuyến nghị)
Bật watch daemon:
```bash
FLUTTER_CONTEXT_WATCH=1 python3 mcp_server.py
```
Mỗi khi file `.dart` thay đổi → debounce 3s → auto rebuild vector DB.

### Thủ công
Gọi `build_db()` — chỉ re-embed file đã thay đổi (incremental, ~2-5s).

### Full rebuild (khi đổi embedding model)
Xoá `file_hashes.json` rồi gọi `build_db()`:
```bash
rm file_hashes.json
python3 -c "from mcp_server import build_db; print(build_db())"
```

---

## Environment Variables

| Biến | Mô tả | Default |
|------|--------|---------|
| `FLUTTER_CONTEXT_TRANSPORT` | `stdio` hoặc `sse` | `stdio` |
| `FLUTTER_CONTEXT_PORT` | Port cho SSE mode | `8765` |
| `FLUTTER_CONTEXT_WATCH` | Bật watch daemon (`1`/`true`) | off |
| `FLUTTER_CONTEXT_TOOLS` | Comma-separated tool names để expose | all |
| `EMBEDDING_MODEL` | Tên SentenceTransformer model | `paraphrase-multilingual-MiniLM-L12-v2` |
| `OPENAI_API_KEY` | Dùng OpenAI embeddings thay local | — |
| `AZURE_OPENAI_ENDPOINT` | Dùng Azure OpenAI embeddings | — |
**Ưu tiên embedding**: Azure > OpenAI > Local (SentenceTransformer)

> ⚠️ **Ràng buộc**: Không đổi embedding model. Máy Intel i5-1038NG7 CPU-only, giữ `paraphrase-multilingual-MiniLM-L12-v2` (max_seq_length=128 token). Document được thiết kế vừa budget này.

---

## Kiến trúc file

```
graphcode/
├── mcp_server.py           # MCP Server chính — tất cả tools
├── extract_graph.py        # Parser AST (tree-sitter) → knowledge graph
├── embedding_provider.py   # Abstraction layer cho embedding models
├── watch_daemon.py         # File watcher + debounce rebuild
├── vector_context_manager.py  # Standalone context selector (legacy)
├── knowledge_graph.json    # Graph data: nodes + edges + file_mapping
├── vector_db.pkl           # Embedding vectors
├── file_hashes.json        # SHA-256 hashes cho incremental rebuild
├── dart_lang.so            # Tree-sitter Dart grammar (compiled)
├── requirements.txt        # Python dependencies
└── steering_templates/     # Workflow templates cho IDE
```

---

## Graph Edge Types

| Edge | Ý nghĩa |
|------|---------|
| `depends_on` | Class A inject/dùng Class B |
| `binds` | Module bind UseCase/Repository |
| `routes_to` | Module route đến Module khác |
| `has_part` | Bloc có Event/State files |
| `imports_from` | Cross-repo import |
| `implements` | Class implement interface |
| `tested_by` | Class có test file tương ứng |
| `similar_to` | Modules có cấu trúc tương tự |

---

## Troubleshooting

**MCP không connect được**
```bash
# Test thủ công
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | python3 mcp_server.py
```

**Tree-sitter lỗi**
```bash
# Rebuild grammar
rm dart_lang.so
python3 -c "from extract_graph import *; print('OK')"
```

**Vector DB dimension mismatch**
```bash
rm vector_db.pkl file_hashes.json
# Rồi gọi build_db()
```

**Kill process cũ**
```bash
ps aux | grep mcp_server.py | grep -v grep | awk '{print $2}' | xargs kill
```
