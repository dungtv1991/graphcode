const fs = require("fs");
const path = require("path");
const Parser = require("tree-sitter");

// ⚠️ QUAN TRỌNG: phải .dart
const Dart = require("tree-sitter-dart");

const parser = new Parser();
parser.setLanguage(Dart);

// 👉 ĐỔI PATH NÀY thành project Flutter của bạn
const projectPath = "../khlc-mobile/lib";

// ===== DATA =====
let graph = {
  nodes: [],
  edges: []
};

let fileMap = {};

// để tránh trùng node
const nodeSet = new Set();

// ===== SCAN DIR =====
function scanDir(dir) {
  if (!fs.existsSync(dir)) {
    console.error("❌ Path không tồn tại:", dir);
    return;
  }

  const files = fs.readdirSync(dir);

  files.forEach(file => {
    const fullPath = path.join(dir, file);

    if (fs.statSync(fullPath).isDirectory()) {
      scanDir(fullPath);
    } else if (file.endsWith(".dart")) {
      processFile(fullPath);
    }
  });
}

// ===== PROCESS FILE =====
function processFile(filePath) {
  try {
    const code = fs.readFileSync(filePath, "utf8");
    const tree = parser.parse(code);

    const root = tree.rootNode;

    root.namedChildren.forEach(node => {
      if (node.type === "class_declaration") {
        const nameNode = node.childForFieldName("name");
        if (!nameNode) return;

        const className = nameNode.text;
        const type = detectType(className, node);

        if (type) {
          addNode(className, type, filePath);
        }

        detectDependencies(node, className);
      }
    });
  } catch (err) {
    console.error("⚠️ Lỗi file:", filePath);
    console.error(err.message);
  }
}

// ===== ADD NODE =====
function addNode(name, type, filePath) {
  if (nodeSet.has(name)) return;

  nodeSet.add(name);

  graph.nodes.push({
    id: name,
    type
  });

  fileMap[name] = filePath;
}

// ===== DETECT TYPE =====
function detectType(name, node) {
  // 1. theo tên
  if (name.endsWith("Module")) return "Module";
  if (name.endsWith("Controller")) return "Controller";
  if (name.endsWith("Service")) return "Service";
  if (name.endsWith("Repository")) return "Repository";

  // 2. theo extends (Flutter Modular)
  const extendsNode = node.childForFieldName("superclass");

  if (extendsNode) {
    const text = extendsNode.text;

    if (text.includes("Module")) return "Module";
  }

  return null;
}

// ===== DETECT DEPENDENCIES =====
function detectDependencies(node, className) {
  const constructors = node.descendantsOfType("constructor_declaration");

  constructors.forEach(cons => {
    const params = cons.descendantsOfType("formal_parameter");

    params.forEach(param => {
      const typeNode = param.childForFieldName("type");

      if (typeNode) {
        let dep = typeNode.text;

        // normalize (remove ?)
        dep = dep.replace("?", "");

        graph.edges.push({
          from: className,
          to: dep,
          type: "depends_on"
        });
      }
    });
  });
}

// ===== RUN =====
console.log("🚀 Scanning project...");
scanDir(projectPath);

// ===== SAVE =====
fs.writeFileSync(
  "knowledge_graph.json",
  JSON.stringify(graph, null, 2)
);

fs.writeFileSync(
  "file_map.json",
  JSON.stringify(fileMap, null, 2)
);

console.log("✅ DONE!");
console.log("📁 knowledge_graph.json created");
console.log("📁 file_map.json created");