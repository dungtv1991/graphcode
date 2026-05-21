

// const client = new OpenAI({
//   apiKey: "sk-12a37715e0cc4058a9c64c0305b1da65",
//   baseURL: "https://api.deepseek.com"
// });
const { spawn } = require("child_process");
const fs = require("fs");
const OpenAI = require("openai");

const client = new OpenAI({
  apiKey: "sk-12a37715e0cc4058a9c64c0305b1da65",
  baseURL: "https://api.deepseek.com"
});

// ===== PERSISTENT PYTHON PROCESS =====
let pythonProcess = null;
let pythonReady = false;

function startPythonServer() {
  if (pythonProcess) return;

  pythonProcess = spawn("python3", ["vector_context_manager.py"], {
    stdio: ["pipe", "pipe", "inherit"]
  });

  pythonProcess.stdout.on("data", (data) => {
    const line = data.toString().trim();
    if (line === "READY") {
      pythonReady = true;
      console.log("✅ Python server ready (model cached)");
    }
  });

  pythonProcess.on("exit", () => {
    pythonProcess = null;
    pythonReady = false;
  });
}

function queryPython(query) {
  return new Promise((resolve, reject) => {
    if (!pythonReady) {
      return reject(new Error("Python server not ready"));
    }

    let buffer = "";
    const handler = (data) => {
      buffer += data.toString();
      const lines = buffer.split("\n");
      
      // Giữ lại dòng cuối chưa hoàn chỉnh
      buffer = lines.pop();
      
      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const result = JSON.parse(line);
          pythonProcess.stdout.off("data", handler);
          resolve(result);
        } catch (e) {
          // Chưa phải JSON hoàn chỉnh, đợi thêm
        }
      }
    };

    pythonProcess.stdout.on("data", handler);
    pythonProcess.stdin.write(query + "\n");
  });
}

// ===== INTENT =====
function detectIntent(query) {
  const q = query.toLowerCase();

  if (q.includes("luồng") || q.includes("flow")) return "FLOW";
  if (q.includes("fix") || q.includes("bug") || q.includes("crash")) return "DEBUG";

  return "GENERAL";
}

// ===== LOAD FILE =====
const BLACKLIST_FILES = ["khlc_analytics_screens.dart", "khlc_analytics_events.dart"];

function loadFiles(files) {
  if (!files) return "";

  return files
    .filter(f => !BLACKLIST_FILES.some(b => f.includes(b)))
    .slice(0, 6)  // tối đa 6 files để không quá dài
    .map((file) => {
      try {
        const content = fs.readFileSync(file, "utf-8").slice(0, 2500);
        return `\nFILE: ${file}\n${content}`;
      } catch {
        return `\nFILE: ${file}\n(Cannot read file)`;
      }
    })
    .join("\n");
}

// ===== MAIN =====
async function main() {
  const query = process.argv[2];
  if (!query) return console.log("Missing query");

  console.log("🔍 Query:", query);
  console.log("📂 Selecting context...");

  // ===== CALL PYTHON (persistent server) =====
  startPythonServer();

  // Chờ Python server sẵn sàng (model load lần đầu)
  await new Promise((resolve) => {
    const check = setInterval(() => {
      if (pythonReady) { clearInterval(check); resolve(); }
    }, 100);
  });

  let parsed;
  try {
    parsed = await queryPython(query);
  } catch (e) {
    console.error("Python error:", e.message);
    return;
  }

  const files = parsed.files || [];
  const flow = (parsed.flow || [])
    .filter(f => !BLACKLIST_FILES.some(b => f.includes(b)));
  const graph = parsed.graph || "";

  console.log("✅ Files:", files);
  console.log("🔥 Flow:", flow);

  const codeContext = loadFiles(files);

  // Ưu tiên load: UI Pages trước, rồi Blocs, bỏ qua Modules/Routes
  const priorityFlow = flow.filter(f =>
    f.includes('_page.dart') || f.includes('_screen.dart') || f.includes('_view.dart')
  );
  const blocFlow = flow.filter(f =>
    f.includes('_bloc.dart') || f.includes('_cubit.dart')
  );
  const orderedFlow = [...new Set([...priorityFlow, ...blocFlow, ...flow])];
  const flowContext = loadFiles(orderedFlow);

  const intent = detectIntent(query);

  let systemPrompt = "";

  if (intent === "FLOW") {
    systemPrompt = `
You are a senior Flutter architect.

STRICT RULES — NEVER VIOLATE:
1. ONLY use code that exists in the provided files above. DO NOT invent or assume any code.
2. If a method, class, or endpoint is NOT in the files, say "not found in provided context" — do NOT guess.
3. Quote actual code snippets from the files. Do not write example code.
4. If flow is incomplete due to missing files, explicitly state what is missing.

Explain REAL execution flow based ONLY on the provided files.

Output:
1. Entry UI (which file, which widget)
2. User Action (actual onTap/gesture found in code)
3. Navigation (actual Modular.to.pushNamed or Navigator call found in code)
4. Step-by-step Flow (trace actual class → class from GRAPH CONTEXT)
5. What is NOT available in the provided context (be honest)
`;
  } else if (intent === "DEBUG") {
    systemPrompt = `
You are a senior Flutter engineer.

Find root cause and fix bug.

Output:
Root Cause
Fix
Code Diff
`;
  } else {
    systemPrompt = `Explain clearly.`;
  }

  const prompt = `
USER QUERY:
${query}

=== FLOW FILES (GROUND TRUTH) ===
${flowContext}

${graph}

=== RELATED FILES ===
${codeContext}

${systemPrompt}
`;

  console.log("🤖 Calling AI...");

  try {
    const res = await client.chat.completions.create({
      model: "deepseek-chat",
      messages: [{ role: "user", content: prompt }],
      temperature: 0.2
    });

    console.log("\n🧠 RESULT:\n");
    console.log(res.choices[0].message.content);
  } catch (e) {
    console.error("AI error:", e.message);
  }

  // Cleanup Python server
  if (pythonProcess) pythonProcess.kill();
}

main();