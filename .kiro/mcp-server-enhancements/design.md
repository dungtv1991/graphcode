# Design Document

## Overview

This design describes the implementation approach for 8 enhancements to the flutter-context MCP server. The changes span three existing files (`mcp_server.py`, `extract_graph.py`, `vector_context_manager.py`) and introduce two new modules (`watch_daemon.py`, `embedding_provider.py`). The design prioritizes backward compatibility — all existing tool signatures and behaviors remain unchanged.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     MCP Server (mcp_server.py)               │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │ Tool     │  │ Adjacency    │  │ Embedding Provider    │  │
│  │ Filter   │  │ Index        │  │ (local/openai/azure)  │  │
│  └──────────┘  └──────────────┘  └───────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐│
│  │ Transport Layer (stdio | HTTP/SSE)                       ││
│  └──────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ extract_graph.py│  │ vector_db.pkl    │  │ watch_daemon.py  │
│ + cross-repo    │  │ (embeddings)     │  │ (inotify/fsevents│
│ + tested_by     │  │                  │  │  → incremental)  │
│ + implements    │  │                  │  │                  │
└─────────────────┘  └──────────────────┘  └──────────────────┘
```

## Component Designs

### 1. Adjacency Index (mcp_server.py)

**Data Structure:**
```python
# Built at _init() time from _State.edges
_State.adj_forward: dict[str, list[dict]]  # node → [{"to": ..., "type": ...}, ...]
_State.adj_reverse: dict[str, list[dict]]  # node → [{"from": ..., "type": ...}, ...]
```

**Build Logic:**
```python
def _build_adjacency_index():
    _State.adj_forward = defaultdict(list)
    _State.adj_reverse = defaultdict(list)
    for edge in _State.edges:
        _State.adj_forward[edge["from"]].append(edge)
        _State.adj_reverse[edge["to"]].append(edge)
```

**Impact on existing functions:**
- `_trace_flow()`: Replace `for edge in _State.edges` with `for edge in _State.adj_forward.get(node, [])`
- `get_blast_radius()`: Replace `for edge in _State.edges` with `for edge in _State.adj_reverse.get(node, [])`
- `_graph_info()`: Use both forward and reverse lookups instead of full scan
- `_init()` and `build_db()`: Call `_build_adjacency_index()` after loading/reloading edges

**Complexity improvement:**
- Before: O(E) per DFS step where E = total edges (~10,000+)
- After: O(d) per DFS step where d = node degree (typically 3-10)

### 2. Cross-Repo Import Resolution (extract_graph.py)

**Package-to-Repo Mapping:**
```python
def _build_package_repo_map(root_dir: str) -> dict[str, str]:
    """Read pubspec.yaml from each khlc-* repo to map package names to repo names."""
    mapping = {}  # package_name → repo_name
    for repo in os.listdir(root_dir):
        if not repo.startswith('khlc-'):
            continue
        pubspec = os.path.join(root_dir, repo, 'pubspec.yaml')
        if os.path.exists(pubspec):
            # Extract 'name:' field from pubspec.yaml
            with open(pubspec) as f:
                for line in f:
                    if line.startswith('name:'):
                        pkg_name = line.split(':')[1].strip()
                        mapping[pkg_name] = repo
                        break
    return mapping
```

**Import Parsing (added to parse_dart_file_ts):**
```python
_RE_IMPORT = re.compile(r"import\s+['\"]package:(\w+)/(.+?)['\"]")

# In parse_dart_file_ts, after existing edge extraction:
for pkg, path in _RE_IMPORT.findall(content):
    if pkg in package_repo_map and package_repo_map[pkg] != repo_name:
        # Resolve imported file to a class node
        target_class = _resolve_import_to_class(pkg, path, package_repo_map)
        if target_class and target_class in known_nodes:
            edges_out.append({"from": main_node, "to": target_class, "type": "imports_from"})
```

**Resolution strategy:** Map `package:khlc_cart/src/domain/cart_bloc.dart` → look up `CartBloc` in existing file_mapping by matching the relative path.

**Integration:** The `package_repo_map` is built once in `FlutterModularMultiRepoParser.__init__()` and passed to each `parse_dart_file()` call.

### 3. Watch Daemon (new file: watch_daemon.py)

**Dependencies:** `watchdog` library (cross-platform filesystem events)

**Design:**
```python
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class DartFileHandler(FileSystemEventHandler):
    def __init__(self, rebuild_callback, debounce_seconds=3.0):
        self.rebuild_callback = rebuild_callback
        self.debounce_seconds = debounce_seconds
        self._pending_files: set[str] = set()
        self._timer: asyncio.TimerHandle | None = None

    def on_modified(self, event):
        if event.src_path.endswith('.dart') and not event.src_path.endswith('.g.dart'):
            self._pending_files.add(event.src_path)
            self._reset_timer()

    def on_created(self, event):
        self.on_modified(event)

    def on_deleted(self, event):
        self.on_modified(event)

    def _reset_timer(self):
        if self._timer:
            self._timer.cancel()
        self._timer = asyncio.get_event_loop().call_later(
            self.debounce_seconds, self._trigger_rebuild
        )

    def _trigger_rebuild(self):
        files = self._pending_files.copy()
        self._pending_files.clear()
        self.rebuild_callback(files)
```

**Integration with MCP Server:**
```python
# In mcp_server.py, after _init():
if os.environ.get("FLUTTER_CONTEXT_WATCH", "0") == "1":
    from watch_daemon import start_watcher
    start_watcher(FPT_ROOT, rebuild_callback=_incremental_rebuild)
```

**Rebuild callback:** Reuses the existing incremental logic from `build_db()` but scoped to only the changed files passed by the watcher.

### 4. Repo Coupling Tool (mcp_server.py)

**New MCP tool:**
```python
@mcp.tool()
def get_repo_coupling() -> str:
    """Show dependency matrix between repos and detect circular dependencies."""
    _init()

    # Build matrix: {(from_repo, to_repo): count}
    matrix = defaultdict(int)
    node_repo_map = {n["id"]: n.get("repo", "") for n in _State.graph.get("nodes", [])}

    for edge in _State.edges:
        if edge["type"] in ("depends_on", "imports_from", "binds", "routes_to"):
            from_repo = node_repo_map.get(edge["from"], "")
            to_repo = node_repo_map.get(edge["to"], "")
            if from_repo and to_repo and from_repo != to_repo:
                matrix[(from_repo, to_repo)] += 1

    # Detect cycles using DFS on repo-level graph
    repo_graph = defaultdict(set)
    for (fr, tr) in matrix:
        repo_graph[fr].add(tr)

    cycles = _detect_cycles(repo_graph)

    return json.dumps({
        "matrix": [{"from": fr, "to": tr, "edge_count": cnt}
                   for (fr, tr), cnt in sorted(matrix.items(), key=lambda x: -x[1])],
        "circular_dependencies": cycles,
        "summary": {
            "total_cross_repo_edges": sum(matrix.values()),
            "repo_pairs": len(matrix),
            "cycles_detected": len(cycles),
        }
    }, ensure_ascii=False, indent=2)
```

**Cycle detection:** Standard DFS-based cycle detection on the directed repo-level graph. Returns list of cycles as ordered repo lists (e.g., `["khlc-cart", "khlc-payment", "khlc-cart"]`).

### 5. TESTED_BY and IMPLEMENTS Edges (extract_graph.py)

**Test file matching:**
```python
def _match_test_to_source(test_filename: str, known_nodes: set) -> str | None:
    """Match test file to source class by naming convention.
    cart_bloc_test.dart → CartBloc
    get_session_id_use_case_test.dart → GetSessionIdUseCase
    """
    base = test_filename.replace('_test.dart', '')
    # Convert snake_case to PascalCase
    class_name = ''.join(word.capitalize() for word in base.split('_'))
    return class_name if class_name in known_nodes else None
```

**Implements parsing (in parse_dart_file_ts):**
```python
def _ts_get_implements(node) -> list[str]:
    """Extract interface names from 'implements' clause."""
    for child in node.children:
        if child.type == 'interfaces':
            return [
                id_node.text.decode('utf-8', errors='replace').split('<')[0]
                for id_node in _ts_find_text(child, 'type_name')
            ]
    return []
```

**Integration:** 
- Test scanning: Add a second pass in `scan_all_repos()` that walks `test/` directories
- Implements: Extract during the existing class declaration parsing loop

### 6. Embedding Provider (new file: embedding_provider.py)

**Interface:**
```python
class EmbeddingProvider:
    def encode(self, texts: list[str], **kwargs) -> np.ndarray:
        """Return normalized embeddings as numpy array."""
        raise NotImplementedError

    @property
    def dimension(self) -> int:
        raise NotImplementedError

class LocalProvider(EmbeddingProvider):
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)

    def encode(self, texts, **kwargs):
        return self.model.encode(texts, normalize_embeddings=True, **kwargs)

    @property
    def dimension(self):
        return self.model.get_sentence_embedding_dimension()

class OpenAIProvider(EmbeddingProvider):
    def __init__(self, model: str, api_key: str):
        import openai
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    def encode(self, texts, **kwargs):
        response = self.client.embeddings.create(input=texts, model=self.model)
        embs = np.array([d.embedding for d in response.data])
        # Normalize
        norms = np.linalg.norm(embs, axis=1, keepdims=True)
        return embs / norms

    @property
    def dimension(self):
        return 1536  # text-embedding-3-small default

class AzureProvider(EmbeddingProvider):
    # Similar to OpenAI but with Azure endpoint configuration
    ...
```

**Factory:**
```python
def create_provider() -> EmbeddingProvider:
    provider_type = os.environ.get("FLUTTER_CONTEXT_EMBEDDING_PROVIDER", "local")
    model = os.environ.get("FLUTTER_CONTEXT_EMBEDDING_MODEL", "")

    try:
        if provider_type == "openai":
            return OpenAIProvider(model or "text-embedding-3-small", os.environ["OPENAI_API_KEY"])
        elif provider_type == "azure":
            return AzureProvider(...)
        else:
            return LocalProvider(model or "paraphrase-multilingual-MiniLM-L12-v2")
    except Exception as e:
        print(f"Warning: Failed to init {provider_type}, falling back to local: {e}", file=sys.stderr)
        return LocalProvider(model or "paraphrase-multilingual-MiniLM-L12-v2")
```

**Integration:** Replace `_State.model = SentenceTransformer(MODEL_NAME)` with `_State.model = create_provider()`. All encode calls go through the provider interface.

### 7. HTTP Transport (mcp_server.py)

**Implementation using FastMCP's built-in SSE support:**
```python
if __name__ == "__main__":
    transport = os.environ.get("FLUTTER_CONTEXT_TRANSPORT", "stdio")

    if transport == "http":
        port = int(os.environ.get("FLUTTER_CONTEXT_PORT", "8765"))
        # FastMCP supports SSE transport natively
        mcp.run(transport="sse", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio")
```

**Notes:**
- FastMCP library already supports SSE transport — no custom HTTP server needed
- SSE transport handles multiple concurrent connections via async event loop
- Port conflict detection is handled by the underlying server (raises OSError)

### 8. Tool Filtering (mcp_server.py)

**Implementation:**
```python
def _apply_tool_filter():
    """Remove tools not in the whitelist from the MCP server."""
    allowed = os.environ.get("FLUTTER_CONTEXT_TOOLS", "")
    if not allowed:
        return  # No filter — expose all tools

    allowed_set = {t.strip() for t in allowed.split(",") if t.strip()}
    registered_tools = list(mcp._tools.keys())  # Access FastMCP internal registry

    for tool_name in registered_tools:
        if tool_name not in allowed_set:
            del mcp._tools[tool_name]
        else:
            allowed_set.discard(tool_name)

    # Warn about unrecognized tool names
    for unknown in allowed_set:
        print(f"Warning: Tool '{unknown}' in FLUTTER_CONTEXT_TOOLS not found", file=sys.stderr)
```

**Invocation:** Called once at startup, after all `@mcp.tool()` decorators have registered but before `mcp.run()`.

## File Changes Summary

| File | Changes |
|------|---------|
| `mcp_server.py` | Add adjacency index build, refactor traversal functions, add `get_repo_coupling` tool, add tool filter, add HTTP transport option, integrate embedding provider |
| `extract_graph.py` | Add cross-repo import parsing, add `implements` edge extraction, add test file scanning, build package-repo map from pubspec.yaml |
| `vector_context_manager.py` | Update `trace_flow` to use adjacency index (keep in sync with mcp_server.py) |
| `embedding_provider.py` (new) | EmbeddingProvider interface + Local/OpenAI/Azure implementations |
| `watch_daemon.py` (new) | Filesystem watcher with debounce + incremental rebuild trigger |
| `requirements.txt` | Add `watchdog` dependency |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLUTTER_CONTEXT_WATCH` | `0` | Set to `1` to enable auto-rebuild on file changes |
| `FLUTTER_CONTEXT_TRANSPORT` | `stdio` | Transport mode: `stdio` or `http` |
| `FLUTTER_CONTEXT_PORT` | `8765` | HTTP port (only when transport=http) |
| `FLUTTER_CONTEXT_TOOLS` | (empty = all) | Comma-separated whitelist of tool names |
| `FLUTTER_CONTEXT_EMBEDDING_PROVIDER` | `local` | Embedding provider: `local`, `openai`, `azure` |
| `FLUTTER_CONTEXT_EMBEDDING_MODEL` | (provider default) | Model name override |
| `OPENAI_API_KEY` | — | Required when provider=openai |
| `AZURE_OPENAI_ENDPOINT` | — | Required when provider=azure |
| `AZURE_OPENAI_KEY` | — | Required when provider=azure |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | — | Required when provider=azure |

## Testing Strategy

- **Adjacency Index**: Property test — for any node, forward adjacency lookup returns same edges as full scan filter. Round-trip: build index → query → verify matches linear scan.
- **Cross-Repo Imports**: Unit test with sample Dart files containing cross-repo imports. Verify edges created correctly.
- **Watch Daemon**: Integration test — write a file, verify rebuild triggered after debounce.
- **Repo Coupling**: Unit test with known graph structure, verify matrix counts and cycle detection.
- **TESTED_BY/IMPLEMENTS**: Unit test with naming convention samples (snake_case → PascalCase).
- **Embedding Provider**: Mock-based test for OpenAI/Azure. Property test for local: encode(text).shape == (1, dim).
- **HTTP Transport**: Integration test — start server, connect via SSE client, call a tool.
- **Tool Filter**: Unit test — set env var, verify only listed tools are exposed.
