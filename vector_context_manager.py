
"""
Graph + Vector Context Manager (FINAL)
"""

import json
import os
import pickle
import numpy as np
import sys
from sentence_transformers import SentenceTransformer

FPT_ROOT = "/Users/dungtv54/FPT"
GRAPH_FILE = os.path.join(FPT_ROOT, "data/knowledge_graph.json")
DB_FILE = os.path.join(FPT_ROOT, "data/vector_db.pkl")
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


class SmartContextSelector:
    def __init__(self):
        with open(GRAPH_FILE, "r") as f:
            self.graph = json.load(f)

        self.file_mapping = self.graph["file_mapping"]
        self.edges = self.graph["edges"]
        self._model = None

    @property
    def model(self):
        if self._model is None:
            print("Loading embedding model...", file=sys.stderr)
            self._model = SentenceTransformer(MODEL_NAME)
        return self._model

    # =========================
    # VECTOR SEARCH
    # =========================
    # Nodes bị blacklist vì match quá rộng, gây nhiễu mọi query
    BLACKLIST_NODES = {"KhlcAnalyticsScreens", "HomeScreenToken"}

    def query(self, text, top_k=5):
        with open(DB_FILE, "rb") as f:
            db = pickle.load(f)

        if "flash" in text.lower():
            text += " flash sale fsell product discount"

        q_vec = self.model.encode([text], normalize_embeddings=True)
        scores = (db["embeddings"] @ q_vec.T).flatten()
        top_indices = np.argsort(scores)[::-1][:top_k + len(self.BLACKLIST_NODES) + 5]

        results = []
        for idx in top_indices:
            node = db["metadata"][idx]["id"]
            if node in self.file_mapping and node not in self.BLACKLIST_NODES:
                results.append(node)
            if len(results) >= top_k:
                break

        return results

    # =========================
    # GRAPH FLOW TRACER
    # =========================
    def trace_flow(self, start_nodes, max_depth=5):
        visited = set()
        flow = []

        def dfs(node, depth):
            if depth > max_depth or node in visited:
                return
            visited.add(node)
            flow.append(node)

            for edge in self.edges:
                if edge["from"] == node and edge["type"] in ["routes_to", "depends_on", "binds"]:
                    dfs(edge["to"], depth + 1)

        # Đi xuôi từ start nodes
        for node in start_nodes:
            dfs(node, 0)

        # Đi ngược: tìm UI Page/Screen nào depends_on các node đã tìm được
        # để bổ sung entry point vào đầu flow
        flow_set = set(flow)
        ui_entries = []
        for edge in self.edges:
            if (edge["to"] in flow_set
                    and edge["type"] == "depends_on"
                    and edge["from"] not in flow_set
                    and edge["from"] in self.file_mapping):
                node_info = next((n for n in self.graph.get("nodes", []) if n["id"] == edge["from"]), {})
                if node_info.get("type") in ("UI", "Controller"):
                    ui_entries.append(edge["from"])

        # Prepend UI entries (không trùng lặp)
        for entry in ui_entries:
            if entry not in flow_set:
                flow.insert(0, entry)

        return flow

    # =========================
    # DETECT ENTRY
    # =========================
    def detect_entry_nodes(self, query):
        query = query.lower()
        candidates = []

        for node_id in self.file_mapping:
            name = node_id.lower()

            if "home" in query and "home" in name:
                candidates.append(node_id)

            if "flash" in query and ("flash" in name or "fsell" in name):
                candidates.append(node_id)

        return candidates[:3]

    # =========================
    # GRAPH INFO
    # =========================
    def generate_graph_info(self, nodes):
        node_set = set(nodes)
        lines = ["=== GRAPH CONTEXT ==="]

        for edge in self.edges:
            if edge["from"] in node_set or edge["to"] in node_set:
                lines.append(f"{edge['from']} --[{edge['type']}]--> {edge['to']}")

        return "\n".join(lines)


# =========================
# CLI / SERVER MODE
# =========================
def run_query(selector, query):
    def to_files(nodes):
        seen = set()
        result = []
        for n in nodes:
            if n in selector.file_mapping:
                path = os.path.join(FPT_ROOT, selector.file_mapping[n])
                if path not in seen:
                    seen.add(path)
                    result.append(path)
        return result

    base_nodes = selector.query(query)
    entry_nodes = selector.detect_entry_nodes(query) or base_nodes
    flow_nodes = selector.trace_flow(entry_nodes)

    return {
        "files": to_files(base_nodes),
        "flow": to_files(flow_nodes),
        "graph": selector.generate_graph_info(flow_nodes)
    }


if __name__ == "__main__":
    selector = SmartContextSelector()

    # Single query mode
    if len(sys.argv) >= 2:
        query = sys.argv[1]
        print(json.dumps(run_query(selector, query)))
        exit()

    # Server mode: đọc query từ stdin, trả kết quả qua stdout
    # Model chỉ load 1 lần, tái dùng cho mọi query
    print("READY", flush=True)
    for line in sys.stdin:
        query = line.strip()
        if not query:
            continue
        try:
            result = run_query(selector, query)
            print(json.dumps(result), flush=True)
        except Exception as e:
            print(json.dumps({"error": str(e)}), flush=True)