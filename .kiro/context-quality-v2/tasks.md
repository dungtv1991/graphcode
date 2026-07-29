# Implementation Tasks — Context Quality v2

Ràng buộc: **không đổi embedding model** (Intel i5-1038NG7, CPU-only). Giữ
`paraphrase-multilingual-MiniLM-L12-v2`.

## Task 0: Chuẩn bị

- [ ] 0.1 Commit hoặc stash công việc BM25 đang dở trên branch `feat/binary` — hiện `mcp_server.py`, `requirements.txt`, `README.md` đang modified và `bm25_index.pkl`, `compare_models.py`, `.plan.md` untracked
- [ ] 0.2 Tạo branch `feat/context-quality-v2`
- [ ] 0.3 Backup `vector_db.pkl`, `bm25_index.pkl`, `knowledge_graph.json`, `file_hashes.json` sang `.backup/` (đã trong `.gitignore`)
- [ ] 0.4 Lưu baseline: chạy 10 query tiếng Việt đại diện, ghi top-5 vào `.kiro/context-quality-v2/baseline.json` để so sánh sau mỗi phase

---

## Phase 1 — Retrieval quality (không cần đụng graph)

### Task 1: BM25 tokenizer Unicode-safe

- [ ] 1.1 Thay `_tokenize_for_bm25` trong `mcp_server.py`: dùng `_BM25_WORD = re.compile(r'[^\W\d_]+|\d+', re.UNICODE)`, chỉ split camelCase khi `w.isascii() and w.isalpha()`
- [ ] 1.2 Rebuild `bm25_index.pkl` từ corpus hiện có (không re-embed)
- [ ] 1.3 Verify: query `"giỏ hàng thêm sản phẩm khuyến mãi"` — BM25 top-5 phải ra `CartItemPromotion` / `CartProduct` / `AddProductToCart*`, không còn `Price*`
- [ ] 1.4 Verify không regression: `"địa chỉ giao hàng tỉnh thành phố"` và `"lịch sử mua hàng đơn hàng"` phải giữ hoặc tốt hơn baseline

### Task 2: Reverse VI map cho query enrichment

- [ ] 2.1 Thêm `_build_vi_reverse_map()` sinh `{vi_phrase: english_keyword}` từ `VI_KEYWORDS`, cache trên function attribute
- [ ] 2.2 Thêm nhánh match phrase tiếng Việt vào `_enrich_query`, giữ nguyên nhánh ASCII hiện tại
- [ ] 2.3 Match n-gram dài trước ngắn (`"giỏ hàng"` trước `"hàng"`) để tránh khớp sai
- [ ] 2.4 Verify: `_enrich_query("giỏ hàng khuyến mãi")` phải chứa `Cart` và `Promotion` (hiện tại trả về nguyên văn, không enrich)

### Task 3: Consistency guard cho `build_db`

- [ ] 3.1 Thêm hằng `_DOC_SCHEMA_VERSION` và lưu vào `vector_db.pkl`
- [ ] 3.2 Thêm `_needs_full_rebuild()` kiểm 4 điều kiện: DB rỗng, dimension mismatch, doc schema đổi, coverage < 90%
- [ ] 3.3 Khi cần full rebuild → reset `hash_store = {}` và log lý do ra stderr
- [ ] 3.4 `build_db()` trả về coverage trong message, không chỉ `Done!`
- [ ] 3.5 Verify: xoá `vector_db.pkl` rồi gọi `build_db()` → phải re-embed đủ 8410 node, không phải chỉ phần diff

### Task 4: Document builder chung, vừa budget 128 token

- [ ] 4.1 Thêm `_split_identifier(name)` → `"CartItemPromotion"` thành `"Cart Item Promotion"`
- [ ] 4.2 Thêm `_leaf_path(rel)` → chỉ giữ repo name + file stem, bỏ thư mục trung gian
- [ ] 4.3 Thêm `_build_node_document(node_id, node_meta, rel_path)` theo D2: bỏ hẳn import lines và full path, giữ class name + VI keywords + summary + methods + api_paths
- [ ] 4.4 `build_db()` dùng `_build_node_document`; xoá hàm `_extract_class_window` và cache `_file_lines_cache` (không còn đọc file khi build)
- [ ] 4.5 `_incremental_rebuild()` dùng đúng `_build_node_document` — xoá đoạn `f.read(4096)` riêng
- [ ] 4.6 `_incremental_rebuild()` rebuild luôn `bm25_index.pkl` (hiện đang bỏ qua → BM25 lệch dần khỏi vector DB)
- [ ] 4.7 BM25 corpus dùng chung `_build_node_document` thay vì `f"{nid} {nid.replace('_',' ')} {vi}"`
- [ ] 4.8 Bump `_DOC_SCHEMA_VERSION` → full re-embed tự trigger
- [ ] 4.9 Verify token: document trung bình phải ≤128 token, không còn bị truncate (hiện tại 730 token, mất 82%)
- [ ] 4.10 Verify chất lượng: `CartItemPromotion` với query `"giỏ hàng thêm sản phẩm khuyến mãi"` phải vào **top-5** (baseline: rank 48/8410)
- [ ] 4.11 Verify tốc độ: full re-embed phải nhanh hơn baseline 4,7 phút (kỳ vọng ~1 phút vì document ngắn hơn)
- [ ] 4.12 Chạy lại 10 query baseline, so sánh, ghi kết quả vào spec

---

## Phase 2 — Node identity

### Task 5: Qualified node ID

- [ ] 5.1 `extract_graph.py`: đổi node `id` thành `{repo}/{path}::{ClassName}`, key của `file_mapping` theo ID mới
- [ ] 5.2 Sinh `alias_index` trong `knowledge_graph.json`: `{bare_name: [qualified_ids]}`
- [ ] 5.3 Bỏ field `repo` khỏi node record — derive từ segment đầu của path. Xoá loại bug `repo=khlc-fsell` nhưng `file=khlc-cart/...`
- [ ] 5.4 `save_results()`: bỏ dedup theo bare name (đang làm mất ~1.800 class định nghĩa, trong đó có `CartBloc`)
- [ ] 5.5 Edge resolution: khi target là bare name không resolve được unique, ưu tiên node cùng repo trước, rồi mới cross-repo
- [ ] 5.6 Chạy lại `extract_graph.py` (graph stale từ 29/05, 6.965 file .dart trên đĩa)
- [ ] 5.7 Verify: `CartBloc` phải có trong graph; 619 tên trùng phải thành 619 entry trong `alias_index` với đủ candidate
- [ ] 5.8 Verify dangling edge giảm từ 2.724/9.529 (28,6%)

### Task 6: Alias resolution trong tools

- [ ] 6.1 Thêm `_resolve_node(name) -> (candidates, is_ambiguous)` dùng `alias_index`
- [ ] 6.2 `get_blast_radius`: nếu ambiguous → trả danh sách candidate kèm repo + path, **không trộn** kết quả
- [ ] 6.3 Áp `_resolve_node` cho `find_similar_modules`, `get_file_content(class_name=...)`
- [ ] 6.4 Verify: `get_blast_radius("CustomerGateway")` phải trả 11 candidate để chọn, không trả 94 node trộn từ 11 class khác nhau
- [ ] 6.5 Re-embed + rebuild BM25 với node ID mới

---

## Phase 3 — Cross-repo

### Task 7: Barrel export expansion

- [ ] 7.1 Thêm `_RE_EXPORT` bắt `export '...'` kèm `hide` / `show` clause
- [ ] 7.2 Thêm `_build_barrel_map(root_dir, package_repo_map)` — parse mọi barrel, đệ quy khi export trỏ barrel khác, cache theo file
- [ ] 7.3 Xử lý export relative (`export 'src/foo.dart'`) và export package (`export 'package:khlc_x/...'`)
- [ ] 7.4 Thêm Strategy 0 vào `_resolve_import_to_class`: import trùng barrel → edge tới tất cả class barrel đó export
- [ ] 7.5 Gắn `"via": "barrel"` cho loại edge này; **loại trừ** khỏi `_trace_flow` để không làm nổ token, chỉ dùng cho blast radius
- [ ] 7.6 Verify: `imports_from` từ 33 lên ≥800 (có 977 import statement thật trên đĩa)
- [ ] 7.7 Verify `khlc-core/lib/khlc_core.dart` (43 export) resolve ra được danh sách class cụ thể

### Task 8: `public_api` flag + external boundary

- [ ] 8.1 Đánh dấu `visibility: "public" | "internal"` cho mỗi node — public = reachable từ barrel của repo mình
- [ ] 8.2 Tạo node stub `ExternalPackage` cho `app_core`, `app_ui`, `app_interface`, `app_notification`, `app_settings`, `app_tracking`, `app_authentication`, `app_badge_plus` (98 import, hiện hoàn toàn vô hình)
- [ ] 8.3 `get_blast_radius` trả kết luận sớm: `internal` → "0 cross-repo risk"; `public` → liệt kê repo import qua barrel
- [ ] 8.4 Verify: sửa 1 class internal trong `khlc-core` phải cho verdict "internal only" mà không cần đọc file nào

### Task 9: pubspec dependency graph

- [ ] 9.1 Mở rộng `_build_package_repo_map` đọc luôn block `dependencies:` → sinh `repo_deps` trong graph
- [ ] 9.2 Ghi nhận cả git dep (url + ref) để bắt được `app_*`
- [ ] 9.3 Cross-check: repo khai dep nhưng không import (dead dep) và import nhưng không khai (sẽ vỡ build)
- [ ] 9.4 `get_repo_coupling()` bổ sung layer pubspec song song với layer AST

### Task 10: Tool `get_change_impact`

- [ ] 10.1 Implement `get_change_impact(files: str, max_depth: int = 3)` — nhận output `git diff --name-only`
- [ ] 10.2 Map file → node → reverse traversal, group theo repo, xếp theo mức độ
- [ ] 10.3 Output gồm `verdict` (internal-only / cross-repo), `impact[]` với `via` + `public_nodes` + `dependents` + `risk`, và `regression_suggest[]`
- [ ] 10.4 Thêm vào `autoApprove` trong README mẫu mcp.json
- [ ] 10.5 Verify trên 1 commit thật đã biết phạm vi ảnh hưởng

---

## Phase 4 — Token & perf (độc lập, làm song song được)

### Task 11: Compact output

- [ ] 11.1 Đổi mọi `json.dumps(..., indent=2)` sang `separators=(',', ':')` ở `query_context`, `get_blast_radius`, `get_change_impact`
- [ ] 11.2 Trả `"root"` một lần, path còn lại relative
- [ ] 11.3 `query_context`: bỏ `flow_nodes` và `flow_files` (trùng với `graph`); thêm param `verbose: bool = False`
- [ ] 11.4 `get_blast_radius`: mặc định chỉ trả summary theo repo + type; liệt kê node khi `verbose=True`
- [ ] 11.5 Verify: `get_blast_radius("CustomerGateway")` từ ~5.000 token xuống <1.000 ở chế độ mặc định

### Task 12: Perf

- [ ] 12.1 `get_architecture_overview`: dựng `node_meta_map` một lần, thay mọi `next((n for n in nodes if ...))` — đo được 7,4s → 0,006s
- [ ] 12.2 `detect_communities`: cùng thay đổi
- [ ] 12.3 `search_by_filename`: bỏ vòng O(n²) check `in_graph`, dùng set dựng một lần
- [ ] 12.4 `grep_in_files` / `search_by_filename`: dùng `rg` qua subprocess nếu có trong PATH, fallback `os.walk`
- [ ] 12.5 Thêm `python-igraph` vào `requirements.txt`; bỏ `faiss-cpu` (không dùng ở đâu)

---

## Phase 5 — Housekeeping

### Task 13: Xoá code chết và rủi ro

- [ ] 13.1 **Revoke DeepSeek API key** `sk-12a37715...` hardcode trong `run.js`
- [ ] 13.2 Xoá `run.js`, `index.js` (ghi ra cùng tên `knowledge_graph.json` với schema không tương thích — chạy nhầm là phá graph)
- [ ] 13.3 Xoá `vector_context_manager.py`, `test_selector.py` (legacy, duplicate logic search)
- [ ] 13.4 Xoá `package.json` / `package-lock.json` / `node_modules` nếu chỉ phục vụ `index.js` — kiểm `tree-sitter-dart` có còn cần cho `dart_lang.so` không
- [ ] 13.5 Sửa `compare_models.py` thêm prefix `query:` / `passage:` cho E5, hoặc xoá — benchmark hiện tại thiếu prefix nên không kết luận được và dễ bị dùng làm căn cứ sai
- [ ] 13.6 Cân nhắc `.plan.md` (kế hoạch BM25 đã xong) → xoá hoặc chuyển vào `.kiro/`

### Task 14: Graph incremental update

- [ ] 14.1 Tách `parse_dart_file` thành entry point chạy được cho 1 file lẻ, trả về nodes/edges/file_mapping delta
- [ ] 14.2 Thêm `_incremental_graph_update(changed_files)` merge delta vào `knowledge_graph.json`
- [ ] 14.3 `watch_daemon` gọi cả graph update lẫn vector update (hiện chỉ cập nhật vector → graph stale 2 tháng)
- [ ] 14.4 Rebuild `alias_index` và adjacency index sau mỗi lần merge

### Task 15: Sync steering templates

- [ ] 15.1 Copy 4 file thiếu từ `khlc-mobile/.kiro/steering/` vào `steering_templates/khlc-mobile/`: `screen_business_logic.md`, `usecase_registry.md`, `data_model_mapping.md`, `inter_module_dependency_map.md`
- [ ] 15.2 Kiểm routing table trong `AGENTS.md` khớp với file thực có
- [ ] 15.3 Verify `init_steering()` cho 1 repo mới tạo đủ file

### Task 16: Docs

- [ ] 16.1 Cập nhật `README.md`: thêm `get_change_impact`, ghi rõ ràng buộc không đổi model, cập nhật bảng env vars
- [ ] 16.2 Ghi kết quả đo trước/sau của từng phase vào spec này

---

## Tiêu chí hoàn thành

| Chỉ số | Baseline (đo được) | Mục tiêu |
|---|---|---|
| BM25 top-5 với query tiếng Việt | `Price*` (sai) | Cart-related (đúng) |
| `CartItemPromotion` rank cho `"giỏ hàng..."` | 48/8410 | top-5 |
| Token bị truncate mỗi document | 602/730 (82%) | 0 |
| Full re-embed 8410 node | 4,7 phút | ≤1,5 phút |
| `imports_from` edge | 33 | ≥800 |
| Dangling edge | 2.724/9.529 (28,6%) | <5% |
| Class name trùng gây mất định nghĩa | 619 tên, ~1.800 class mất | 0 |
| `get_blast_radius("CustomerGateway")` | 94 node trộn từ 11 class | 11 candidate để chọn |
| Token `get_blast_radius` mặc định | ~5.000 | <1.000 |
| `get_architecture_overview` edge mapping | 7,4s | <0,1s |
| Trả lời "sửa X ảnh hưởng repo nào" | không làm được | `get_change_impact` |
