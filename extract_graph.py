"""
Flutter Knowledge Graph Extractor — Tree-sitter powered
Chính xác hơn regex: bắt được class, extension, mixin, typedef, anonymous class
"""
import os
import re
import json
import hashlib
import warnings
warnings.filterwarnings('ignore')

# ─── Hash utilities ──────────────────────────────────────────────────────────
def _hash_file(path: str) -> str:
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


# ─── Tree-sitter setup ───────────────────────────────────────────────────────
try:
    from tree_sitter import Language, Parser as TSParser
    _DART_LIB = os.path.join(os.path.dirname(__file__), 'dart_lang.so')
    _DART_GRAMMAR = os.path.join(os.path.dirname(__file__), 'node_modules/tree-sitter-dart')

    if not os.path.exists(_DART_LIB):
        print(f"Building Dart grammar → {_DART_LIB}")
        Language.build_library(_DART_LIB, [_DART_GRAMMAR])

    DART_LANG = Language(_DART_LIB, 'dart')
    _ts_parser = TSParser()
    _ts_parser.set_language(DART_LANG)
    USE_TREESITTER = True
    print("✅ Tree-sitter Dart parser ready")
except Exception as e:
    USE_TREESITTER = False
    print(f"⚠️  Tree-sitter unavailable ({e}), falling back to regex")


# ─── Node summary builder ────────────────────────────────────────────────────
def _build_summary(node_id: str, node_type: str, base_class: str,
                   methods: list, events: list, api_paths: list) -> str:
    """Tạo summary ngắn gọn (~80 chars) thay thế raw code snippet."""
    parts = [node_type]
    if base_class and base_class not in ('', 'Mixin'):
        parts.append(f"extends {base_class}")
    if events:
        parts.append(f"on<{','.join(events[:3])}>")
    elif methods:
        parts.append(f"fn:{','.join(methods[:4])}")
    if api_paths:
        parts.append(f"api:{api_paths[0]}")
    return " | ".join(parts)


# ─── Node type classifier ─────────────────────────────────────────────────────
def _classify_node(name: str, base: str) -> str:
    if "Module" in base or "Module" in name:
        return "Module"
    if any(x in name for x in ("Bloc", "Cubit", "Controller", "Store")):
        return "Controller"
    if "Service" in name:
        return "Service"
    if any(x in name for x in ("Repository", "Gateway", "Api", "Datasource", "DataSource")):
        return "Repository"
    if any(x in name for x in ("Page", "Screen", "View")):
        return "UI"
    if "UseCase" in name:
        return "UseCase"
    if any(x in name for x in ("Event",)) and name.endswith("Event"):
        return "Event"
    if name.endswith("State"):
        return "State"
    # Data layer types
    if any(x in name for x in ("Model", "Entity", "Dto", "Response", "VO")):
        return "Model"
    if any(x in name for x in ("Resource", "Mapper", "Converter", "Transformer")):
        return "Resource"
    if any(x in name for x in ("Param", "Request", "Body", "Input")):
        return "Param"
    # Navigation
    if any(x in name for x in ("Route", "Router", "Routes")):
        return "Route"
    # UI components
    if any(x in name for x in ("Widget", "Button", "Card", "Dialog", "Sheet",
                                "Item", "Tile", "Cell", "Badge", "Chip", "Tag")):
        return "Widget"
    return "Unknown"


# ─── Tree-sitter parser ───────────────────────────────────────────────────────
_RE_MODULAR_GET = re.compile(r'(?:i|Modular)\.get<(\w+)>')
_RE_BIND = re.compile(r'Bind\.(?:\w+)\(\(i\)\s*=>\s*(\w+)\(')
_RE_ROUTE_MODULE = re.compile(r'r\.module\([\'"](.+?)[\'"],\s*module:\s*(\w+)\(\)')
_RE_ON_EVENT = re.compile(r'on<(\w+)>\s*\(')
_RE_API_PATH = re.compile(r"['\"]([/][a-zA-Z0-9/_\-{}]+)['\"]")
_RE_ROUTE_PATH = re.compile(r"static\s+(?:const\s+)?String\s+\w+\s*=\s*['\"]([/][a-z0-9/_\-]+)['\"]")
_RE_ERROR = re.compile(r'(?:throw\s+(\w+)|catch\s*\(\w+\s+(\w+)\)|on\s+(\w+Exception|\w+Error)\s*\{)')
_RE_METHOD = re.compile(r'(?:Future|Stream|void|bool|String|int|double|List|Map)\s+(\w+)\s*\(')
_RE_EVENT_CLASS = re.compile(r'class\s+(\w+Event)\b')
_RE_STATE_CLASS = re.compile(r'class\s+(\w+State)\b')


def _ts_find_text(node, target_type):
    """Tìm tất cả node có type = target_type, trả về text."""
    results = []
    if node.type == target_type:
        results.append(node.text.decode('utf-8', errors='replace'))
    for child in node.children:
        results.extend(_ts_find_text(child, target_type))
    return results


def _ts_get_class_name(node):
    """Lấy tên class/extension/mixin từ tree-sitter node."""
    for child in node.children:
        if child.type == 'identifier':
            return child.text.decode('utf-8', errors='replace')
    return None


def _ts_get_superclass(node):
    """Lấy tên superclass từ class_definition node."""
    for child in node.children:
        if child.type == 'superclass':
            for sub in child.children:
                if sub.type == 'type_name':
                    return sub.text.decode('utf-8', errors='replace').split('<')[0]
                if sub.type == 'identifier':
                    return sub.text.decode('utf-8', errors='replace')
    return ''


def parse_dart_file_ts(file_path: str, repo_name: str, root_dir: str):
    """Parse Dart file bằng Tree-sitter. Trả về (nodes, edges)."""
    relative_path = os.path.join(
        repo_name,
        os.path.relpath(file_path, os.path.join(root_dir, repo_name))
    )
    filename = os.path.basename(file_path)

    try:
        with open(file_path, 'rb') as f:
            content_bytes = f.read()
        content = content_bytes.decode('utf-8', errors='replace')
    except Exception:
        return [], [], {}

    nodes_out = []
    edges_out = []
    file_mapping_out = {}

    # ── P1: event/state part files ──────────────────────────────────────────
    if filename.endswith('_event.dart') or filename.endswith('_state.dart'):
        event_classes = _RE_EVENT_CLASS.findall(content)
        state_classes = _RE_STATE_CLASS.findall(content)
        all_classes = event_classes + state_classes
        if all_classes:
            node_id = filename.replace('.dart', '').replace('_', ' ').title().replace(' ', '')
            node_type = 'Event' if filename.endswith('_event.dart') else 'State'
            nodes_out.append({
                "id": node_id, "type": node_type, "repo": repo_name,
                "classes": all_classes[:20],
                "methods": [], "events": [], "api_paths": [],
                "route_paths": [], "error_types": [],
            })
            file_mapping_out[node_id] = relative_path
            bloc_name = node_id.replace('Event', 'Bloc').replace('State', 'Bloc')
            edges_out.append({"from": bloc_name, "to": node_id, "type": "has_part"})
        return nodes_out, edges_out, file_mapping_out

    # ── Tree-sitter parse ────────────────────────────────────────────────────
    tree = _ts_parser.parse(content_bytes)
    root = tree.root_node

    # Collect all class-like declarations
    declarations = []
    for node in root.children:
        if node.type in ('class_definition', 'extension_declaration', 'mixin_declaration'):
            declarations.append(node)

    if not declarations:
        return nodes_out, edges_out, file_mapping_out

    # Shared metadata từ file content (dùng regex trên text)
    methods = list(set(_RE_METHOD.findall(content)))[:10]
    events = list(set(_RE_ON_EVENT.findall(content)))[:10]
    api_paths = [p for p in set(_RE_API_PATH.findall(content)) if len(p) > 3][:5]
    route_paths = _RE_ROUTE_PATH.findall(content)[:3]
    error_matches = _RE_ERROR.findall(content)
    error_types = list(set(t for group in error_matches for t in group if t))[:5]

    current_classes = []

    for decl in declarations:
        class_name = _ts_get_class_name(decl)
        if not class_name:
            continue

        if decl.type == 'class_definition':
            base_class = _ts_get_superclass(decl)
        elif decl.type == 'extension_declaration':
            # extension X on Y → base = Y
            base_class = ''
            for child in decl.children:
                if child.type == 'type_name':
                    base_class = child.text.decode('utf-8', errors='replace').split('<')[0]
        elif decl.type == 'mixin_declaration':
            base_class = 'Mixin'
        else:
            base_class = ''

        node_type = _classify_node(class_name, base_class)
        start_line = decl.start_point[0] + 1  # tree-sitter là 0-indexed

        nodes_out.append({
            "id": class_name,
            "type": node_type,
            "repo": repo_name,
            "methods": methods,
            "events": events,
            "api_paths": api_paths,
            "route_paths": route_paths,
            "error_types": error_types,
            "base_class": base_class,
            "start_line": start_line,
            "summary": _build_summary(class_name, node_type, base_class,
                                      methods, events, api_paths),
        })
        file_mapping_out[class_name] = {"path": relative_path, "line": start_line}
        current_classes.append(class_name)

    if not current_classes:
        return nodes_out, edges_out, file_mapping_out

    main_node = current_classes[0]

    # Edges từ DI patterns
    for dep in set(_RE_MODULAR_GET.findall(content)):
        if dep != main_node:
            edges_out.append({"from": main_node, "to": dep, "type": "depends_on"})

    for bind_target in set(_RE_BIND.findall(content)):
        if bind_target != main_node:
            edges_out.append({"from": main_node, "to": bind_target, "type": "binds"})

    for _, target_module in _RE_ROUTE_MODULE.findall(content):
        edges_out.append({"from": main_node, "to": target_module, "type": "routes_to"})

    return nodes_out, edges_out, file_mapping_out


# ─── Regex fallback parser (giữ lại cho safety) ──────────────────────────────
def parse_dart_file_regex(file_path: str, repo_name: str, root_dir: str):
    """Fallback regex parser — dùng khi tree-sitter không available."""
    relative_path = os.path.join(
        repo_name,
        os.path.relpath(file_path, os.path.join(root_dir, repo_name))
    )
    filename = os.path.basename(file_path)

    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception:
        return [], [], {}

    nodes_out, edges_out, file_mapping_out = [], [], {}

    if filename.endswith('_event.dart') or filename.endswith('_state.dart'):
        event_classes = _RE_EVENT_CLASS.findall(content)
        state_classes = _RE_STATE_CLASS.findall(content)
        all_classes = event_classes + state_classes
        if all_classes:
            node_id = filename.replace('.dart', '').replace('_', ' ').title().replace(' ', '')
            node_type = 'Event' if filename.endswith('_event.dart') else 'State'
            nodes_out.append({
                "id": node_id, "type": node_type, "repo": repo_name,
                "classes": all_classes[:20], "methods": [], "events": [],
                "api_paths": [], "route_paths": [], "error_types": [],
            })
            file_mapping_out[node_id] = relative_path
            bloc_name = node_id.replace('Event', 'Bloc').replace('State', 'Bloc')
            edges_out.append({"from": bloc_name, "to": node_id, "type": "has_part"})
        return nodes_out, edges_out, file_mapping_out

    # Match cả class có inheritance lẫn class standalone
    class_inherit = re.compile(r'class\s+(\w+)\s+(?:extends|with|implements)\s+(\w+)')
    class_standalone = re.compile(r'class\s+(\w+)\s*[{<]')
    classes = list(class_inherit.findall(content))  # [(name, base), ...]
    seen_names = {name for name, _ in classes}
    for name in class_standalone.findall(content):
        if name not in seen_names:
            classes.append((name, ''))
            seen_names.add(name)
    current_classes = []

    methods = list(set(_RE_METHOD.findall(content)))[:10]
    events = list(set(_RE_ON_EVENT.findall(content)))[:10]
    api_paths = [p for p in set(_RE_API_PATH.findall(content)) if len(p) > 3][:5]
    route_paths = _RE_ROUTE_PATH.findall(content)[:3]
    error_matches = _RE_ERROR.findall(content)
    error_types = list(set(t for group in error_matches for t in group if t))[:5]

    # Tìm start_line cho từng class bằng regex
    _class_line_pattern = re.compile(r'^.*\bclass\s+(\w+)\b', re.MULTILINE)
    class_lines = {m.group(1): m.start() for m in _class_line_pattern.finditer(content)}
    line_offsets = [i for i, c in enumerate(content) if c == '\n']

    def _char_to_line(char_pos: int) -> int:
        return next((i + 1 for i, o in enumerate(line_offsets) if o >= char_pos), 1)

    for class_name, base_class in classes:
        node_type = _classify_node(class_name, base_class)
        start_line = _char_to_line(class_lines.get(class_name, 0))
        nodes_out.append({
            "id": class_name, "type": node_type, "repo": repo_name,
            "methods": methods, "events": events, "api_paths": api_paths,
            "route_paths": route_paths, "error_types": error_types,
            "base_class": base_class,
            "start_line": start_line,
            "summary": _build_summary(class_name, node_type, base_class,
                                      methods, events, api_paths),
        })
        file_mapping_out[class_name] = {"path": relative_path, "line": start_line}
        current_classes.append(class_name)

    if not current_classes:
        return nodes_out, edges_out, file_mapping_out

    main_node = current_classes[0]
    for dep in set(_RE_MODULAR_GET.findall(content)):
        if dep != main_node:
            edges_out.append({"from": main_node, "to": dep, "type": "depends_on"})
    for bind_target in set(_RE_BIND.findall(content)):
        if bind_target != main_node:
            edges_out.append({"from": main_node, "to": bind_target, "type": "binds"})
    for _, target_module in _RE_ROUTE_MODULE.findall(content):
        edges_out.append({"from": main_node, "to": target_module, "type": "routes_to"})

    return nodes_out, edges_out, file_mapping_out


# ─── Main parser (auto-select) ────────────────────────────────────────────────
def parse_dart_file(file_path: str, repo_name: str, root_dir: str):
    if USE_TREESITTER:
        return parse_dart_file_ts(file_path, repo_name, root_dir)
    return parse_dart_file_regex(file_path, repo_name, root_dir)


# ─── Multi-repo scanner ───────────────────────────────────────────────────────
class FlutterModularMultiRepoParser:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.nodes = []
        self.edges = []
        self.file_mapping = {}

    def scan_all_repos(self):
        print(f"Scanning all khlc-* repos in: {self.root_dir}...")
        repos = [
            d for d in os.listdir(self.root_dir)
            if d.startswith('khlc-') and os.path.isdir(os.path.join(self.root_dir, d))
        ]
        for repo_name in repos:
            lib_path = os.path.join(self.root_dir, repo_name, 'lib')
            if not os.path.exists(lib_path):
                continue
            print(f"  -> Indexing: {repo_name}...")
            for root, _, files in os.walk(lib_path):
                for file in files:
                    if file.endswith('.dart') and not file.endswith('.g.dart'):
                        n, e, fm = parse_dart_file(
                            os.path.join(root, file), repo_name, self.root_dir
                        )
                        self.nodes.extend(n)
                        self.edges.extend(e)
                        self.file_mapping.update(fm)

    def save_results(self):
        # Deduplicate nodes
        unique_nodes = {}
        for n in self.nodes:
            if n['id'] not in unique_nodes:
                unique_nodes[n['id']] = n

        # Deduplicate edges
        edge_set = set()
        unique_edges = []
        for e in self.edges:
            key = (e['from'], e['to'], e['type'])
            if key not in edge_set:
                edge_set.add(key)
                unique_edges.append(e)

        # similar_to edges
        unique_edges += self._build_similar_to_edges(unique_nodes, unique_edges)

        output = {
            "nodes": list(unique_nodes.values()),
            "edges": unique_edges,
            "file_mapping": self.file_mapping,
            "parser": "tree-sitter" if USE_TREESITTER else "regex",
        }

        output_file = os.path.join(self.root_dir, 'data', 'knowledge_graph.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print("\n--- Global Workspace Extraction Complete ---")
        print(f"Parser: {'Tree-sitter ✅' if USE_TREESITTER else 'Regex (fallback)'}")
        print(f"Total Repos Indexed: {len(set(n['repo'] for n in output['nodes']))}")
        print(f"Total Nodes: {len(output['nodes'])}")
        print(f"Total Edges: {len(unique_edges)}")
        print(f"Output saved to: {output_file}")

    def _build_similar_to_edges(self, nodes_dict, edges):
        module_usecases = {}
        for e in edges:
            if e['type'] == 'binds' and 'UseCase' in e['to']:
                mod = e['from']
                if mod not in module_usecases:
                    module_usecases[mod] = set()
                module_usecases[mod].add(e['to'])

        similar_edges = []
        edge_set = set()
        modules = list(module_usecases.keys())
        for i, m1 in enumerate(modules):
            for m2 in modules[i+1:]:
                shared = module_usecases[m1] & module_usecases[m2]
                if shared:
                    key = tuple(sorted([m1, m2]))
                    if key not in edge_set:
                        edge_set.add(key)
                        similar_edges.append({
                            "from": m1, "to": m2,
                            "type": "similar_to",
                            "shared_usecases": list(shared)[:3]
                        })
        return similar_edges


# ─── Incremental scan ────────────────────────────────────────────────────────
def scan_changed_only(root_dir: str, hash_store: dict, file_mapping: dict = None):
    """
    Compare SHA-256 hashes of all .dart files against hash_store.

    Returns:
        changed_files  — list of absolute paths that are new or content-changed
        deleted_node_ids — list of node IDs whose source files no longer exist
    """
    current_files = {}  # abs_path -> hash
    repos = [
        d for d in os.listdir(root_dir)
        if d.startswith('khlc-') and os.path.isdir(os.path.join(root_dir, d))
    ]
    for repo_name in repos:
        lib_path = os.path.join(root_dir, repo_name, 'lib')
        if not os.path.exists(lib_path):
            continue
        for root, _, files in os.walk(lib_path):
            for file in files:
                if file.endswith('.dart') and not file.endswith('.g.dart'):
                    abs_path = os.path.join(root, file)
                    current_files[abs_path] = _hash_file(abs_path)

    changed_files = [
        path for path, h in current_files.items()
        if hash_store.get(path) != h
    ]

    deleted_paths = set(hash_store.keys()) - set(current_files.keys())

    deleted_node_ids = []
    if file_mapping and deleted_paths:
        # file_mapping values are {"path": rel_path, "line": N} or plain rel_path strings
        deleted_rel = {os.path.relpath(p, root_dir) for p in deleted_paths}
        for node_id, path_info in file_mapping.items():
            rel_path = path_info['path'] if isinstance(path_info, dict) else path_info
            if rel_path in deleted_rel:
                deleted_node_ids.append(node_id)

    return changed_files, deleted_node_ids


if __name__ == "__main__":
    root_dir = "/Users/dungtv54/FPT"
    parser = FlutterModularMultiRepoParser(root_dir)
    parser.scan_all_repos()
    parser.save_results()
