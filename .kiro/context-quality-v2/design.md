# Design — Context Quality v2

Nguyên tắc: giữ `paraphrase-multilingual-MiniLM-L12-v2`. Mọi thay đổi phải hoặc giảm việc
cho CPU, hoặc giữ nguyên. Không thêm model, không thêm inference pass.

---

## D1 — Tokenizer Unicode-safe (`mcp_server.py`)

Vấn đề là alternative đầu `[A-Za-z_][A-Za-z0-9_]*` match greedy từ trái, cắt từ tiếng Việt.
Thay bằng một class ký tự chữ Unicode duy nhất, rồi mới split camelCase **chỉ khi** token
thuần ASCII.

```python
_BM25_WORD = re.compile(r'[^\W\d_]+|\d+', re.UNICODE)

def _tokenize_for_bm25(text: str) -> list[str]:
    tokens = []
    for w in _BM25_WORD.findall(text):
        wl = w.lower()
        if len(wl) >= 2:
            tokens.append(wl)
        # chỉ split camelCase cho identifier ASCII — tiếng Việt giữ nguyên
        if w.isascii() and w.isalpha():
            for p in re.sub(r'([a-z])([A-Z])', r'\1 \2', w).split():
                pl = p.lower()
                if len(pl) >= 2 and pl != wl:
                    tokens.append(pl)
    return tokens
```

`[^\W\d_]+` = "ký tự chữ, không phải số, không phải `_`" — bao gồm toàn bộ chữ có dấu.
Snake_case tự nhiên bị `_` tách sẵn nên không cần nhánh riêng.

Không cần re-embed. Chỉ rebuild `bm25_index.pkl` từ corpus có sẵn — vài giây.

---

## D2 — Document builder chung, vừa budget 128 token

Hiện tại có 2 chỗ tạo document (`build_db` và `_incremental_rebuild`) với format khác nhau.
Gộp thành một hàm duy nhất, và thiết kế lại nội dung theo budget.

```python
def _build_node_document(node_id: str, node_meta: dict, rel_path: str) -> str:
    """Document cho embedding + BM25. Mục tiêu <=128 token của MiniLM.

    Bỏ hẳn: full path (40 tok noise), import lines (67 tok noise), class body.
    Giữ: tên class, VI keywords, summary, methods, api_paths — toàn bộ là tín hiệu.
    """
    parts = [node_id, _split_identifier(node_id)]        # "CartItemPromotion" + "Cart Item Promotion"

    vi = _enrich_vi_keywords(node_id)
    if vi:
        parts.append(vi)

    if node_meta.get("summary"):
        parts.append(node_meta["summary"])               # "Widget | extends StatelessWidget | fn:..."

    parts.append(_leaf_path(rel_path))                   # "khlc-cart" + "cart_item_promotiion" thôi

    for key in ("methods", "events", "api_paths"):
        vals = node_meta.get(key) or []
        if vals:
            parts.append(f"{key}: {', '.join(vals[:6])}")

    return " | ".join(p for p in parts if p)
```

Hai helper:
- `_split_identifier("CartItemPromotion")` → `"Cart Item Promotion"` — giúp cả dense lẫn BM25
- `_leaf_path("khlc-cart/lib/src/features/cart/presentation/widgets/cart_item_promotiion.dart")`
  → `"khlc-cart cart_item_promotiion"` — giữ repo + tên file, bỏ 6 tầng thư mục trung gian

Path đầy đủ và line number vẫn nằm trong `file_mapping` / metadata để `query_context` trả về —
chỉ là **không đưa vào text đi embed**.

Ước tính token sau thay đổi: ~45–70 token/document, nằm gọn trong budget. Không còn truncation.

**Chi phí:** full re-embed 8410 node. Document ngắn → ~1 phút trên máy này (so với 4,7 phút
với document dài hiện tại). Cộng rebuild BM25.

**Đo lại sau khi làm:** `CartItemPromotion` với query `"giỏ hàng thêm sản phẩm khuyến mãi"`
phải vào top-5 (baseline hiện tại: rank 48).

---

## D3 — Reverse VI map cho query

`VI_KEYWORDS` đã có sẵn dữ liệu, chỉ thiếu chiều ngược. Build một lần, cache trên function
attribute như `_enrich_query` đang làm.

```python
def _build_vi_reverse_map() -> dict[str, str]:
    """{"giỏ hàng": "Cart", "thanh toán": "Payment", ...} — từ chính VI_KEYWORDS."""
    rev = {}
    for eng, vi_str in VI_KEYWORDS.items():
        for phrase in (p.strip().lower() for p in vi_str.split(",")):
            if phrase and phrase not in rev:
                rev[phrase] = eng
    return rev
```

Trong `_enrich_query`: giữ nhánh ASCII hiện tại, thêm nhánh match phrase tiếng Việt trên
query đã lowercase. Match n-gram dài trước (`"giỏ hàng"` trước `"hàng"`) để tránh khớp sai.
Append các English keyword tìm được vào query — vừa giúp dense (tên class là tiếng Anh) vừa
giúp BM25.

---

## D4 — Qualified node ID + alias resolution

Node ID mới: `{repo}/{path}::{ClassName}`. `file_mapping` key theo ID mới. Thêm alias index:

```python
# knowledge_graph.json thêm 1 field
"alias_index": {
    "CartBloc": ["khlc-cart/lib/.../cart_bloc.dart::CartBloc"],
    "CustomerGateway": [
        "khlc-sso-integration/lib/src/gateway/customer_gateway.dart::CustomerGateway",
        "khlc-payment/lib/gateway/customer.dart::CustomerGateway",
        ...  # 11 entry
    ]
}
```

Contract của tool giữ nguyên — vẫn nhận tên trần:

```python
def _resolve_node(name: str) -> tuple[list[str], bool]:
    """Trả (candidates, is_ambiguous). Tool tự quyết cách xử lý."""
```

- 1 candidate → xử lý bình thường
- nhiều candidate → **không trộn**. Trả về danh sách kèm repo + path để agent chọn:
  ```json
  {"ambiguous": "CustomerGateway", "candidates": [
     {"id": "khlc-payment/lib/gateway/customer.dart::CustomerGateway", "repo": "khlc-payment"},
     ...
  ], "hint": "Truyền id đầy đủ để phân tích chính xác"}
  ```

Đồng thời bỏ hẳn nguồn `repo` từ node record — luôn derive từ segment đầu của path. Xoá được
loại bug `repo=khlc-fsell` nhưng `file=khlc-cart/...`.

**Chi phí:** chạy lại `extract_graph.py` (graph đã stale 2 tháng, cần chạy lại kiểu gì cũng phải),
rồi full re-embed + BM25 rebuild (~1 phút).

---

## D5 — Barrel export expansion

Đây là mấu chốt của cross-repo. Thêm bước resolve barrel trước khi resolve import.

```python
def _build_barrel_map(root_dir, package_repo_map) -> dict[str, list[str]]:
    """{"khlc_core/khlc_core.dart": [danh sách rel_path mà barrel này export]}

    Đọc mọi export trong file barrel, đệ quy nếu export lại trỏ tới barrel khác.
    Tôn trọng `hide` / `show`. Cache theo file để không parse lại.
    """
```

Xử lý 3 dạng export gặp trong `khlc-core/lib/khlc_core.dart`:
1. `export 'src/foo/bar.dart';` — relative, resolve trong cùng repo
2. `export 'package:khlc_x/...';` — trỏ repo khác, đệ quy
3. `export 'package:app_core/app_core.dart' hide DefaultStorage, ...;` — package ngoài,
   ghi nhận là **external boundary node** (xem D6)

Sau đó `_resolve_import_to_class` thêm Strategy 0: nếu import path trùng barrel đã biết →
tạo edge tới **tất cả** class mà barrel đó export. Để tránh bùng nổ edge, gắn thêm
`"via": "barrel"` và **không** dùng loại edge này cho `_trace_flow` (chỉ dùng cho
`get_blast_radius` / `get_change_impact`).

Mục tiêu kiểm chứng: `imports_from` từ 33 lên ≥800 (có 977 import statement thật).

---

## D6 — `public_api` flag + external boundary

Mỗi node được đánh dấu khi build graph:

```python
"visibility": "public"    # reachable từ barrel của repo mình
"visibility": "internal"  # không export ra ngoài
```

Node cho package `app_*` không có source trên đĩa → tạo node stub:

```python
{"id": "app_core::__external__", "type": "ExternalPackage", "repo": "app_core",
 "source": "git2.fptshop.com.vn", "indexed": false}
```

Giá trị: `get_blast_radius` kết luận được **mà không cần đọc file nào**:
- `visibility: internal` → "0 cross-repo risk, chỉ ảnh hưởng trong repo X"
- `visibility: public` → "public API, N repo import qua barrel"

Đây là phần tiết kiệm token lớn nhất — agent bỏ được cả bước đọc file để tự suy luận.

---

## D7 — pubspec dependency graph

Layer thô, độc lập với AST, không phụ thuộc parse đúng. Chạy trong `extract_graph.py`:

```python
"repo_deps": {
    "khlc-mobile": {"khlc_core": "git@...#ref", "khlc_cart": "...", ...},   # 21 dep
    "khlc-cart":   {...},                                                    # 5 dep
}
```

Dùng để: cross-check kết quả AST, phát hiện repo khai dep nhưng không import (dead dep) và
ngược lại (import không khai — sẽ vỡ build), và bắt được cả `app_*`.

---

## D8 — Tool mới `get_change_impact`

```python
@mcp.tool()
def get_change_impact(files: str, max_depth: int = 3) -> str:
    """Nhận danh sách file đã sửa (output của `git diff --name-only`), trả về
    repo bị ảnh hưởng, xếp theo mức độ, kèm public/internal.
    """
```

Output thiết kế để gọn (dạng compact, xem D9):

```json
{
  "changed": {"files": 3, "nodes": 7},
  "verdict": "cross-repo",
  "impact": [
    {"repo": "khlc-mobile", "via": "barrel", "public_nodes": 2, "dependents": 14, "risk": "high"},
    {"repo": "khlc-cart",   "via": "direct", "public_nodes": 0, "dependents": 3,  "risk": "low"}
  ],
  "internal_only": ["khlc-247"],
  "regression_suggest": ["khlc-mobile", "khlc-cart"]
}
```

Đây là thứ workflow trong `AGENTS.md` cần ở SESSION 1 (đánh giá blast radius) và SESSION VERIFY
(kiểm `git diff` có vượt spec không).

---

## D9 — Compact output

Áp cho `query_context`, `get_blast_radius`, `get_change_impact`:

- `json.dumps(..., separators=(',', ':'))` — bỏ `indent=2`
- Trả `"root": "/Users/dungtv54/FPT"` **một lần**, path còn lại là relative
- Bỏ `flow_nodes` (đã nằm trong `graph` string), bỏ `flow_files` (derive được từ `graph`)
- Thêm param `verbose: bool = False`; mặc định chỉ trả `files` + `graph`
- `get_blast_radius`: mặc định trả summary theo repo + type, chỉ liệt kê node khi `verbose=True`

Mục tiêu: `get_blast_radius("CustomerGateway")` từ ~5.000 token xuống <1.000 ở chế độ mặc định.

---

## D10 — Consistency guard

Trong `build_db()`, trước khi tính diff:

```python
def _needs_full_rebuild() -> tuple[bool, str]:
    if _State.db is None or len(_State.db.get("metadata", [])) == 0:
        return True, "vector DB rỗng"
    if _State.db["embeddings"].shape[1] != _State.model.dimension:
        return True, "dimension mismatch"
    if _State.db.get("doc_schema") != _DOC_SCHEMA_VERSION:
        return True, "document schema đổi"
    coverage = len(_State.db["metadata"]) / max(len(_State.file_mapping), 1)
    if coverage < 0.9:
        return True, f"coverage chỉ {coverage:.0%}"
    return False, ""
```

Full rebuild → `hash_store = {}`. Thêm `doc_schema` vào `vector_db.pkl` để mọi lần đổi
document format tự trigger re-embed, không cần nhớ xoá `file_hashes.json` bằng tay.

`build_db()` phải trả về coverage trong message thay vì chỉ `Done!`.

---

## D11 — Perf

- `get_architecture_overview` / `detect_communities`: dựng `node_meta_map = {n["id"]: n for n in nodes}`
  **một lần** đầu hàm, thay mọi `next((n for n in nodes if n["id"]==x), {})`. Đo được 7,4s → 0,006s.
- `search_by_filename`: bỏ vòng lặp O(n²) check `in_graph`, dùng set `{_node_path(nid) for nid in file_mapping}`
  dựng một lần.
- `grep_in_files` / `search_by_filename`: nếu có `rg` trong PATH thì dùng `subprocess`, fallback
  `os.walk`. Không bắt buộc cài.
- `igraph` vào `requirements.txt`. Bỏ `faiss-cpu` (không dùng).

---

## Thứ tự phụ thuộc

```
D1 (tokenizer) ────────────────► rebuild BM25 (giây)
                                      │
D3 (reverse VI) ──────────────────────┤
                                      ▼
D10 (guard) ──► D2 (document) ──► full re-embed + BM25 (~1 phút)
                                      │
                                      ▼
                D4 (node ID) ──► extract_graph + re-embed (~1 phút)
                                      │
                          ┌───────────┼───────────┐
                          ▼           ▼           ▼
                    D5 (barrel)  D6 (public)  D7 (pubspec)
                          └───────────┼───────────┘
                                      ▼
                              D8 (get_change_impact)

D9 (compact) / D11 (perf) — độc lập, làm lúc nào cũng được
```

D1 và D3 làm được ngay, đo được ngay, không cần re-embed. Nên làm trước để có baseline sạch
trước khi đụng vào D2.
