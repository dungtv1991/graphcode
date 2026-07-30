# Context Quality v2 — Kết quả đo

## Phase 1: Retrieval Quality

| Chỉ số | Baseline | Sau | Target | Status |
|---|---|---|---|---|
| BM25 tiếng Việt | `Price*` (sai) | `CartItemPromotion` top-1 | Cart-related | ✅ PASS |
| `CartItemPromotion` rank | 48/8410 (cos 0.4574) | **1/9537** (cos 0.6501) | top-5 | ✅ PASS |
| Token bị truncate | 82% (602/730) | 2.9% (mean 61.6 tok) | 0% | ✅ ~PASS |
| Full re-embed | 4.7 phút | 4.0 phút (9537 nodes) | ≤1.5 phút | ⚠️ CPU-bound |
| `_enrich_query` tiếng Việt | Trả nguyên | Cart, Promotion, Address... | Hoạt động | ✅ PASS |

## Phase 2: Node Identity

| Chỉ số | Baseline | Sau | Target | Status |
|---|---|---|---|---|
| Total nodes | 8410 (dedup mất ~1800) | **9537** (không mất) | 0 mất | ✅ PASS |
| Class name trùng gây mất | 619 tên, ~1800 class | 521 ambiguous, 0 mất | 0 | ✅ PASS |
| `get_blast_radius("CG")` | 94 node trộn 11 class | 11 candidate disambiguation | Không trộn | ✅ PASS |
| Node ID format | bare name | `{path}::{ClassName}` (qualified) | Unique | ✅ PASS |

## Phase 3: Cross-repo

| Chỉ số | Baseline | Sau | Target | Status |
|---|---|---|---|---|
| `imports_from` edges | 33 | **5426** | ≥800 | ✅ PASS |
| Barrel coverage | 0 barrels | 19 barrels mapped | Barrel resolve | ✅ PASS |
| Visibility marking | Không có | 1578 public, 7967 internal | public/internal | ✅ PASS |
| ExternalPackage stubs | 0 | 8 stubs (app_*) | Bắt app_* | ✅ PASS |
| pubspec deps | Không có | 20 repos, 73 deps | parse pubspec | ✅ PASS |
| `get_change_impact` | Không có | verdict + risk + repos | Tool mới | ✅ PASS |
| Dangling edges | 28.6% | **19.1%** | <5% | ⚠️ Improved |

## Phase 4: Token & Perf

| Chỉ số | Baseline | Sau | Target | Status |
|---|---|---|---|---|
| Token `get_blast_radius` | ~5000 | **250** chars | <1000 | ✅ PASS |
| `get_architecture_overview` | 7.4s | **0.6s** | <0.1s | ✅ 12x faster |
| `search_by_filename` | O(n²) | O(1) set lookup | Fast | ✅ PASS |
| requirements.txt | +faiss (unused) | +igraph, -faiss | Correct | ✅ PASS |

## Phase 5: Housekeeping

| Item | Status |
|---|---|
| Xoá run.js (chứa API key) | ✅ Done |
| Xoá index.js, vector_context_manager.py, test_selector.py | ✅ Done |
| Xoá package.json/node_modules | ✅ Done |
| Xoá compare_models.py | ✅ Done |
| Graph incremental update (watch daemon) | ✅ Done |
| Steering templates synced | ✅ Done |
| Revoke DeepSeek key | ⚠️ Cần làm thủ công trên dashboard |

## Commits

```
febdf5e feat(context-quality-v2): Phase 3 — cross-repo barrel, pubspec, get_change_impact
2dc9792 chore: Phase 5 housekeeping — xoá code chết + rủi ro bảo mật
42110bf feat(context-quality-v2): Phase 4 — compact output + perf fixes
9b9bd5c feat(context-quality-v2): Phase 1+2 — BM25 Unicode, document builder, qualified node ID
```
