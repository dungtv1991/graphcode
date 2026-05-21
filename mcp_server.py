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
from sentence_transformers import SentenceTransformer

# ─────────────────────────────────────────
# Config
# ─────────────────────────────────────────
FPT_ROOT = "/Users/dungtv54/FPT"
GRAPH_FILE = os.path.join(FPT_ROOT, "data/knowledge_graph.json")
DB_FILE = os.path.join(FPT_ROOT, "data/vector_db.pkl")
HASH_STORE_FILE = os.path.join(FPT_ROOT, "data/file_hashes.json")
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
}


def _enrich_vi_keywords(class_name: str) -> str:
    """Sinh keywords tiếng Việt từ tên class (CamelCase split)."""
    import re as _re
    words = _re.findall(r'[A-Z][a-z0-9]*|[0-9]+', class_name)
    matched = [VI_KEYWORDS[w] for w in words if w in VI_KEYWORDS]
    return ", ".join(matched)


mcp = FastMCP("flutter-context")

# ─────────────────────────────────────────
# Singleton — load 1 lần khi server start
# ─────────────────────────────────────────
class _State:
    graph = None
    file_mapping = None
    edges = None
    model = None
    db = None

def _init():
    if _State.graph is not None:
        return

    print("Loading knowledge graph...", file=sys.stderr)
    with open(GRAPH_FILE, "r") as f:
        _State.graph = json.load(f)
    _State.file_mapping = _State.graph["file_mapping"]
    _State.edges = _State.graph["edges"]

    print("Loading embedding model...", file=sys.stderr)
    _State.model = SentenceTransformer(MODEL_NAME)

    if os.path.exists(DB_FILE):
        print("Loading vector DB...", file=sys.stderr)
        with open(DB_FILE, "rb") as f:
            _State.db = pickle.load(f)

    print("Ready.", file=sys.stderr)

# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────
def _enrich_query(text: str) -> str:
    """Thêm VI_KEYWORDS vào query để tăng recall khi search."""
    import re as _re
    # Tìm các từ tiếng Anh trong query (có thể là tên class/feature)
    words = _re.findall(r'[A-Za-z][a-z0-9]*', text)
    extra = []
    for w in words:
        key = w.capitalize()
        if key in VI_KEYWORDS:
            extra.append(VI_KEYWORDS[key])
    if extra:
        text = text + " " + " ".join(extra)
    return text


def _vector_search(text: str, top_k: int) -> list[str]:
    text = _enrich_query(text)
    q_vec = _State.model.encode([text], normalize_embeddings=True)
    scores = (_State.db["embeddings"] @ q_vec.T).flatten()
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [
        _State.db["metadata"][i]["id"]
        for i in top_indices
        if _State.db["metadata"][i]["id"] in _State.file_mapping
    ]

def _detect_entry_nodes(query: str) -> list[str]:
    q = query.lower()
    candidates = []
    for node_id in _State.file_mapping:
        name = node_id.lower()
        if ("home" in q and "home" in name) or \
           ("flash" in q and ("flash" in name or "fsell" in name)):
            candidates.append(node_id)
    return candidates[:3]

def _trace_flow(start_nodes: list[str], max_depth: int = 5) -> list[str]:
    visited, flow = set(), []

    def dfs(node, depth):
        if depth > max_depth or node in visited:
            return
        visited.add(node)
        flow.append(node)
        for edge in _State.edges:
            if edge["from"] == node and edge["type"] in ["routes_to", "depends_on"]:
                dfs(edge["to"], depth + 1)

    for node in start_nodes:
        dfs(node, 0)
    return flow

def _graph_info(nodes: list[str]) -> str:
    node_set = set(nodes)
    lines = ["=== GRAPH CONTEXT ==="]
    for edge in _State.edges:
        if edge["from"] in node_set or edge["to"] in node_set:
            lines.append(f"{edge['from']} --[{edge['type']}]--> {edge['to']}")
    return "\n".join(lines)

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
        _State.model = SentenceTransformer(MODEL_NAME)

    # 1. Load hash store
    if os.path.exists(HASH_STORE_FILE):
        with open(HASH_STORE_FILE, "r") as f:
            hash_store = json.load(f)
    else:
        hash_store = {}

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

    merged = np.array(all_embs) if all_embs else np.empty((0, 384))

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

    unchanged_count = len(old_embeddings)
    new_count = len(new_documents)
    deleted_count = len(deleted_node_ids)
    return (
        f"Done! {len(all_meta)} total vectors "
        f"({new_count} re-embedded, {unchanged_count} unchanged, {deleted_count} deleted) "
        f"— {size_mb:.1f} MB"
    )


@mcp.tool()
def query_context(query: str, top_k: int = 5, snippet_chars: int = 300) -> str:
    """
    Tìm các file Flutter liên quan đến query dựa trên semantic search + knowledge graph.
    Trả về file paths, graph relationships, và snippet ngắn của mỗi file.
    Dùng get_file_content để đọc đầy đủ nội dung file cần thiết.

    Args:
        query: Câu hỏi hoặc mô tả tính năng cần tìm (tiếng Việt hoặc tiếng Anh)
        top_k: Số lượng kết quả vector search (mặc định 5)
        snippet_chars: Số ký tự preview mỗi file để nhận diện nhanh (mặc định 300, đặt 0 để tắt)
    """
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
        "flow_files": _to_files(flow_nodes),
        "graph": _graph_info(flow_nodes),
        "flow_nodes": flow_nodes[:20],
    }
    return json.dumps(result, ensure_ascii=False, indent=2)


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
        for edge in _State.edges:
            if edge["to"] == node and edge["type"] in ("depends_on", "binds", "has_part"):
                caller = edge["from"]
                if caller not in affected:
                    affected[caller] = {
                        "depth": depth,
                        "via_edge": edge["type"],
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
        if any(skip in dirpath for skip in ('/build/', '/.dart_tool/', '/node_modules/', '/venv/', '/.pub-cache/')):
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
        if any(skip in dirpath for skip in ('/build/', '/.dart_tool/', '/node_modules/', '/venv/', '/.pub-cache/')):
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
TEMPLATES_DIR = os.path.join(FPT_ROOT, "data/steering_templates")

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
# Entry point
# ─────────────────────────────────────────
if __name__ == "__main__":
    mcp.run(transport="stdio")
