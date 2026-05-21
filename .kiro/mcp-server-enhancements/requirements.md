# Requirements Document

## Introduction

This feature enhances the flutter-context MCP server with performance optimizations, cross-repo intelligence, automated maintenance, and deployment flexibility. The enhancements target the three core files (`mcp_server.py`, `extract_graph.py`, `vector_context_manager.py`) to improve graph traversal speed, cross-repo dependency visibility, freshness of the knowledge graph, and team-wide accessibility.

## Glossary

- **MCP_Server**: The FastMCP-based Python server exposing tools for Flutter code intelligence (query_context, get_blast_radius, build_db, etc.)
- **Knowledge_Graph**: The JSON graph structure containing nodes (Dart classes), edges (dependencies), and file_mapping produced by the graph extractor
- **Graph_Extractor**: The module (`extract_graph.py`) that parses Dart files using Tree-sitter and produces the Knowledge_Graph
- **Vector_DB**: The pickle-serialized database containing sentence embeddings and metadata for semantic search
- **Adjacency_Index**: An in-memory dictionary mapping each node to its outgoing and incoming neighbor lists, built at initialization time
- **Watch_Daemon**: A filesystem watcher process that monitors `.dart` file changes and triggers incremental graph/vector rebuilds
- **Embedding_Provider**: A configurable component responsible for generating text embeddings (default: local SentenceTransformer, optional: OpenAI/Azure)
- **Repo_Coupling_Matrix**: A data structure showing dependency counts between repos and detecting circular dependency chains
- **Tool_Filter**: An environment-variable-based mechanism to control which MCP tools are exposed to clients

## Requirements

### Requirement 1: Adjacency Index for Graph Traversal

**User Story:** As a developer using the MCP server, I want graph traversal operations (trace_flow, get_blast_radius) to execute in O(neighbors) time instead of O(all_edges), so that responses are fast even as the knowledge graph grows.

#### Acceptance Criteria

1. WHEN the MCP_Server initializes, THE Adjacency_Index SHALL build forward adjacency lists (node → list of outgoing edges) and reverse adjacency lists (node → list of incoming edges) from all edges in the Knowledge_Graph
2. WHEN trace_flow is called, THE MCP_Server SHALL traverse using the forward Adjacency_Index instead of scanning all edges on each DFS step
3. WHEN get_blast_radius is called, THE MCP_Server SHALL traverse using the reverse Adjacency_Index instead of scanning all edges on each reverse-DFS step
4. WHEN the Knowledge_Graph is reloaded after a build_db call, THE Adjacency_Index SHALL be rebuilt from the updated edges
5. THE Adjacency_Index SHALL support all edge types currently used in traversal: routes_to, depends_on, binds, has_part, and imports_from

### Requirement 2: Cross-Repo Import Resolution

**User Story:** As a developer working across multiple Flutter repos, I want the graph extractor to parse Dart import statements and create `imports_from` edges between repos, so that I can see cross-repo dependencies in the knowledge graph.

#### Acceptance Criteria

1. WHEN the Graph_Extractor parses a Dart file, THE Graph_Extractor SHALL extract all import statements matching the pattern `import 'package:<package_name>/...'`
2. WHEN an import references a package belonging to another khlc-* repo, THE Graph_Extractor SHALL create an edge of type `imports_from` from the importing class to the imported class
3. WHEN the imported class cannot be resolved to a known node, THE Graph_Extractor SHALL skip that import without producing an error
4. THE Graph_Extractor SHALL maintain a package-to-repo mapping by reading `pubspec.yaml` files from each khlc-* repo at scan time
5. WHEN a Dart file imports from the same repo, THE Graph_Extractor SHALL NOT create an `imports_from` edge (intra-repo imports are already captured by depends_on edges)

### Requirement 3: Watch Daemon for Auto-Rebuild

**User Story:** As a developer, I want the vector DB and knowledge graph to stay fresh automatically when I edit Dart files, so that I do not need to manually call build_db after every code change.

#### Acceptance Criteria

1. WHEN the Watch_Daemon is started, THE Watch_Daemon SHALL monitor all `lib/` directories under khlc-* repos for `.dart` file changes (create, modify, delete)
2. WHEN a `.dart` file change is detected, THE Watch_Daemon SHALL debounce changes for 3 seconds before triggering a rebuild
3. WHEN the debounce period expires, THE Watch_Daemon SHALL perform an incremental rebuild of the Knowledge_Graph and Vector_DB for only the changed files
4. IF the Watch_Daemon encounters a file read error during rebuild, THEN THE Watch_Daemon SHALL log the error and continue processing remaining files
5. WHEN the MCP_Server starts with the environment variable `FLUTTER_CONTEXT_WATCH=1`, THE Watch_Daemon SHALL start automatically as a background task
6. WHEN the MCP_Server starts without the environment variable or with `FLUTTER_CONTEXT_WATCH=0`, THE Watch_Daemon SHALL NOT start

### Requirement 4: Repo Coupling Tool

**User Story:** As a tech lead, I want to see a dependency matrix between repos and detect circular dependencies, so that I can manage coupling and plan refactoring.

#### Acceptance Criteria

1. WHEN get_repo_coupling is called, THE MCP_Server SHALL compute a dependency matrix showing the count of edges from each repo to every other repo
2. WHEN computing the dependency matrix, THE MCP_Server SHALL include edges of types: depends_on, imports_from, binds, and routes_to
3. WHEN the dependency matrix is computed, THE MCP_Server SHALL detect circular dependency chains (repo A → repo B → repo A) and report them
4. THE MCP_Server SHALL return the coupling matrix as a JSON object containing: the matrix (repo pairs with edge counts), a list of circular dependency chains, and a summary with total cross-repo edge count
5. WHEN no cross-repo edges exist, THE MCP_Server SHALL return an empty matrix with a descriptive message

### Requirement 5: TESTED_BY and IMPLEMENTS Edges

**User Story:** As a developer, I want the knowledge graph to show which test files test which classes, and which classes implement which interfaces, so that I can navigate between tests and implementations easily.

#### Acceptance Criteria

1. WHEN the Graph_Extractor encounters a file in a `test/` directory, THE Graph_Extractor SHALL attempt to match it to a source class by naming convention (e.g., `cart_bloc_test.dart` → `CartBloc`)
2. WHEN a test-to-source match is found, THE Graph_Extractor SHALL create an edge of type `tested_by` from the source class node to the test file node
3. WHEN the Graph_Extractor parses a class declaration with an `implements` clause, THE Graph_Extractor SHALL create an edge of type `implements` from the implementing class to the interface class
4. IF a test file name does not match any known source class, THEN THE Graph_Extractor SHALL skip that file without producing an error
5. THE MCP_Server SHALL include `tested_by` and `implements` edge types in the Adjacency_Index for traversal operations

### Requirement 6: Configurable Embedding Provider

**User Story:** As a team deploying the MCP server in different environments, I want to configure the embedding provider (local SentenceTransformer, OpenAI, or Azure), so that I can choose between speed, quality, and cost.

#### Acceptance Criteria

1. THE MCP_Server SHALL read the embedding provider configuration from the environment variable `FLUTTER_CONTEXT_EMBEDDING_PROVIDER` with valid values: `local` (default), `openai`, `azure`
2. WHEN the provider is set to `local`, THE Embedding_Provider SHALL use SentenceTransformer with the model specified in `FLUTTER_CONTEXT_EMBEDDING_MODEL` (default: `paraphrase-multilingual-MiniLM-L12-v2`)
3. WHEN the provider is set to `openai`, THE Embedding_Provider SHALL use the OpenAI embeddings API with the model specified in `FLUTTER_CONTEXT_EMBEDDING_MODEL` (default: `text-embedding-3-small`) and the API key from `OPENAI_API_KEY`
4. WHEN the provider is set to `azure`, THE Embedding_Provider SHALL use the Azure OpenAI embeddings API with endpoint from `AZURE_OPENAI_ENDPOINT`, API key from `AZURE_OPENAI_KEY`, and deployment name from `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`
5. IF the configured provider fails to initialize, THEN THE Embedding_Provider SHALL fall back to the local SentenceTransformer provider and log a warning
6. WHEN the embedding provider changes, THE MCP_Server SHALL require a full rebuild of the Vector_DB (incremental rebuild is not compatible across different embedding dimensions)

### Requirement 7: HTTP Transport Mode

**User Story:** As a team, I want to run the MCP server in HTTP mode so that multiple developers can share a single server instance instead of each running their own.

#### Acceptance Criteria

1. WHEN the environment variable `FLUTTER_CONTEXT_TRANSPORT` is set to `http`, THE MCP_Server SHALL start an HTTP server on the port specified by `FLUTTER_CONTEXT_PORT` (default: 8765)
2. WHEN the environment variable `FLUTTER_CONTEXT_TRANSPORT` is not set or set to `stdio`, THE MCP_Server SHALL use the standard stdio transport (current behavior)
3. WHEN running in HTTP mode, THE MCP_Server SHALL expose the same MCP protocol over HTTP using the SSE (Server-Sent Events) transport defined by the MCP specification
4. WHEN running in HTTP mode, THE MCP_Server SHALL support multiple concurrent client connections
5. IF the specified port is already in use, THEN THE MCP_Server SHALL log an error message including the port number and exit with a non-zero status code

### Requirement 8: Tool Filtering

**User Story:** As a server administrator, I want to limit which MCP tools are exposed to clients via an environment variable, so that I can restrict access to sensitive or expensive operations.

#### Acceptance Criteria

1. WHEN the environment variable `FLUTTER_CONTEXT_TOOLS` is set, THE MCP_Server SHALL expose only the tools whose names are listed in the comma-separated value (e.g., `query_context,get_file_content,search_by_filename`)
2. WHEN the environment variable `FLUTTER_CONTEXT_TOOLS` is not set, THE MCP_Server SHALL expose all available tools (current behavior)
3. WHEN a tool name in the filter list does not match any registered tool, THE MCP_Server SHALL log a warning and ignore that entry
4. THE MCP_Server SHALL apply the tool filter at startup before the server begins accepting connections
5. WHEN the tool filter excludes build_db, THE Watch_Daemon SHALL still function internally (the filter only affects client-facing tool exposure)
