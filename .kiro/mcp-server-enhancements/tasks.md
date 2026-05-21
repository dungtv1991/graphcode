# Implementation Tasks

## Task 1: Adjacency Index for Graph Traversal

- [x] 1.1 Add `_build_adjacency_index()` function in `mcp_server.py` that builds `_State.adj_forward` and `_State.adj_reverse` dictionaries from `_State.edges`
- [x] 1.2 Call `_build_adjacency_index()` at the end of `_init()` after edges are loaded
- [x] 1.3 Refactor `_trace_flow()` to use `_State.adj_forward.get(node, [])` instead of iterating all edges
- [x] 1.4 Refactor `get_blast_radius()` reverse DFS to use `_State.adj_reverse.get(node, [])` instead of iterating all edges
- [x] 1.5 Refactor `_graph_info()` to use adjacency lookups for the given node set instead of full edge scan
- [x] 1.6 Call `_build_adjacency_index()` at the end of `build_db()` after reloading the graph
- [x] 1.7 Update `vector_context_manager.py` `trace_flow` method to use adjacency index pattern for consistency

## Task 2: Cross-Repo Import Resolution

- [x] 2.1 Add `_build_package_repo_map(root_dir)` function in `extract_graph.py` that reads `pubspec.yaml` from each khlc-* repo and returns `{package_name: repo_name}` mapping
- [x] 2.2 Add `_RE_IMPORT` regex pattern to match `import 'package:<name>/<path>'` statements
- [x] 2.3 Add `_resolve_import_to_class(pkg, path, package_repo_map, file_mapping)` function that maps an import path to a known class node
- [x] 2.4 Integrate import parsing into `parse_dart_file_ts()` — after existing edge extraction, create `imports_from` edges for cross-repo imports
- [x] 2.5 Integrate import parsing into `parse_dart_file_regex()` fallback parser
- [x] 2.6 Pass `package_repo_map` from `FlutterModularMultiRepoParser` to each `parse_dart_file()` call
- [x] 2.7 Add `imports_from` to the edge types used in `_trace_flow()` and adjacency index

## Task 3: Watch Daemon

- [x] 3.1 Create `watch_daemon.py` with `DartFileHandler` class extending `watchdog.events.FileSystemEventHandler`
- [x] 3.2 Implement debounce logic (3 second timer reset on each new event) in `DartFileHandler`
- [x] 3.3 Implement `start_watcher(root_dir, rebuild_callback)` function that sets up Observer for all khlc-*/lib/ directories
- [x] 3.4 Extract incremental rebuild logic from `build_db()` into a reusable `_incremental_rebuild(changed_files)` function in `mcp_server.py`
- [x] 3.5 Add watcher startup in `mcp_server.py` — check `FLUTTER_CONTEXT_WATCH` env var and start watcher as background task if enabled
- [x] 3.6 Add `watchdog` to `requirements.txt`
- [x] 3.7 Add error handling in rebuild callback — log errors and continue

## Task 4: Repo Coupling Tool

- [x] 4.1 Add `_detect_cycles(repo_graph)` helper function implementing DFS-based cycle detection on directed graph
- [x] 4.2 Implement `get_repo_coupling()` MCP tool that builds dependency matrix from cross-repo edges
- [x] 4.3 Include cycle detection results and summary statistics in the tool output
- [x] 4.4 Handle edge case: return descriptive message when no cross-repo edges exist

## Task 5: TESTED_BY and IMPLEMENTS Edges

- [x] 5.1 Add `_match_test_to_source(test_filename, known_nodes)` function that converts snake_case test filename to PascalCase class name
- [x] 5.2 Add test directory scanning in `FlutterModularMultiRepoParser.scan_all_repos()` — walk `test/` dirs and create `tested_by` edges
- [x] 5.3 Add `_ts_get_implements(node)` function to extract interface names from `implements` clause in tree-sitter AST
- [x] 5.4 Integrate `implements` edge creation into `parse_dart_file_ts()` class declaration loop
- [x] 5.5 Add `tested_by` and `implements` to adjacency index edge types

## Task 6: Configurable Embedding Provider

- [x] 6.1 Create `embedding_provider.py` with `EmbeddingProvider` base class defining `encode()` and `dimension` interface
- [x] 6.2 Implement `LocalProvider` class wrapping SentenceTransformer
- [x] 6.3 Implement `OpenAIProvider` class using openai Python SDK
- [x] 6.4 Implement `AzureProvider` class using azure openai endpoint
- [x] 6.5 Implement `create_provider()` factory function reading env vars with fallback logic
- [x] 6.6 Replace `_State.model = SentenceTransformer(MODEL_NAME)` in `mcp_server.py` with `_State.model = create_provider()`
- [x] 6.7 Update `build_db()` to detect dimension mismatch and force full rebuild when provider changes
- [x] 6.8 Update `_vector_search()` to use `_State.model.encode()` interface

## Task 7: HTTP Transport Mode

- [x] 7.1 Add transport selection logic at the bottom of `mcp_server.py` — read `FLUTTER_CONTEXT_TRANSPORT` env var
- [x] 7.2 Implement HTTP/SSE startup path using `mcp.run(transport="sse", ...)` with configurable port from `FLUTTER_CONTEXT_PORT`
- [x] 7.3 Add port-in-use error handling — catch OSError and exit with descriptive message
- [x] 7.4 Ensure `_init()` is called before server starts in both transport modes

## Task 8: Tool Filtering

- [x] 8.1 Implement `_apply_tool_filter()` function that reads `FLUTTER_CONTEXT_TOOLS` env var and removes unlisted tools from FastMCP registry
- [x] 8.2 Add warning log for tool names in filter that don't match any registered tool
- [x] 8.3 Call `_apply_tool_filter()` after all tool registrations but before `mcp.run()`
- [x] 8.4 Ensure watch daemon internal rebuild is not affected by tool filter (build_db logic remains callable internally)
