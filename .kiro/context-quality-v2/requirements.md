# Requirements — Context Quality v2

## Bối cảnh

`graphcode` đang chạy được nhưng chất lượng retrieval bị 3 lỗi mà query log không phát hiện
được, vì query vẫn trả về *kết quả* — chỉ là kết quả sai. Toàn bộ số liệu dưới đây được đo
trực tiếp trên máy, không phải suy đoán.

**Ràng buộc cứng: KHÔNG đổi embedding model.** Máy là Intel Core i5-1038NG7 @ 2.00GHz,
CPU-only, không có GPU/MPS. Giữ `paraphrase-multilingual-MiniLM-L12-v2`. Mọi cải thiện phải
đến từ tokenizer, cấu trúc document, và graph — không từ model.

Throughput đo được trên máy này (MiniLM, batch_size=32):

| Loại document | docs/s | Re-embed 8410 node |
|---|---|---|
| dài (~1.700 chars) | 29,8 | **4,7 phút** |
| ngắn (~150 chars) | 151,1 | **0,9 phút** |

→ Document ngắn hơn vừa chính xác hơn vừa nhanh gấp 5×. Phase 1 là **bỏ việc**, không thêm việc.

---

## R1 — BM25 phải hoạt động với tiếng Việt

**Hiện tại:** `_tokenize_for_bm25` dùng regex
`r'[A-Za-z_][A-Za-z0-9_]*|[^\s\W]+'`. Alternative đầu match greedy từ trái nên **cắt từ
tiếng Việt tại dấu thanh đầu tiên**.

```
"giỏ hàng thêm sản phẩm khuyến mãi"
→ ['gi','h','àng','th','êm','s','ản','ph','ẩm','khuy','ến','m','ãi']
```

BM25 khớp fragment vô nghĩa (`ph`, `m`, `th`, `gi`) với sub-token camelCase của tên class:

| | top-5 |
|---|---|
| hiện tại | `PricePromotionTag`, `PriceX`, `ProductPricePromotionTag`, `PriceWidget`, `PriceEntity` — score ~25, **sai hoàn toàn** |
| sau khi sửa regex | `CartItemPromotion`, `CartProduct`, `CartItemPriceInfoCard`, `AddProductToCartParam`, `AddProductToCartResource` — **đúng** |

Đã verify bằng cách build lại BM25 index với tokenizer sửa trên đúng corpus hiện tại.

**Yêu cầu:** token tiếng Việt giữ nguyên nguyên vẹn. Chỉ split camelCase/snake_case với
token ASCII. BM25 tiếng Việt phải bằng hoặc tốt hơn dense-only.

---

## R2 — Document phải vừa budget 128 token

**Phát hiện gốc:** `MiniLM.max_seq_length = 128 tokens`. Document `CartItemPromotion` dài
730 token → **602 token (82%) bị âm thầm bỏ đi**.

Phân bổ 128 token thực tế được embed:

| Thành phần | Tokens | Giá trị |
|---|---|---|
| `File: khlc-cart/lib/src/features/cart/presentation/widgets/cart_item_promotiion.dart` | **40** | noise — path components trùng lặp giữa hàng nghìn file |
| `import 'package:flutter/material.dart'; import 'package:khlc_core/...'` | **67** | noise — gần như mọi file Dart đều có |
| `Mô tả: giỏ hàng, thêm vào giỏ, xem giỏ hàng, khuyến mãi...` | 30 | **tín hiệu duy nhất** |
| `Methods:` / `Events:` / `API paths:` | 0 | **bị cắt hết** |
| class body | 0 | **không bao giờ được embed** |

→ **107/128 token (84%) đốt vào noise.**

Hệ quả đo được: `CartItemPromotion` có `Mô tả` khớp gần như từng chữ với query
`"giỏ hàng thêm sản phẩm khuyến mãi"` nhưng chỉ đạt **rank 48/8410, cos 0.4574**, so với
top-1 `ProductPricePromotionTag` cos 0.5335. Với `top_k=5` (giá trị thực tế trong log) node
đúng không bao giờ lên.

**Yêu cầu:** document ≤128 token, không chứa import, không chứa full path. Ưu tiên
`class name` → `VI keywords` → `summary` → `methods` → `api_paths`.

---

## R3 — `_enrich_query` phải chạy với query tiếng Việt

`re.findall(r'[A-Za-z][A-Za-z0-9]*', "giỏ hàng thêm...")` → `['gi','h','th','m',...]`,
không khớp key nào của `VI_KEYWORDS` (toàn tiếng Anh). Verified: `_enrich_query(q) == q`.

`VI_KEYWORDS` (~150 entry) chỉ hoạt động **một chiều**: class name → VI, phía document.
Phía query không có map ngược.

**Yêu cầu:** build reverse index từ chính `VI_KEYWORDS`, không thêm dữ liệu mới.

---

## R4 — Node identity phải unique; `get_blast_radius` không được trả kết quả sai

619 tên class được định nghĩa ở nhiều file (`InitialState` ×17, `Assets` ×19,
`CustomerGateway` ×11). `save_results()` dedup theo `id` → mất ~1.800 class định nghĩa.
`CartBloc` **không tồn tại** trong vector DB dù có 121 node chứa "Cart".

`get_blast_radius("CustomerGateway")` trả 94 node / 9 repo — nhưng đó là hợp của **11 class
khác nhau**. Bằng chứng corruption trong output live, `repo` và `file` mâu thuẫn:

| node | repo báo | file thật |
|---|---|---|
| `ProfileModule` | khlc-profile | `khlc-vaccine/lib/src/features/profile/...` |
| `HomeModule` | khlc-247 | `khlc-mobile/lib/src/features/home/...` |
| `FsellRemoteDatasource` | khlc-fsell | `khlc-cart/lib/src/features/fsell/...` |
| `FsellRepositoryImpl` | khlc-fsell | `khlc-cart/lib/src/features/fsell/...` |

Nguyên nhân: `repo` lấy từ node record (dedup → first-seen wins), `file` lấy từ
`file_mapping` (last-write wins). Hai nguồn không đồng bộ.

**Yêu cầu:** node ID unique. Tool vẫn nhận tên trần làm input, nhưng khi ambiguous phải trả
danh sách disambiguation thay vì trộn.

---

## R5 — Cross-repo impact phải đo được

| Chỉ số | Hiện tại |
|---|---|
| `imports_from` edge | **33** |
| import cross-repo thật trên đĩa | **977** |
| coverage | **~3%** |

Nguyên nhân: 99% import là barrel (`package:khlc_core/khlc_core.dart` ×582; deep-path chỉ
×5). `_resolve_import_to_class` fail cả 2 strategy vì `khlc_core.dart` chỉ chứa 43 `export`,
không có class nào.

Thiếu thêm:
- Layer `app_*` (`app_core`, `app_ui`, `app_interface`, `app_notification` — git dep từ
  git2.fptshop.com.vn) hoàn toàn vô hình: 98 import trực tiếp, `scan_all_repos()` chỉ nhận `khlc-*`
- `pubspec.yaml` chỉ đọc field `name:`, không dùng làm dependency graph
- Không có khái niệm public API (export ra barrel) vs internal
- 2.724/9.529 edge (**28,6%**) dangling — `get_architecture_overview` báo `total_edges: 6805`
  vs 9529 trong file, phần chênh bị drop im lặng

**Yêu cầu:** trả lời được "sửa file X ảnh hưởng repo nào, mức độ nào" với căn cứ kiểm chứng được.

---

## R6 — Token output phải tương xứng

- `get_blast_radius("CustomerGateway")` ≈ **5.000 token / 1 lần gọi** (94 entry × 53 token,
  `indent=2`, path tuyệt đối lặp prefix `/Users/dungtv54/FPT/`). Dạng compact → ~3.850 (**-23%**)
- `query_context` trùng dữ liệu 3 chỗ: `files` / `flow_files` / `flow_nodes`. Test thực
  `top_k=3` vẫn trả 3 files + 15 `flow_files` + 18 `flow_nodes` + graph 16 dòng
- `snippet_chars=0` không tiết kiệm gì vì `summary` luôn có sẵn

---

## R7 — Không được có 2 đường build tạo document khác nhau

`_incremental_rebuild` (watch daemon) và `build_db` tạo document **khác format**:

| | `build_db` | `_incremental_rebuild` |
|---|---|---|
| content | class window 120 dòng | `f.read(4096)` từ đầu file |
| methods/events/api | có | **không** |
| rebuild BM25 | có | **không** |

→ BM25 index lệch dần khỏi vector DB mỗi lần watch daemon chạy. Node nào được watch daemon
cập nhật thì mất metadata và mất vị trí class window.

Thêm: không có consistency guard. `file_hashes.json` đầy nhưng vector DB rỗng → `build_db()`
chỉ embed phần diff rồi in `Done!` như thành công (đã xảy ra ở bản `graph-code-flutter`:
569/8410 = 6,8% coverage).

---

## R8 — Housekeeping

- `igraph 1.0.0` đã cài trong venv nhưng **không có trong `requirements.txt`** → máy mới mất
  `detect_communities` + `get_architecture_overview`
- `faiss-cpu` có trong requirements nhưng không dùng ở đâu
- Linear scan trong loop ở `get_architecture_overview` / `detect_communities`: đo **7,4s**
  riêng phần map edge vs **0,006s** dùng dict (~1200×)
- `search_by_filename` O(n²): mỗi file match lại quét toàn bộ 8410 `file_mapping`
- `index.js` ghi ra cùng tên `knowledge_graph.json` với schema không tương thích
- `run.js` hardcode DeepSeek API key `sk-12a37715...` → cần revoke
- `vector_context_manager.py`, `test_selector.py` legacy, duplicate logic
- `compare_models.py` so MiniLM vs `multilingual-e5-small` **không có prefix `query:`/`passage:`**
  → benchmark không kết luận được (giữ lại nhưng phải sửa hoặc xoá để tránh dùng làm căn cứ sai)
- `knowledge_graph.json` từ 29/05 — 2 tháng. `extract_graph.py` chỉ full-rebuild; watch daemon
  chỉ cập nhật vector, **không cập nhật graph**
- `steering_templates/khlc-mobile/` thiếu 4 file routing table cần:
  `screen_business_logic.md`, `usecase_registry.md`, `data_model_mapping.md`,
  `inter_module_dependency_map.md` (đã có trong `khlc-mobile/.kiro/steering/`, chưa sync)

---

## Ngoài scope

- Đổi embedding model (E5, BGE-M3, jina) — máy Intel CPU-only, giữ MiniLM
- Cross-encoder reranker — quá chậm trên CPU này
- Method-level AST chunking — sẽ đẩy vector count lên ~50k, cân nhắc sau khi Phase 1–3 xong
- FAISS/ANN — 8410 vector brute-force matmul vẫn dưới 5ms, chưa cần
