"""
MCP Server - Flutter Knowledge Graph Context Selector
Model load 1 lần khi server khởi động, mọi query sau đó ~100ms
"""

import json
import os
import pickle
import sys
import re
import numpy as np
from mcp.server.fastmcp import FastMCP
from embedding_provider import create_provider

# ─────────────────────────────────────────
# Config
# ─────────────────────────────────────────
FPT_ROOT = "/Users/dungtv54/FPT"
GRAPHCODE_DIR = os.path.dirname(os.path.abspath(__file__))
GRAPH_FILE = os.path.join(GRAPHCODE_DIR, "knowledge_graph.json")
DB_FILE = os.path.join(GRAPHCODE_DIR, "vector_db.pkl")
HASH_STORE_FILE = os.path.join(GRAPHCODE_DIR, "file_hashes.json")
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

# ─────────────────────────────────────────
# Vietnamese keyword enrichment
# ─────────────────────────────────────────
VI_KEYWORDS = {
    # Commerce
    "Cart": "giỏ hàng, thêm vào giỏ, xem giỏ hàng",
    "Payment": "thanh toán, phương thức thanh toán, trả tiền",
    "Order": "đơn hàng, tạo đơn, lịch sử mua hàng, đặt hàng",
    "Product": "sản phẩm, danh sách sản phẩm, chi tiết sản phẩm",
    "Checkout": "thanh toán, xác nhận đơn hàng",
    "Voucher": "voucher, mã giảm giá, khuyến mãi",
    "Promotion": "khuyến mãi, ưu đãi, giảm giá",
    "Price": "giá, giá sản phẩm, giá khuyến mãi",
    "Rebuy": "mua lại, đặt lại đơn hàng",
    "Repayment": "thanh toán lại, trả nợ đơn hàng",
    # Payment methods - digital wallets
    "Momo": "ví momo, thanh toán momo, ví điện tử momo",
    "Zalopay": "ví zalopay, thanh toán zalopay, zalo pay",
    "Zalo": "ví zalopay, thanh toán zalo",
    "Digital": "ví điện tử, thanh toán số, momo zalopay",
    "Vnpay": "vnpay, thanh toán vnpay, ngân hàng",
    "Alepay": "alepay, thẻ tín dụng, trả góp",
    "Qr": "mã QR, quét QR, thanh toán QR",
    "Sameless": "thanh toán liền mạch, seamless payment",
    "Status": "trạng thái, kết quả thanh toán, thành công thất bại",
    "Webview": "webview, trang web thanh toán, cổng thanh toán",
    "Bank": "ngân hàng, chuyển khoản, ATM",
    "Card": "thẻ, thẻ tín dụng, thẻ ngân hàng",
    "Cards": "danh sách thẻ, thẻ đã lưu",
    "Wallet": "ví, ví điện tử",
    # Auth
    "Auth": "xác thực, đăng nhập, tài khoản",
    "Login": "đăng nhập, tài khoản, mật khẩu",
    "Logout": "đăng xuất, thoát tài khoản",
    "SSO": "đăng nhập một lần, liên kết tài khoản",
    "OTP": "mã OTP, xác minh điện thoại",
    "Password": "mật khẩu, đổi mật khẩu",
    "Register": "đăng ký, tạo tài khoản mới",
    "Biometric": "vân tay, face id, xác thực sinh trắc học",
    # User / Profile
    "Profile": "hồ sơ cá nhân, thông tin người dùng",
    "Address": "địa chỉ, địa chỉ giao hàng, thêm địa chỉ",
    "Customer": "khách hàng, người dùng",
    "Account": "tài khoản, thông tin tài khoản",
    # Navigation
    "Splash": "màn hình khởi động, splash screen",
    "Home": "trang chủ, màn hình chính",
    "Dashboard": "bảng điều khiển, tổng quan",
    "Navigation": "điều hướng, chuyển màn hình",
    "Route": "điều hướng, navigation, route",
    # Search & Content
    "Search": "tìm kiếm, tra cứu, tìm sản phẩm",
    "Content": "nội dung, bài viết, tin tức",
    "Landing": "trang landing, trang giới thiệu",
    "Banner": "banner, quảng cáo",
    "Notification": "thông báo, push notification",
    "Noti": "thông báo, tin nhắn hệ thống",
    # Health / Medical
    "Vaccine": "vaccine, tiêm chủng, đặt lịch tiêm",
    "Health": "sức khỏe, kiểm tra sức khỏe",
    "Medicine": "thuốc, lịch uống thuốc, nhắc nhở",
    "Prescription": "đơn thuốc, kê đơn",
    "Consultancy": "tư vấn, tư vấn sức khỏe",
    # Technical
    "Module": "module, tính năng",
    "Repository": "repository, data layer, lấy dữ liệu",
    "Service": "service, dịch vụ",
    "Gateway": "gateway, API, kết nối server",
    "Bloc": "state management, trạng thái màn hình",
    "Datasource": "nguồn dữ liệu, API call",
    "Store": "lưu trữ, cửa hàng",
    "Finding": "tìm kiếm, tìm cửa hàng",
    "Version": "phiên bản, cập nhật ứng dụng",
    "Maintenance": "bảo trì, dừng dịch vụ",
    "Connection": "kết nối mạng, internet",
    "Game": "trò chơi, mini game, giải trí",
    "Loyalty": "điểm thưởng, khách hàng thân thiết",
    "Fsell": "bán hàng, flash sale",
    "247": "24/7, dịch vụ liên tục",
    # Delivery / Shipping
    "Delivery": "giao hàng, vận chuyển, ship",
    "Shipping": "vận chuyển, phí ship, đơn vị giao hàng",
    "Tracking": "theo dõi đơn hàng, trạng thái giao hàng",
    # Health metrics
    "Blood": "máu, huyết áp, nhóm máu",
    "Pressure": "huyết áp, đo huyết áp",
    "Glucose": "đường huyết, đo đường huyết",
    "Bmi": "chỉ số BMI, cân nặng, chiều cao",
    "Vaccination": "tiêm chủng, lịch tiêm chủng",
    "Schedule": "lịch hẹn, đặt lịch, lịch khám",
    "Expert": "chuyên gia, bác sĩ, tư vấn viên",
    "Survey": "khảo sát, câu hỏi, bảng hỏi",
    # Content / Media
    "Article": "bài viết, tin tức, blog",
    "Video": "video, xem video, clip",
    "Chat": "chat, nhắn tin, hội thoại",
    "Message": "tin nhắn, thông điệp",
    "Rating": "đánh giá, xếp hạng, sao",
    # Commerce extras
    "Detail": "chi tiết, thông tin chi tiết",
    "Category": "danh mục, phân loại, nhóm sản phẩm",
    "History": "lịch sử, lịch sử giao dịch, lịch sử mua hàng",
    "Gift": "quà tặng, điểm thưởng, ưu đãi",
    "Combo": "combo, gói sản phẩm, bundle",
    "Shop": "cửa hàng, gian hàng",
    "Suggestion": "gợi ý, đề xuất, tìm kiếm gợi ý",
    "Suggest": "gợi ý, đề xuất",
    "Filter": "lọc, bộ lọc, tìm kiếm nâng cao",
    "Select": "chọn, lựa chọn",
    "Onboarding": "hướng dẫn, giới thiệu ứng dụng, onboarding",
    "Policy": "chính sách, điều khoản, quy định",
    "Result": "kết quả, kết quả tìm kiếm",
    "Record": "bản ghi, lịch sử đo, dữ liệu",
    "Group": "nhóm, phân nhóm",
    "Popup": "popup, hộp thoại, thông báo",
    "Info": "thông tin, thông tin chi tiết",
    # Pharmacy / OTC
    "Otc": "thuốc không kê đơn, OTC, mua thuốc tự do",
    "Multimedia": "hình ảnh, video, media, tải ảnh",
    "Camera": "chụp ảnh, camera, quét mã",
    "Ocr": "nhận dạng ký tự, quét đơn thuốc, OCR",
    # Shopping / Mall
    "Mall": "trung tâm thương mại, gian hàng, mall",
    "Brand": "thương hiệu, nhãn hàng, hãng",
    "Sale": "giảm giá, khuyến mãi, sale",
    "Flash": "flash sale, giảm giá chớp nhoáng",
    "Confirm": "xác nhận, đồng ý, confirm",
    "Cancel": "huỷ, huỷ đơn, cancel",
    # Forms / Input
    "Form": "biểu mẫu, form nhập liệu, điền thông tin",
    "Field": "trường nhập, ô nhập liệu",
    "Tab": "tab, thẻ chuyển đổi, tab bar",
    "Calendar": "lịch, chọn ngày, date picker",
    "Date": "ngày, ngày tháng, chọn ngày",
    # Health extended
    "Cancer": "ung thư, tầm soát ung thư, sàng lọc",
    "Covid": "covid, xét nghiệm covid, tiêm vaccine covid",
    "Guideline": "hướng dẫn, phác đồ điều trị, guideline",
    # Social / Community
    "Contact": "liên hệ, danh bạ, thông tin liên lạc",
    "Comment": "bình luận, nhận xét, đánh giá",
    "Charity": "từ thiện, quyên góp, đóng góp",
    "Postcard": "thiệp, bưu thiếp, gửi lời chúc",
    # Navigation extended
    "Walkthrough": "hướng dẫn sử dụng, walkthrough, tutorial",
    "Success": "thành công, hoàn tất, kết quả thành công",
    "Skeleton": "loading, placeholder, skeleton UI",
    # UI Components extended
    "Header": "tiêu đề, header, phần đầu",
    "Bar": "thanh điều hướng, app bar, bottom bar",
    "Chart": "biểu đồ, đồ thị, thống kê",
    "Selection": "lựa chọn, chọn nhiều, multi select",
}


def _enrich_vi_keywords(class_name: str) -> str:
    """Sinh keywords tiếng Việt từ tên class (CamelCase split)."""
    import re as _re
    words = _re.findall(r'[A-Z][a-z0-9]*|[0-9]+', class_name)
    matched = [VI_KEYWORDS[w] for w in words if w in VI_KEYWORDS]
    return ", ".join(matched)


mcp = FastMCP("flutter-context")

# ─────────────────────────────────────────
# Query log — lightweight, append-only
# ─────────────────────────────────────────
QUERY_LOG_FILE = os.path.join(GRAPHCODE_DIR, "query_log.jsonl")

def _log_query(query: str, top_k: int, nodes_found: list[str], flow_count: int,
               success: bool = True, error: str = ""):
    """Append 1 dòng JSONL per query — cả thành công lẫn thất bại."""
    import time
    entry = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "query": query,
        "top_k": top_k,
        "nodes": nodes_found[:10] if nodes_found else [],
        "flow_count": flow_count,
        "success": success,
    }
    if error:
        entry["error"] = error
    try:
        with open(QUERY_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[log] Failed to write query log: {e}", file=sys.stderr)

# ─────────────────────────────────────────
# Singleton — load 1 lần khi server start
# ─────────────────────────────────────────
class _State:
    graph = None
    file_mapping = None
    edges = None
    model = None
    db = None
    adj_forward = None
    adj_reverse = None

def _init():
    if _State.graph is not None:
        return

    print("Loading knowledge graph...", file=sys.stderr)
    with open(GRAPH_FILE, "r") as f:
        _State.graph = json.load(f)
    _State.file_mapping = _State.graph["file_mapping"]
    _State.edges = _State.graph["edges"]

    print("Loading embedding model...", file=sys.stderr)
    _State.model = create_provider()

    if os.path.exists(DB_FILE):
        print("Loading vector DB...", file=sys.stderr)
        with open(DB_FILE, "rb") as f:
            _State.db = pickle.load(f)

    _build_adjacency_index()

    print("Ready.", file=sys.stderr)

# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────
def _build_adjacency_index():
    """Build forward and reverse adjacency dicts from _State.edges (single pass)."""
    forward = {}
    reverse = {}
    for edge in _State.edges:
        src = edge["from"]
        dst = edge["to"]
        etype = edge["type"]
        forward.setdefault(src, []).append((dst, etype))
        reverse.setdefault(dst, []).append((src, etype))
    _State.adj_forward = forward
    _State.adj_reverse = reverse


def _enrich_query(text: str) -> str:
    """Thêm VI_KEYWORDS vào query để tăng recall khi search.

    Match case-insensitive để xử lý cả key viết hoa (OTP, SSO, QR) lẫn
    thường (otp, sso). Trước đây dùng w.capitalize() nên "otp" → "Otp"
    không khớp key "OTP" → miss enrichment.
    """
    import re as _re
    # Build lookup viết thường 1 lần (cache trên function attribute)
    if not hasattr(_enrich_query, "_lower_map"):
        _enrich_query._lower_map = {k.lower(): v for k, v in VI_KEYWORDS.items()}
    lower_map = _enrich_query._lower_map

    words = _re.findall(r'[A-Za-z][A-Za-z0-9]*', text)
    extra = []
    seen = set()
    for w in words:
        wl = w.lower()
        if wl in lower_map and wl not in seen:
            seen.add(wl)
            extra.append(lower_map[wl])
    if extra:
        text = text + " " + " ".join(extra)
    return text


def _vector_search(text: str, top_k: int) -> list[str]:
    """Vector search + lexical re-rank.

    Lấy pool rộng (top_k*6, tối thiểu 40) theo cosine, rồi boost node có tên class
    khớp keyword trong query gốc. Boost phân tầng:
      - exact match (cả query ⊆ tên hoặc tên ⊆ query): +0.20
      - keyword khớp 1 phần trong tên: +0.08 mỗi keyword (cap +0.24)
    Pool rộng giúp node vector-score thấp nhưng tên khớp (vd VNPayOrderModel) vẫn lọt.
    """
    raw_query = text
    text = _enrich_query(text)
    q_vec = _State.model.encode([text], normalize_embeddings=True)
    scores = (_State.db["embeddings"] @ q_vec.T).flatten()

    # Pool rộng để re-rank — quan trọng cho keyword hiếm
    pool_size = min(len(scores), max(top_k * 5, 32))
    pool_idx = np.argsort(scores)[::-1][:pool_size]

    # Keyword từ query gốc — chỉ token ≥3 ký tự (tránh nhiễu "vn","qr").
    # Bỏ stopword tiếng Việt để không boost nhầm tên class (vd "thanh"→BaoThanhNien).
    _VI_STOP = {"thanh", "toan", "don", "hang", "ngan", "cho", "khi", "tin",
                "nhan", "moi", "cap", "nhat", "trang", "man", "hinh", "nguoi", "dung"}
    kws = [w.lower() for w in re.findall(r'[A-Za-z][a-z0-9]{2,}', raw_query)
           if w.lower() not in _VI_STOP]

    reranked = []
    for i in pool_idx:
        nid = _State.db["metadata"][i]["id"]
        if nid not in _State.file_mapping:
            continue
        base = float(scores[i])
        name_lower = nid.lower()
        # Boost: mỗi keyword khớp trong tên class +0.08, cap +0.20
        boost = min(sum(0.08 for kw in kws if kw in name_lower), 0.20)
        reranked.append((base + boost, nid))

    reranked.sort(key=lambda x: x[0], reverse=True)
    return [nid for _, nid in reranked[:top_k]]

def _detect_entry_nodes(query: str) -> list[str]:
    q = query.lower()
    candidates = []
    for node_id in _State.file_mapping:
        name = node_id.lower()
        if ("home" in q and "home" in name) or \
           ("flash" in q and ("flash" in name or "fsell" in name)):
            candidates.append(node_id)
    return candidates[:3]

# Node types ưu tiên giữ lại trong flow (logic-bearing > UI noise)
_IMPORTANT_TYPES = {
    "Module", "Controller", "UseCase", "Repository", "Service",
    "Model", "Event", "State", "Route", "Provider", "Interceptor",
}
# Edge types ưu tiên (data/control flow > inheritance noise)
_PRIORITY_EDGES = ("depends_on", "binds", "data_flows_to", "routes_to",
                   "has_part", "imports_local", "imports_from")
_SECONDARY_EDGES = ("extends", "mixes_in", "implements")


def _trace_flow(start_nodes: list[str], max_nodes: int = 18) -> list[str]:
    """BFS theo độ ưu tiên: priority edges trước, cap tổng số node để tiết kiệm token.

    Trả về danh sách node đã rank — entry nodes + neighbor quan trọng nhất.
    """
    visited = set(start_nodes)
    flow = list(start_nodes)
    # BFS queue: (node, depth)
    from collections import deque
    queue = deque((n, 0) for n in start_nodes)
    node_meta_map = {n["id"]: n for n in _State.graph.get("nodes", [])}

    def _is_important(nid: str) -> bool:
        return node_meta_map.get(nid, {}).get("type", "") in _IMPORTANT_TYPES

    while queue and len(flow) < max_nodes:
        node, depth = queue.popleft()
        if depth >= 2:  # giới hạn 2 hop
            continue

        # Gom neighbor theo ưu tiên edge
        neighbors_pri, neighbors_sec = [], []
        for target, etype in _State.adj_forward.get(node, []):
            if target in visited:
                continue
            (neighbors_pri if etype in _PRIORITY_EDGES else neighbors_sec).append(target)
        # Reverse chỉ ở hop 0 (ai dùng entry node) — context "blast" nhẹ
        if depth == 0:
            for source, etype in _State.adj_reverse.get(node, []):
                if source in visited:
                    continue
                if etype in ("depends_on", "binds", "data_flows_to"):
                    neighbors_pri.append(source)

        # Ưu tiên node quan trọng trong từng nhóm
        ordered = (
            [n for n in neighbors_pri if _is_important(n)] +
            [n for n in neighbors_pri if not _is_important(n)] +
            [n for n in neighbors_sec if _is_important(n)]
        )
        for nb in ordered:
            if nb not in visited and len(flow) < max_nodes:
                visited.add(nb)
                flow.append(nb)
                queue.append((nb, depth + 1))

    return flow

def _graph_info(nodes: list[str], max_edges: int = 40) -> str:
    """Chỉ render edges GIỮA các node trong kết quả (intra-result), cap để gọn token."""
    node_set = set(nodes)
    lines = []
    seen: set[tuple[str, str, str]] = set()

    def _emit(edges_pool):
        for node in nodes:  # giữ thứ tự rank
            for target, etype in _State.adj_forward.get(node, []):
                if target in node_set and etype in edges_pool:
                    key = (node, etype, target)
                    if key not in seen:
                        seen.add(key)
                        lines.append(f"{node} -{etype}-> {target}")
                        if len(lines) >= max_edges:
                            return

    _emit(_PRIORITY_EDGES)      # quan trọng trước
    if len(lines) < max_edges:
        _emit(_SECONDARY_EDGES) # inheritance sau nếu còn chỗ

    if not lines:
        return ""
    return "=== GRAPH (intra-result edges) ===\n" + "\n".join(lines)

def _node_path(node_id: str) -> str:
    """Lấy relative path từ file_mapping (hỗ trợ cả format cũ string và mới dict)."""
    fm = _State.file_mapping.get(node_id)
    if fm is None:
        return ""
    return fm["path"] if isinstance(fm, dict) else fm

def _node_line(node_id: str) -> int:
    if _State.file_mapping is None:
        return 1
    fm = _State.file_mapping.get(node_id)
    if isinstance(fm, dict):
        return fm.get("line", 1)
    return 1

def _to_files(nodes: list[str]) -> list[str]:
    seen, result = set(), []
    for n in nodes:
        rel = _node_path(n)
        if rel:
            path = os.path.join(FPT_ROOT, rel)
            if path not in seen:
                seen.add(path)
                result.append(path)
    return result

# ─────────────────────────────────────────
# MCP Tools
# ─────────────────────────────────────────
@mcp.tool()
def build_db() -> str:
    """
    Rebuild vector DB — incremental: chỉ re-embed file thay đổi.
    Lần đầu chạy (chưa có hash store) sẽ full rebuild như cũ.
    """
    from extract_graph import scan_changed_only, _hash_file

    # Load graph và model (không dùng _init() để tránh lỗi khi DB chưa tồn tại)
    if _State.graph is None:
        print("Loading knowledge graph...", file=sys.stderr)
        with open(GRAPH_FILE, "r") as f:
            _State.graph = json.load(f)
        _State.file_mapping = _State.graph["file_mapping"]
        _State.edges = _State.graph["edges"]
    if _State.model is None:
        print("Loading embedding model...", file=sys.stderr)
        _State.model = create_provider()

    # 0. Detect dimension mismatch → force full rebuild
    force_full_rebuild = False
    if _State.db is not None and len(_State.db["embeddings"]) > 0:
        existing_dim = _State.db["embeddings"].shape[1]
        if existing_dim != _State.model.dimension:
            print(f"Dimension mismatch: DB={existing_dim}, model={_State.model.dimension}. Full rebuild.", file=sys.stderr)
            force_full_rebuild = True

    # 1. Load hash store
    if os.path.exists(HASH_STORE_FILE):
        with open(HASH_STORE_FILE, "r") as f:
            hash_store = json.load(f)
    else:
        hash_store = {}

    if force_full_rebuild:
        hash_store = {}  # Force re-hash all files

    # 2. Xác định file thay đổi / node bị xóa
    changed_files, deleted_node_ids = scan_changed_only(
        FPT_ROOT, hash_store, _State.file_mapping
    )

    # 3. Reverse mapping: rel_path → set of node_ids
    path_to_nodes: dict = {}
    for node_id, path_info in _State.file_mapping.items():
        rel = path_info["path"] if isinstance(path_info, dict) else path_info
        path_to_nodes.setdefault(rel, set()).add(node_id)

    # 4. Node IDs thuộc file thay đổi
    changed_rel = {os.path.relpath(p, FPT_ROOT) for p in changed_files}
    changed_node_ids: set = set()
    for rel, node_ids in path_to_nodes.items():
        if rel in changed_rel:
            changed_node_ids.update(node_ids)

    remove_node_ids = changed_node_ids | set(deleted_node_ids)

    # 5. Giữ lại embeddings cũ của các node không đổi
    old_embeddings: dict = {}  # node_id → (meta_dict, emb_vector)
    if _State.db is not None:
        for meta, emb in zip(_State.db["metadata"], _State.db["embeddings"]):
            nid = meta["id"]
            if nid not in remove_node_ids:
                old_embeddings[nid] = (meta, emb)

    # 6. Chuẩn bị document cho các node cần re-embed
    _file_lines_cache: dict = {}

    def _extract_class_window(full_path: str, class_name: str, window: int = 120) -> str:
        if full_path not in _file_lines_cache:
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    _file_lines_cache[full_path] = f.readlines()
            except Exception:
                _file_lines_cache[full_path] = []
        lines = _file_lines_cache[full_path]
        pattern = re.compile(rf'\bclass\s+{re.escape(class_name)}\b')
        start = 0
        for i, line in enumerate(lines):
            if pattern.search(line):
                start = max(0, i - 3)
                break
        return ''.join(lines[start: start + window])

    node_meta_map = {n["id"]: n for n in _State.graph.get("nodes", [])}
    new_documents, new_metadata = [], []

    for node_id in changed_node_ids:
        if node_id not in _State.file_mapping:
            continue
        path_info = _State.file_mapping[node_id]
        rel = path_info["path"] if isinstance(path_info, dict) else path_info
        full_path = os.path.join(FPT_ROOT, rel)

        content = ""
        if os.path.exists(full_path):
            content = _extract_class_window(full_path, node_id)
            if not content and full_path in _file_lines_cache:
                content = ''.join(_file_lines_cache[full_path][:120])

        vi_keywords = _enrich_vi_keywords(node_id)
        vi_section = f"Mô tả: {vi_keywords}" if vi_keywords else ""
        node_meta = node_meta_map.get(node_id, {})
        methods_str = ", ".join(node_meta.get("methods", []))
        events_str = ", ".join(node_meta.get("events", []))
        api_str = ", ".join(node_meta.get("api_paths", []))
        meta_section = ""
        if methods_str: meta_section += f"Methods: {methods_str}\n"
        if events_str:  meta_section += f"Events: {events_str}\n"
        if api_str:     meta_section += f"API paths: {api_str}\n"

        text = f"Class: {node_id}\nFile: {rel}\n{vi_section}\n{meta_section}\n{content}"
        new_documents.append(text)
        new_metadata.append({"id": node_id, "file": rel})

    # 7. Encode các node mới / thay đổi
    if new_documents:
        new_embs = _State.model.encode(
            new_documents,
            show_progress_bar=True,
            batch_size=32,
            normalize_embeddings=True,
        )
    else:
        new_embs = None

    # 8. Merge embeddings cũ + mới
    all_meta = [m for m, _ in old_embeddings.values()]
    all_embs = [e for _, e in old_embeddings.values()]
    all_meta.extend(new_metadata)
    if new_embs is not None:
        all_embs.extend(new_embs)

    merged = np.array(all_embs) if all_embs else np.empty((0, _State.model.dimension))

    # 9. Lưu DB
    with open(DB_FILE, "wb") as f:
        pickle.dump({"embeddings": merged, "metadata": all_meta, "model_name": MODEL_NAME}, f)

    # 10. Cập nhật hash store
    new_hash_store = {k: v for k, v in hash_store.items() if os.path.exists(k)}
    for abs_path in changed_files:
        if os.path.exists(abs_path):
            new_hash_store[abs_path] = _hash_file(abs_path)
    with open(HASH_STORE_FILE, "w") as f:
        json.dump(new_hash_store, f, indent=2)

    # 11. Reload state
    size_mb = os.path.getsize(DB_FILE) / 1024 / 1024
    _State.db = None
    with open(DB_FILE, "rb") as f:
        _State.db = pickle.load(f)

    _build_adjacency_index()

    unchanged_count = len(old_embeddings)
    new_count = len(new_documents)
    deleted_count = len(deleted_node_ids)
    return (
        f"Done! {len(all_meta)} total vectors "
        f"({new_count} re-embedded, {unchanged_count} unchanged, {deleted_count} deleted) "
        f"— {size_mb:.1f} MB"
    )


@mcp.tool()
def query_context(query: str, top_k: int = 8, snippet_chars: int = 300) -> str:
    """
    Tìm các file Flutter liên quan đến query dựa trên semantic search + knowledge graph.
    Trả về file paths, graph relationships, và snippet ngắn của mỗi file.
    Dùng get_file_content để đọc đầy đủ nội dung file cần thiết.

    Args:
        query: Câu hỏi hoặc mô tả tính năng cần tìm (tiếng Việt hoặc tiếng Anh)
        top_k: Số lượng kết quả vector search (mặc định 8)
        snippet_chars: Số ký tự preview mỗi file để nhận diện nhanh (mặc định 300, đặt 0 để tắt)
    """
    try:
        _init()

        base_nodes = _vector_search(query, top_k)
        entry_nodes = _detect_entry_nodes(query) or base_nodes
        flow_nodes = _trace_flow(entry_nodes)

        files = _to_files(base_nodes)

        # Lấy node metadata từ graph để build summary
        node_meta_map = {n["id"]: n for n in _State.graph.get("nodes", [])}

        files_with_content = []
        for node_id, file_path in zip(base_nodes, files):
            meta = node_meta_map.get(node_id, {})
            entry: dict = {
                "node": node_id,
                "path": file_path,
                "line": _node_line(node_id),       # jump thẳng đến class
                "summary": meta.get("summary", ""), # ~20 tokens, rất informative
            }
            # Chỉ đọc file nếu summary rỗng (node cũ chưa có summary)
            if not entry["summary"] and snippet_chars > 0:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        entry["snippet"] = f.read(snippet_chars)
                except Exception:
                    pass
            files_with_content.append(entry)

        result = {
            "files": files_with_content,
            "flow_files": _to_files(flow_nodes)[:15],
            "graph": _graph_info(flow_nodes),
            "flow_nodes": flow_nodes[:18],
        }

        _log_query(query, top_k, base_nodes, len(flow_nodes), success=True)
        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        _log_query(query, top_k, [], 0, success=False, error=str(e))
        raise


@mcp.tool()
def get_file_content(file_path: str, start_line: int = 1, end_line: int = 0, class_name: str = "") -> str:
    """
    Đọc nội dung file Flutter với line numbers. Hỗ trợ đọc theo range hoặc jump đến class.

    Args:
        file_path: Đường dẫn tuyệt đối đến file (lấy từ query_context)
        start_line: Dòng bắt đầu đọc (mặc định 1 = từ đầu file)
        end_line: Dòng kết thúc (mặc định 0 = đọc 200 dòng từ start_line)
        class_name: Nếu truyền tên class, tự động jump đến dòng định nghĩa class đó
    """
    try:
        if class_name:
            _init()

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            all_lines = f.readlines()

        total = len(all_lines)

        # Jump đến class — dùng start_line từ graph nếu có (nhanh hơn scan)
        if class_name:
            graph_line = _node_line(class_name)
            if graph_line > 1:
                start_line = max(1, graph_line - 2)
            else:
                pattern = re.compile(rf'\bclass\s+{re.escape(class_name)}\b')
                for i, line in enumerate(all_lines):
                    if pattern.search(line):
                        start_line = max(1, i - 2)
                        break

        # Normalize range — class_name → 150 lines, default → 200 lines
        s = max(1, start_line) - 1  # convert to 0-indexed
        default_limit = 150 if class_name else 200
        e = end_line if end_line > 0 else s + default_limit
        e = min(e, total)

        chunk = all_lines[s:e]
        numbered = ''.join(f"{s+i+1:4}: {line}" for i, line in enumerate(chunk))

        footer = f"\n--- [{s+1}–{s+len(chunk)}/{total} lines] ---"
        if s + len(chunk) < total:
            footer += f"  (còn {total - s - len(chunk)} dòng, dùng start_line={s+len(chunk)+1} để đọc tiếp)"
        return numbered + footer

    except FileNotFoundError:
        return f"File not found: {file_path}"
    except Exception as e:
        return f"Error reading file: {e}"


@mcp.tool()
def search_by_api_path(path: str) -> str:
    """
    Tìm tất cả file liên quan đến một API endpoint.
    Dùng khi BA/ticket đề cập endpoint cụ thể.

    Args:
        path: API path cần tìm, ví dụ: '/v1/orders', '/multimedia'
    """
    _init()
    results = []
    for node in _State.graph.get("nodes", []):
        api_paths = node.get("api_paths", [])
        if any(path in p or p in path for p in api_paths):
            file_path = _node_path(node["id"])
            results.append({
                "node": node["id"],
                "type": node["type"],
                "repo": node.get("repo", ""),
                "api_paths": api_paths,
                "file": os.path.join(FPT_ROOT, file_path) if file_path else "",
            })
    if not results:
        return json.dumps({"message": f"No nodes found with api_path containing '{path}'"})
    return json.dumps(results, ensure_ascii=False, indent=2)


@mcp.tool()
def search_by_error_type(error_type: str) -> str:
    """
    Tìm file nào throw/catch một loại exception cụ thể.
    Dùng khi fix bug crash với error type đã biết.

    Args:
        error_type: Tên exception, ví dụ: 'NetworkException', 'OrderException'
    """
    _init()
    results = []
    for node in _State.graph.get("nodes", []):
        error_types = node.get("error_types", [])
        if any(error_type.lower() in e.lower() for e in error_types):
            file_path = _node_path(node["id"])
            results.append({
                "node": node["id"],
                "type": node["type"],
                "repo": node.get("repo", ""),
                "error_types": error_types,
                "file": os.path.join(FPT_ROOT, file_path) if file_path else "",
            })
    if not results:
        return json.dumps({"message": f"No nodes found handling '{error_type}'"})
    return json.dumps(results, ensure_ascii=False, indent=2)


@mcp.tool()
def find_similar_modules(module_name: str) -> str:
    """
    Tìm các module có cấu trúc tương tự để dùng làm template khi tạo feature mới.
    So sánh dựa trên UseCase types và route patterns.

    Args:
        module_name: Tên module cần tìm template, ví dụ: 'InfographicModule'
    """
    _init()
    # Lấy các UseCase mà module này bind
    target_usecases = set()
    for edge in _State.edges:
        if edge["from"] == module_name and edge["type"] == "binds":
            if "UseCase" in edge["to"]:
                # Lấy suffix pattern: GetXxxPageUseCase → GetXxxPageUseCase pattern
                uc = edge["to"]
                target_usecases.add(uc)

    # Tìm module khác có UseCase pattern tương tự
    module_scores = {}
    for edge in _State.edges:
        if edge["type"] == "binds" and "UseCase" in edge["to"] and edge["from"] != module_name:
            other_module = edge["from"]
            other_uc = edge["to"]
            # So sánh suffix pattern (bỏ prefix Get/Create/Delete)
            for tuc in target_usecases:
                t_suffix = re.sub(r'^(Get|Create|Delete|Update|Fetch)', '', tuc)
                o_suffix = re.sub(r'^(Get|Create|Delete|Update|Fetch)', '', other_uc)
                if t_suffix and o_suffix and (t_suffix in o_suffix or o_suffix in t_suffix):
                    module_scores[other_module] = module_scores.get(other_module, 0) + 1

    if not module_scores:
        return json.dumps({"message": f"No similar modules found for '{module_name}'"})

    sorted_modules = sorted(module_scores.items(), key=lambda x: x[1], reverse=True)[:5]
    results = []
    for mod, score in sorted_modules:
        file_path = _node_path(mod)
        mod_node = next((n for n in _State.graph["nodes"] if n["id"] == mod), {})
        results.append({
            "module": mod,
            "similarity_score": score,
            "repo": mod_node.get("repo", ""),
            "file": os.path.join(FPT_ROOT, file_path) if file_path else "",
        })
    return json.dumps(results, ensure_ascii=False, indent=2)


@mcp.tool()
def get_blast_radius(node_id: str, max_depth: int = 4) -> str:
    """
    Tìm tất cả nodes bị ảnh hưởng nếu thay đổi node này.
    Dùng khi muốn biết sửa file X sẽ ảnh hưởng đến đâu.

    Args:
        node_id: Tên class cần phân tích, ví dụ: 'GetSessionIdUseCase', 'CartConfirmBloc'
        max_depth: Độ sâu tìm kiếm (mặc định 4)
    """
    _init()

    # Tìm tất cả nodes phụ thuộc vào node_id (reverse traversal)
    affected = {}  # node_id -> {depth, edge_type, path}

    def reverse_dfs(node, depth, path):
        if depth > max_depth:
            return
        for (caller, etype) in _State.adj_reverse.get(node, []):
            if etype in ("depends_on", "binds", "has_part", "data_flows_to",
                         "extends", "mixes_in", "imports_from", "imports_local"):
                if caller not in affected:
                    affected[caller] = {
                        "depth": depth,
                        "via_edge": etype,
                        "path": path + [caller],
                    }
                    reverse_dfs(caller, depth + 1, path + [caller])

    reverse_dfs(node_id, 1, [node_id])

    if not affected:
        return json.dumps({"node": node_id, "message": "No dependents found — safe to change"})

    # Group by node type
    grouped = {}
    for nid, info in affected.items():
        node_meta = next((n for n in _State.graph["nodes"] if n["id"] == nid), {})
        ntype = node_meta.get("type", "Unknown")
        repo = node_meta.get("repo", "")
        if ntype not in grouped:
            grouped[ntype] = []
        grouped[ntype].append({
            "node": nid,
            "repo": repo,
            "depth": info["depth"],
            "file": os.path.join(FPT_ROOT, _node_path(nid)) if nid in _State.file_mapping else "",
        })

    # Sort each group by depth
    for g in grouped.values():
        g.sort(key=lambda x: x["depth"])

    summary = {k: len(v) for k, v in grouped.items()}

    return json.dumps({
        "node": node_id,
        "total_affected": len(affected),
        "summary": summary,
        "affected_by_type": grouped,
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def detect_communities(min_size: int = 3) -> str:
    """
    Phát hiện các community (nhóm code liên quan) trong knowledge graph bằng Leiden algorithm.
    Dùng để hiểu tổng quan kiến trúc project.

    Args:
        min_size: Số node tối thiểu để tạo thành 1 community (mặc định 3)
    """
    _init()
    try:
        import igraph as ig
    except ImportError:
        return json.dumps({"error": "python-igraph not installed. Run: pip install python-igraph"})

    # Build igraph từ edges
    nodes = list(_State.file_mapping.keys())
    node_index = {n: i for i, n in enumerate(nodes)}

    edges_ig = []
    for edge in _State.edges:
        if edge["from"] in node_index and edge["to"] in node_index:
            edges_ig.append((node_index[edge["from"]], node_index[edge["to"]]))

    if not edges_ig:
        return json.dumps({"error": "No edges found"})

    g = ig.Graph(n=len(nodes), edges=edges_ig, directed=False)

    # Leiden community detection
    try:
        partition = g.community_leiden(objective_function="modularity", n_iterations=10)
    except Exception:
        # Fallback to Louvain nếu Leiden không available
        partition = g.community_multilevel()

    # Build community results
    communities = []
    for i, community in enumerate(partition):
        if len(community) < min_size:
            continue

        member_nodes = [nodes[idx] for idx in community]
        # Lấy repo distribution
        repo_count = {}
        node_types = {}
        for nid in member_nodes:
            meta = next((n for n in _State.graph["nodes"] if n["id"] == nid), {})
            repo = meta.get("repo", "unknown")
            ntype = meta.get("type", "Unknown")
            repo_count[repo] = repo_count.get(repo, 0) + 1
            node_types[ntype] = node_types.get(ntype, 0) + 1

        # Dominant repo = tên community
        dominant_repo = max(repo_count, key=repo_count.get) if repo_count else "unknown"

        communities.append({
            "id": i,
            "name": dominant_repo,
            "size": len(member_nodes),
            "repo_distribution": repo_count,
            "node_types": node_types,
            "key_nodes": member_nodes[:5],  # top 5 nodes
        })

    # Sort by size
    communities.sort(key=lambda x: x["size"], reverse=True)

    # Lưu community assignment vào graph để dùng sau
    community_map = {}
    for i, community in enumerate(partition):
        for idx in community:
            community_map[nodes[idx]] = i

    return json.dumps({
        "total_communities": len(communities),
        "total_nodes_covered": sum(c["size"] for c in communities),
        "communities": communities,
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def get_architecture_overview() -> str:
    """
    Tổng quan kiến trúc project: hub nodes, bridge nodes, coupling warnings.
    Dùng khi muốn hiểu nhanh toàn bộ project hoặc onboard developer mới.
    """
    _init()
    try:
        import igraph as ig
    except ImportError:
        return json.dumps({"error": "python-igraph not installed"})

    nodes = list(_State.file_mapping.keys())
    node_index = {n: i for i, n in enumerate(nodes)}

    edges_ig = []
    for edge in _State.edges:
        if edge["from"] in node_index and edge["to"] in node_index:
            edges_ig.append((node_index[edge["from"]], node_index[edge["to"]]))

    g = ig.Graph(n=len(nodes), edges=edges_ig, directed=False)

    # Hub nodes: degree cao nhất
    degrees = g.degree()
    hub_threshold = sorted(degrees, reverse=True)[min(9, len(degrees)-1)]
    hubs = [
        {
            "node": nodes[i],
            "degree": degrees[i],
            "repo": next((n.get("repo","") for n in _State.graph["nodes"] if n["id"]==nodes[i]), ""),
            "type": next((n.get("type","") for n in _State.graph["nodes"] if n["id"]==nodes[i]), ""),
        }
        for i in range(len(nodes)) if degrees[i] >= hub_threshold
    ]
    hubs.sort(key=lambda x: x["degree"], reverse=True)

    # Betweenness centrality → bridge nodes
    betweenness = g.betweenness(directed=False)
    bridge_threshold = sorted(betweenness, reverse=True)[min(4, len(betweenness)-1)]
    bridges = [
        {
            "node": nodes[i],
            "betweenness": round(betweenness[i], 2),
            "repo": next((n.get("repo","") for n in _State.graph["nodes"] if n["id"]==nodes[i]), ""),
        }
        for i in range(len(nodes)) if betweenness[i] >= bridge_threshold and betweenness[i] > 0
    ]
    bridges.sort(key=lambda x: x["betweenness"], reverse=True)

    # Repo coupling: edges giữa các repo khác nhau
    cross_repo_edges = []
    for edge in _State.edges:
        from_meta = next((n for n in _State.graph["nodes"] if n["id"]==edge["from"]), {})
        to_meta = next((n for n in _State.graph["nodes"] if n["id"]==edge["to"]), {})
        from_repo = from_meta.get("repo","")
        to_repo = to_meta.get("repo","")
        if from_repo and to_repo and from_repo != to_repo:
            key = tuple(sorted([from_repo, to_repo]))
            cross_repo_edges.append(key)

    from collections import Counter
    coupling = Counter(cross_repo_edges).most_common(10)
    coupling_warnings = [
        {"repos": list(pair), "edge_count": count}
        for pair, count in coupling if count >= 3
    ]

    return json.dumps({
        "graph_stats": {
            "total_nodes": len(nodes),
            "total_edges": len(edges_ig),
            "repos": len(set(n.get("repo","") for n in _State.graph["nodes"])),
        },
        "hub_nodes": hubs[:10],
        "bridge_nodes": bridges[:5],
        "cross_repo_coupling": coupling_warnings,
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def call_api(url: str, method: str = "GET", headers: dict = {}, body: dict = {}) -> str:
    """
    Gọi HTTP API và trả về response JSON thực tế.
    Dùng sau khi đọc code để biết endpoint, rồi gọi để lấy response thật so sánh với model.

    Args:
        url: Full URL, ví dụ: 'https://api.longchau.com/v1/product/abc'
        method: GET hoặc POST (mặc định GET)
        headers: Headers dict, ví dụ: {'Authorization': 'Bearer token...'}
        body: Request body cho POST (mặc định rỗng)
    """
    import urllib.request
    import urllib.error

    try:
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        for k, v in headers.items():
            req.add_header(k, v)

        with urllib.request.urlopen(req, timeout=10) as res:
            raw = res.read().decode("utf-8", errors="replace")
            # Pretty print nếu là JSON
            try:
                parsed = json.loads(raw)
                return json.dumps(parsed, ensure_ascii=False, indent=2)
            except Exception:
                return raw

    except urllib.error.HTTPError as e:
        body_err = e.read().decode("utf-8", errors="replace")
        return json.dumps({
            "error": f"HTTP {e.code}",
            "message": str(e.reason),
            "body": body_err[:2000]
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def list_nodes(node_type: str = "", limit: int = 50) -> str:
    """
    Liệt kê các nodes trong knowledge graph.

    Args:
        node_type: Lọc theo type: Controller, UI, Module, Repository, Service (để trống = tất cả)
        limit: Số lượng tối đa (mặc định 50)
    """
    _init()
    nodes = _State.graph["nodes"]
    if node_type:
        nodes = [n for n in nodes if n.get("type", "").lower() == node_type.lower()]
    return json.dumps(nodes[:limit], ensure_ascii=False, indent=2)


@mcp.tool()
def search_by_filename(pattern: str, repo: str = "") -> str:
    """
    Tìm file theo tên (wildcard) trong tất cả repo Flutter.
    Dùng khi biết tên file/feature nhưng không nhớ đường dẫn đầy đủ.

    Args:
        pattern: Tên file hoặc pattern, ví dụ: 'cart_bloc', 'voucher', '*_model*'
        repo: Giới hạn trong 1 repo cụ thể, ví dụ: 'khlc-cart' (để trống = tất cả)
    """
    import fnmatch

    pattern_lower = pattern.lower().replace('*', '')
    results = []

    search_root = os.path.join(FPT_ROOT, repo) if repo else FPT_ROOT

    for dirpath, _, files in os.walk(search_root):
        if any(skip in dirpath for skip in ('/build/', '/.dart_tool/', '/node_modules/', '/venv/', '/.pub-cache/', '/KHNT/', '/data/')):
            continue
        # Chỉ scan trong khlc-* repos khi search toàn bộ FPT_ROOT
        if not repo and search_root == FPT_ROOT:
            rel_to_root = os.path.relpath(dirpath, FPT_ROOT)
            top_folder = rel_to_root.split(os.sep)[0]
            if not top_folder.startswith('khlc-'):
                continue
        for fname in files:
            if not fname.endswith('.dart'):
                continue
            # Wildcard match hoặc substring match
            if fnmatch.fnmatch(fname.lower(), f"*{pattern_lower}*"):
                full_path = os.path.join(dirpath, fname)
                rel = os.path.relpath(full_path, FPT_ROOT)
                # Kiểm tra xem file này có trong graph không
                in_graph = any(
                    _node_path(nid) == rel or _node_path(nid).endswith(fname)
                    for nid in _State.file_mapping
                ) if _State.file_mapping else False
                results.append({
                    "file": full_path,
                    "relative": rel,
                    "in_graph": in_graph,
                })
                if len(results) >= 30:
                    break
        if len(results) >= 30:
            break

    if not results:
        return json.dumps({"message": f"No .dart files found matching '{pattern}'"})
    return json.dumps(results, ensure_ascii=False, indent=2)


@mcp.tool()
def grep_in_files(keyword: str, repo: str = "", file_pattern: str = "*.dart",
                  max_results: int = 20, context_lines: int = 3) -> str:
    """
    Tìm kiếm text/code trong nội dung file thực tế.
    Dùng khi vector search không tìm ra, hoặc muốn tìm string cụ thể.

    Args:
        keyword: Từ khóa cần tìm trong nội dung file (case-insensitive)
        repo: Giới hạn trong 1 repo, ví dụ: 'khlc-payment' (để trống = tất cả)
        file_pattern: Lọc theo tên file, ví dụ: '*.dart', '*bloc*', '*model*'
        max_results: Số lượng kết quả tối đa (mặc định 20)
        context_lines: Số dòng context xung quanh mỗi match (mặc định 3)
    """
    import fnmatch

    search_root = os.path.join(FPT_ROOT, repo) if repo else FPT_ROOT
    keyword_lower = keyword.lower()
    results = []

    for dirpath, _, files in os.walk(search_root):
        if any(skip in dirpath for skip in ('/build/', '/.dart_tool/', '/node_modules/', '/venv/', '/.pub-cache/', '/KHNT/', '/data/')):
            continue
        # Chỉ scan trong khlc-* repos khi search toàn bộ FPT_ROOT
        if not repo and search_root == FPT_ROOT:
            rel_to_root = os.path.relpath(dirpath, FPT_ROOT)
            top_folder = rel_to_root.split(os.sep)[0]
            if not top_folder.startswith('khlc-'):
                continue
        for fname in files:
            if not fnmatch.fnmatch(fname, file_pattern):
                continue
            full_path = os.path.join(dirpath, fname)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
            except Exception:
                continue

            matches = []
            for i, line in enumerate(lines):
                if keyword_lower in line.lower():
                    start = max(0, i - context_lines)
                    end = min(len(lines), i + context_lines + 1)
                    snippet = ''.join(
                        f"{j+1:4}: {'>>>' if j == i else '   '} {lines[j]}"
                        for j in range(start, end)
                    )
                    matches.append({"line": i + 1, "snippet": snippet})
                    if len(matches) >= 3:
                        break

            if matches:
                results.append({
                    "file": full_path,
                    "relative": os.path.relpath(full_path, FPT_ROOT),
                    "matches": matches,
                })
                if len(results) >= max_results:
                    break
        if len(results) >= max_results:
            break

    if not results:
        return json.dumps({"message": f"No matches found for '{keyword}'"})
    return json.dumps(results, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────
# Steering management
# ─────────────────────────────────────────
TEMPLATES_DIR = os.path.join(GRAPHCODE_DIR, "steering_templates")

IDE_CONFIG = {
    "kiro": {
        "files": {
            ".kiro/steering/00-workflow.md": "kiro/00-workflow.md",
            ".kiro/steering/session-lifecycle.md": "kiro/session-lifecycle.md",
        },
        "label": "Kiro (.kiro/steering/)",
    },
    "antigravity": {
        "files": {"GEMINI.md": "workflow_full.md"},
        "label": "Google Antigravity (GEMINI.md)",
    },
    "cursor": {
        "files": {".cursorrules": "workflow_full.md"},
        "label": "Cursor (.cursorrules)",
    },
    "windsurf": {
        "files": {".windsurfrules": "workflow_full.md"},
        "label": "Windsurf (.windsurfrules)",
    },
    "claude-code": {
        "files": {"CLAUDE.md": "workflow_full.md"},
        "label": "Claude Code (CLAUDE.md)",
    },
    "codex": {
        "files": {"AGENTS.md": "workflow_full.md"},
        "label": "Codex / OpenAI (AGENTS.md)",
    },
}


@mcp.tool()
def init_steering(project_path: str, ide: str = "kiro") -> str:
    """
    Khởi tạo workflow rules cho project mới.
    Copy steering templates từ flutter-context vào project theo đúng format của IDE.

    Args:
        project_path: Đường dẫn tuyệt đối đến project (ví dụ: /Users/dungtv54/FPT/khlc-mobile)
        ide: IDE đang dùng — kiro | antigravity | cursor | windsurf | claude-code | codex
    """
    ide = ide.lower()
    if ide not in IDE_CONFIG:
        return json.dumps({
            "error": f"IDE '{ide}' không hỗ trợ.",
            "supported": list(IDE_CONFIG.keys()),
        })

    if not os.path.isdir(project_path):
        return json.dumps({"error": f"Project path không tồn tại: {project_path}"})

    config = IDE_CONFIG[ide]
    created, skipped = [], []

    for dest_rel, src_rel in config["files"].items():
        src_path = os.path.join(TEMPLATES_DIR, src_rel)
        dest_path = os.path.join(project_path, dest_rel)

        if not os.path.exists(src_path):
            return json.dumps({"error": f"Template không tồn tại: {src_path}"})

        if os.path.exists(dest_path):
            skipped.append(dest_rel)
            continue

        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(src_path, "r", encoding="utf-8") as f:
            content = f.read()
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(content)
        created.append(dest_rel)

    return json.dumps({
        "ide": config["label"],
        "project": project_path,
        "created": created,
        "skipped_already_exists": skipped,
        "status": "done" if created else "nothing_to_do",
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def check_steering(project_path: str, ide: str = "kiro") -> str:
    """
    Kiểm tra project đã có steering/workflow files chưa.

    Args:
        project_path: Đường dẫn tuyệt đối đến project
        ide: IDE đang dùng — kiro | antigravity | cursor | windsurf | claude-code | codex
    """
    ide = ide.lower()
    if ide not in IDE_CONFIG:
        return json.dumps({
            "error": f"IDE '{ide}' không hỗ trợ.",
            "supported": list(IDE_CONFIG.keys()),
        })

    config = IDE_CONFIG[ide]
    result = {}
    all_exist = True

    for dest_rel in config["files"]:
        dest_path = os.path.join(project_path, dest_rel)
        exists = os.path.exists(dest_path)
        result[dest_rel] = "✅ exists" if exists else "❌ missing"
        if not exists:
            all_exist = False

    return json.dumps({
        "ide": config["label"],
        "project": project_path,
        "files": result,
        "ready": all_exist,
        "action": "OK" if all_exist else "Chạy init_steering() để tạo",
    }, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────
# Incremental rebuild (reusable by watch daemon)
# ─────────────────────────────────────────
def _incremental_rebuild(changed_files: list[str]):
    """Rebuild vector DB for specific changed files. Called by watch daemon."""
    from extract_graph import scan_changed_only, _hash_file

    if _State.graph is None or _State.model is None:
        _init()

    # Load hash store
    if os.path.exists(HASH_STORE_FILE):
        with open(HASH_STORE_FILE, "r") as f:
            hash_store = json.load(f)
    else:
        hash_store = {}

    # Reverse mapping: rel_path → set of node_ids
    path_to_nodes: dict = {}
    for node_id, path_info in _State.file_mapping.items():
        rel = path_info["path"] if isinstance(path_info, dict) else path_info
        path_to_nodes.setdefault(rel, set()).add(node_id)

    # Node IDs thuộc file thay đổi
    changed_rel = {os.path.relpath(p, FPT_ROOT) for p in changed_files if os.path.exists(p)}
    changed_node_ids: set = set()
    for rel, node_ids in path_to_nodes.items():
        if rel in changed_rel:
            changed_node_ids.update(node_ids)

    if not changed_node_ids:
        return

    # Giữ lại embeddings cũ
    old_embeddings: dict = {}
    if _State.db is not None:
        for meta, emb in zip(_State.db["metadata"], _State.db["embeddings"]):
            if meta["id"] not in changed_node_ids:
                old_embeddings[meta["id"]] = (meta, emb)

    # Re-embed changed nodes
    node_meta_map = {n["id"]: n for n in _State.graph.get("nodes", [])}
    new_documents, new_metadata = [], []
    for node_id in changed_node_ids:
        if node_id not in _State.file_mapping:
            continue
        path_info = _State.file_mapping[node_id]
        rel = path_info["path"] if isinstance(path_info, dict) else path_info
        full_path = os.path.join(FPT_ROOT, rel)
        content = ""
        if os.path.exists(full_path):
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(4096)
            except Exception:
                pass
        vi_keywords = _enrich_vi_keywords(node_id)
        vi_section = f"Mô tả: {vi_keywords}" if vi_keywords else ""
        text = f"Class: {node_id}\nFile: {rel}\n{vi_section}\n{content[:3000]}"
        new_documents.append(text)
        new_metadata.append({"id": node_id, "file": rel})

    if new_documents:
        new_embs = _State.model.encode(new_documents, batch_size=32, normalize_embeddings=True)
    else:
        new_embs = None

    # Merge
    all_meta = [m for m, _ in old_embeddings.values()]
    all_embs = [e for _, e in old_embeddings.values()]
    all_meta.extend(new_metadata)
    if new_embs is not None:
        all_embs.extend(new_embs)

    merged = np.array(all_embs) if all_embs else np.empty((0, _State.model.dimension))

    with open(DB_FILE, "wb") as f:
        pickle.dump({"embeddings": merged, "metadata": all_meta, "model_name": MODEL_NAME}, f)

    # Update hash store
    for abs_path in changed_files:
        if os.path.exists(abs_path):
            hash_store[abs_path] = _hash_file(abs_path)
    with open(HASH_STORE_FILE, "w") as f:
        json.dump(hash_store, f, indent=2)

    # Reload
    with open(DB_FILE, "rb") as f:
        _State.db = pickle.load(f)

    print(f"[rebuild] {len(new_documents)} nodes re-embedded", file=sys.stderr)


# ─────────────────────────────────────────
# Repo coupling analysis
# ─────────────────────────────────────────
def _detect_cycles(repo_graph: dict) -> list[list[str]]:
    """DFS-based cycle detection on directed graph {node: [neighbors]}."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in repo_graph}
    cycles = []

    def dfs(node, path):
        color[node] = GRAY
        path.append(node)
        for neighbor in repo_graph.get(node, []):
            if color.get(neighbor) == GRAY:
                # Found cycle
                cycle_start = path.index(neighbor)
                cycles.append(path[cycle_start:] + [neighbor])
            elif color.get(neighbor, WHITE) == WHITE:
                dfs(neighbor, path)
        path.pop()
        color[node] = BLACK

    for node in repo_graph:
        if color[node] == WHITE:
            dfs(node, [])
    return cycles


@mcp.tool()
def get_repo_coupling() -> str:
    """
    Phân tích coupling giữa các repo dựa trên cross-repo edges.
    Phát hiện circular dependencies và dependency matrix.
    """
    _init()

    # Build dependency matrix from cross-repo edges
    repo_deps: dict = {}  # {from_repo: {to_repo: count}}
    node_meta_map = {n["id"]: n for n in _State.graph.get("nodes", [])}

    for edge in _State.edges:
        from_node = node_meta_map.get(edge["from"], {})
        to_node = node_meta_map.get(edge["to"], {})
        from_repo = from_node.get("repo", "")
        to_repo = to_node.get("repo", "")
        if from_repo and to_repo and from_repo != to_repo:
            repo_deps.setdefault(from_repo, {})
            repo_deps[from_repo][to_repo] = repo_deps[from_repo].get(to_repo, 0) + 1

    if not repo_deps:
        return json.dumps({"message": "No cross-repo edges found — repos are fully decoupled"})

    # Build directed graph for cycle detection
    repo_graph = {repo: list(deps.keys()) for repo, deps in repo_deps.items()}
    cycles = _detect_cycles(repo_graph)

    # Summary stats
    total_cross_edges = sum(
        count for deps in repo_deps.values() for count in deps.values()
    )
    all_repos = set()
    for repo, deps in repo_deps.items():
        all_repos.add(repo)
        all_repos.update(deps.keys())

    return json.dumps({
        "total_repos": len(all_repos),
        "total_cross_repo_edges": total_cross_edges,
        "dependency_matrix": repo_deps,
        "circular_dependencies": cycles if cycles else "None detected",
        "most_depended_on": sorted(
            [(r, sum(d.get(r, 0) for d in repo_deps.values())) for r in all_repos],
            key=lambda x: x[1], reverse=True
        )[:5],
    }, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────
# Tool filter
# ─────────────────────────────────────────
def _apply_tool_filter():
    """Remove tools not listed in FLUTTER_CONTEXT_TOOLS env var."""
    filter_str = os.environ.get("FLUTTER_CONTEXT_TOOLS", "")
    if not filter_str:
        return  # No filter — keep all tools

    allowed = {t.strip() for t in filter_str.split(",") if t.strip()}
    # Get registered tool names from FastMCP
    registered = set(mcp._tool_manager._tools.keys()) if hasattr(mcp, '_tool_manager') else set()

    # Warn about unknown tool names in filter
    unknown = allowed - registered
    for name in unknown:
        print(f"[filter] Warning: '{name}' not a registered tool", file=sys.stderr)

    # Remove tools not in allowed list
    to_remove = registered - allowed
    for name in to_remove:
        if hasattr(mcp, '_tool_manager') and name in mcp._tool_manager._tools:
            del mcp._tool_manager._tools[name]

    if to_remove:
        print(f"[filter] Disabled {len(to_remove)} tools, kept {len(allowed & registered)}", file=sys.stderr)


# ─────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────
if __name__ == "__main__":
    # Apply tool filter before starting
    _apply_tool_filter()

    # Transport selection
    transport = os.environ.get("FLUTTER_CONTEXT_TRANSPORT", "stdio")

    # Start file watcher if enabled
    if os.environ.get("FLUTTER_CONTEXT_WATCH", "").lower() in ("1", "true", "yes"):
        try:
            from watch_daemon import start_watcher
            start_watcher(FPT_ROOT, _incremental_rebuild)
        except ImportError:
            print("[watch] watchdog not installed, skipping watcher", file=sys.stderr)
        except Exception as e:
            print(f"[watch] Failed to start watcher: {e}", file=sys.stderr)

    if transport == "sse":
        port = int(os.environ.get("FLUTTER_CONTEXT_PORT", "8765"))
        _init()  # Pre-load before serving
        try:
            mcp.run(transport="sse", port=port)
        except OSError as e:
            print(f"Error: Port {port} already in use. Set FLUTTER_CONTEXT_PORT to a different port.", file=sys.stderr)
            sys.exit(1)
    else:
        mcp.run(transport="stdio")
