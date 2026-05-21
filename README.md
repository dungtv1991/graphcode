# 🧠 Flutter Agent Knowledge Base
> Knowledge Graph + Semantic Search cho hệ thống Agent KHLC

✅ Đây là cốt lõi 90% sức mạnh của Agent. Phần còn lại chỉ là prompt.

---

## 📦 Hiện trạng hệ thống
| Chỉ số | Giá trị |
|---|---|
| Tổng Repositories được index | 20 |
| Tổng Nodes trong Graph | 1171 |
| Tổng Edges phụ thuộc | 723 |
| Số file được vectorized | 1171 |
| Kích thước Vector DB | 1.8 MB |
| Ngôn ngữ search | Tiếng Việt + Tiếng Anh |

---

## 🚀 Cách sử dụng

### 1. Index toàn bộ dự án
```bash
# Step 1: Parse AST & build Knowledge Graph
python3 extract_graph.py

# Step 2: Build Semantic Vector Database
python3 vector_context_manager.py build
```

### 2. Lấy context cho query bất kỳ
```python
from vector_context_manager import SmartContextSelector

selector = SmartContextSelector()

# ✅ Hàm duy nhất bạn cần dùng
prompt_context, files = selector.build_prompt_context(
    "Fix lỗi crash khi đăng nhập",
    top_k=4
)

# Feed thẳng vào Kiro / LLM
print(prompt_context)
```

### 3. Output chuẩn nhận được
```
USER QUERY: Fix lỗi crash khi đăng nhập

=== RELEVANT FILES ===
  [1] LoginController -> khlc-authentication/lib/login_controller.dart (score:0.789)
  [2] AuthService -> khlc-authentication/lib/auth_service.dart (score:0.742)
  [3] UserRepository -> khlc-core/lib/user_repository.dart (score:0.681)

=== GRAPH CONTEXT ===
  LoginController --[depends_on]--> AuthService
  AuthService --[depends_on]--> UserRepository
  AuthModule --[binds]--> LoginController
```

---

## 🔄 Cập nhật khi code thay đổi
Khi bạn `git pull` code mới:
```bash
# Chạy lại 2 lệnh là xong (không cần restart gì)
python3 extract_graph.py
python3 vector_context_manager.py build
```

⏱️ Tổng thời gian cập nhật: ~10 giây

---

## 📐 Kiến trúc Hybrid Search
```
User Query
    ↓
┌───────────────────────────┐
│ Semantic Vector Search    │  → tìm các file liên quan theo ý nghĩa
└───────────────────────────┘
    ↓
┌───────────────────────────┐
│ Knowledge Graph Expand    │  → kéo theo tất cả dependencies liên quan
└───────────────────────────┘
    ↓
┌───────────────────────────┐
│ Graph Relation Render     │  → tạo sơ đồ luồng cho LLM hiểu
└───────────────────────────┘
    ↓
Prompt Context (feed vào Kiro)
```

---

## ✅ Ưu điểm của kiến trúc này
1.  **Không đoán mò file**: 100% chính xác đường dẫn file thật
2.  **Không bỏ sót dependency**: tự động kéo theo service, repository liên quan
3.  **Hiểu tiếng Việt**: không cần dịch query sang tiếng Anh
4.  **Không có state lỗi**: toàn bộ dữ liệu được rebuild từ gốc mỗi lần index
5.  **Không cần setup DB**: chạy được ngay trên bất kỳ máy nào
6.  **Nhanh**: query trả về kết quả trong <100ms

---

## 📁 Các file chính
| File | Chức năng |
|---|---|
| `extract_graph.py` | Parser Flutter Modular, extract Knowledge Graph |
| `vector_context_manager.py` | Semantic Search + Context Selection |
| `knowledge_graph.json` | Full graph nodes + edges + file mapping |
| `vector_db.pkl` | Embedding vectors cho tất cả file |

---

## ⚠️ Quy tắc vàng
> 🔴 **KHÔNG BAO GIỜ BỎ QUA BƯỚC NÀY**
>
> 90% sức mạnh của Agent nằm ở context selection đúng, không phải ở prompt, không phải ở LLM.
>
> Nếu bạn skip bước này → Agent sẽ đoán file, bỏ sót dependency, fix sai chỗ và gây lỗi.

---

## 🚀 Kế tiếp
Sau khi phần này ổn, bạn chỉ cần:
1.  Đặt `build_prompt_context()` vào trước phần gọi Kiro
2.  Thêm instruction vào prompt: "Chỉ được sửa các file được liệt kê bên trên"
3.  Xong.