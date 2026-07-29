"""Chạy 10 query tiếng Việt đại diện, ghi top-5 BM25 + Vector + Hybrid vào baseline.json."""
import sys
sys.path.insert(0, ".")

import json
import numpy as np
import re

# Import từ mcp_server
from mcp_server import (
    _init, _State, _tokenize_for_bm25, _enrich_query,
)

QUERIES = [
    "giỏ hàng thêm sản phẩm khuyến mãi",
    "địa chỉ giao hàng tỉnh thành phố",
    "lịch sử mua hàng đơn hàng",
    "thanh toán online chuyển khoản",
    "đăng nhập OTP xác thực",
    "tìm kiếm sản phẩm theo tên",
    "voucher mã giảm giá áp dụng",
    "thông báo push notification",
    "hồ sơ sức khỏe bệnh nhân",
    "đặt lịch hẹn khám bệnh",
]


def bm25_top5(query: str) -> list[dict]:
    if _State.bm25_index is None:
        return []
    tokens = _tokenize_for_bm25(query)
    if not tokens:
        return []
    scores = _State.bm25_index.get_scores(tokens)
    top_idx = np.argsort(scores)[::-1][:5]
    results = []
    for idx in top_idx:
        nid = _State.db["metadata"][idx]["id"]
        results.append({"node": nid, "score": round(float(scores[idx]), 4)})
    return results


def vector_top5(query: str) -> list[dict]:
    text = _enrich_query(query)
    q_vec = _State.model.encode([text], normalize_embeddings=True)
    scores = (_State.db["embeddings"] @ q_vec.T).flatten()
    top_idx = np.argsort(scores)[::-1][:5]
    results = []
    for idx in top_idx:
        nid = _State.db["metadata"][idx]["id"]
        results.append({"node": nid, "score": round(float(scores[idx]), 4)})
    return results


def hybrid_top5(query: str) -> list[str]:
    """Reproduce hybrid logic from _vector_search."""
    raw_query = query
    text = _enrich_query(query)
    top_k = 5

    q_vec = _State.model.encode([text], normalize_embeddings=True)
    vec_scores = (_State.db["embeddings"] @ q_vec.T).flatten()
    vec_pool = min(len(vec_scores), max(top_k * 5, 50))
    vec_ranked = np.argsort(vec_scores)[::-1][:vec_pool]

    bm25_ranked = []
    if _State.bm25_index is not None:
        bm25_tokens = _tokenize_for_bm25(raw_query)
        if bm25_tokens:
            bm25_scores = _State.bm25_index.get_scores(bm25_tokens)
            bm25_pool = min(len(bm25_scores), max(top_k * 5, 50))
            bm25_ranked = np.argsort(bm25_scores)[::-1][:bm25_pool]

    K = 60
    rrf_scores: dict = {}
    for rank, idx in enumerate(vec_ranked):
        nid = _State.db["metadata"][idx]["id"]
        if nid not in _State.file_mapping:
            continue
        rrf_scores[nid] = rrf_scores.get(nid, 0) + 1.0 / (K + rank + 1)
    for rank, idx in enumerate(bm25_ranked):
        nid = _State.db["metadata"][idx]["id"]
        if nid not in _State.file_mapping:
            continue
        rrf_scores[nid] = rrf_scores.get(nid, 0) + 1.0 / (K + rank + 1)

    _VI_STOP = {"thanh", "toan", "don", "hang", "ngan", "cho", "khi", "tin",
                "nhan", "moi", "cap", "nhat", "trang", "man", "hinh", "nguoi", "dung"}
    kws = [w.lower() for w in re.findall(r'[A-Za-z][a-z0-9]{2,}', raw_query)
           if w.lower() not in _VI_STOP]

    reranked = []
    for nid, rrf_base in rrf_scores.items():
        name_lower = nid.lower()
        boost = min(sum(0.003 for kw in kws if kw in name_lower), 0.01)
        reranked.append((rrf_base + boost, nid))

    reranked.sort(key=lambda x: x[0], reverse=True)
    return [nid for _, nid in reranked[:top_k]]


def main():
    print("Initializing...", flush=True)
    _init()
    print(f"DB loaded: {len(_State.db['metadata'])} nodes", flush=True)

    baseline = {"node_count": len(_State.db["metadata"]), "queries": []}

    for q in QUERIES:
        print(f"  Query: {q}")
        entry = {
            "query": q,
            "enrich_result": _enrich_query(q),
            "bm25_top5": bm25_top5(q),
            "vector_top5": vector_top5(q),
            "hybrid_top5": hybrid_top5(q),
        }
        baseline["queries"].append(entry)

    out_path = ".kiro/context-quality-v2/baseline.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(baseline, f, ensure_ascii=False, indent=2)

    print(f"\nBaseline saved to {out_path}")
    print(f"Total queries: {len(baseline['queries'])}")


if __name__ == "__main__":
    main()
