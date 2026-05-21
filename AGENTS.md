# Codex Rules For KHLC Mobile

---

## Ngôn ngữ & Phong cách trả lời

- **Luôn trả lời bằng tiếng Việt.** Code, tên class, tên file giữ nguyên tiếng Anh.
- **Chỉ trả lời đúng trọng tâm yêu cầu.** Không giải thích thừa, không tóm tắt lại những gì vừa làm, không liệt kê các bước sắp thực hiện trước khi thực hiện.
- **Ngắn gọn tối đa.** Nếu kết quả là code → trả code. Nếu kết quả là câu trả lời → trả lời thẳng. Không thêm lời dẫn, không thêm lời kết.
- **Chất lượng thực thi không giảm.** Ngắn gọn áp dụng cho giao tiếp, không áp dụng cho code hay phân tích kỹ thuật.

---

## Nguyên tắc cốt lõi

Mỗi session chỉ làm 1 việc = 1 change cluster có thể verify được. Kết thúc ngay khi xong.
`spec.md` là bộ nhớ dùng chung giữa các session — không phải conversation history.
Conversation càng dài càng tốn token và càng giảm độ chính xác.

---

## Vòng đời 1 task = 4–5 session

### SESSION 1 — PLAN
1. `git pull` (ci với khlc-mobile, main với repo khác — trừ khi user yêu cầu branch cụ thể thì checkout branch đó)
2. `jira_get_issue(TICKET_ID)` → extract: AC, business rules, API endpoints
3. `get_confluence_page()` nếu có link → extract: rules, data model
4. Query code bằng flutter-context theo thứ tự:
   - `grep_in_files` / `search_by_filename` nếu biết tên class/file
   - `query_context(top_k=3, snippet_chars=300)` nếu chỉ biết feature
   - `get_file_content(path, class_name="X")` cho tối đa 2 file
   - `get_blast_radius("X")` nếu sửa class dùng chung
5. Ghi toàn bộ kết quả vào `.kiro/specs/TICKET-ID/spec.md`

**→ Kết thúc session. Nhắc user:**
> ✅ SESSION 1 xong — spec tại `.kiro/specs/TICKET-ID/spec.md`
> 👉 Mở session mới, nhắn: `"TICKET-ID SESSION 1.5"` (có UI) hoặc `"TICKET-ID SESSION 2"` (không UI)

---

### SESSION 1.5 — DESIGN *(chỉ khi task có UI, Figma MCP đang bật)*
1. Đọc `spec.md`
2. User chọn node trong Figma
3. `get_selection()` → `get_design_context(level="compact")` nếu cần thêm
4. Bổ sung vào `spec.md` phần `## Design`: layout, spacing, màu, typography, component mapping

**→ Kết thúc session. Nhắc user:**
> ✅ SESSION 1.5 xong — design đã ghi vào spec.md
> 👉 Mở session mới, nhắn: `"TICKET-ID SESSION 2"`

---

### SESSION 2..N — IMPLEMENT *(1 change cluster / session)*
1. Đọc `spec.md`
2. Đọc steering file theo routing table bên dưới
3. `get_file_content(path, class_name="X")` cho file chuẩn bị sửa
4. Implement đúng change cluster trong spec
5. `getDiagnostics` → sửa lỗi
6. Đánh dấu `[x]` file/session đã xong trong `spec.md`
7. Ghi `## Session Notes`: files thực tế đã sửa, tóm tắt thay đổi, verify đã chạy/chưa chạy

**Session sizing**
- Được gom nhiều file nếu cùng 1 flow, pattern đã rõ, blast radius thấp, đọc không quá 3 file hoặc 1 cụm BLoC.
- Không gom nếu task UI chưa qua SESSION 1.5, cần đọc nhiều context mới, chạm shared/core/cross-repo, API/model ảnh hưởng rộng, hoặc bắt đầu có nhiều assumption.

**→ Kết thúc session. Nhắc user:**
> ✅ SESSION N xong — [change cluster] đã implement
> 📋 Còn lại: [các file chưa [x] trong spec]
> 👉 Mở session mới, nhắn: `"TICKET-ID SESSION N+1"` hoặc `"TICKET-ID VERIFY"` nếu xong hết

---

### SESSION N+1 — VERIFY
1. Đọc `spec.md` → kiểm tra progress `[x]` hết chưa
2. Nếu có Model mới: `dart run build_runner build --delete-conflicting-outputs`
3. Nếu có i18n mới: `dart run slang`
4. `flutter analyze` → sửa hết warning/error
5. Kiểm tra `git diff` chỉ gồm file đã liệt kê trong `spec.md`; nếu có file ngoài spec → cập nhật spec trước khi tiếp tục
6. Ghi kết quả verify vào `spec.md`

**→ Kết thúc session. Nhắc user:**
> ✅ SESSION VERIFY xong — analyze [passed / fixed N warnings]
> 👉 Mở session mới, nhắn: `"TICKET-ID SHIP"`

---

### SESSION CUỐI — SHIP
1. Đọc `spec.md`
2. `git checkout -b feat/TICKET-ID`
3. `git add` đúng các file trong spec — không dùng `git add -A`
4. `git commit -m "feat(TICKET-ID): mô tả ngắn"`
5. `git push -u origin feat/TICKET-ID`
6. Jira: comment + transition → `Build` + label `AI-Native`
7. Ghi branch/commit/Jira status vào `## Session Notes`; chưa xoá/archive task context ở SHIP

**→ Kết thúc session. Nhắc user:**
> ✅ TICKET-ID hoàn thành
> 🌿 Branch: `feat/TICKET-ID` đã push
> 🎫 Jira: đã chuyển sang Build + label AI-Native

---

## Template spec.md

```markdown
# TICKET-ID — [summary]

## Yêu cầu
- [AC 1]
- [AC 2]

## Business Rules
- [từ Confluence]

## Design *(bỏ qua nếu không có UI)*
- Layout / Spacing / Colors / Typography
- Components: [Figma] → [KHLC widget]

## Files cần sửa
- [ ] `path/file.dart` — class `X` — [thay đổi cụ thể]
- [ ] `path/file2.dart` — class `Y` — [thay đổi cụ thể]

## Dependencies
- [ClassA phụ thuộc ClassB → sửa B trước]
- Blast radius: [kết quả nếu có]

## Codegen
- [ ] build_runner
- [ ] slang

## Progress
- [ ] SESSION 2: [change cluster 1]
- [ ] SESSION 3: [change cluster 2]
- [ ] SESSION VERIFY
- [ ] SESSION SHIP

## Session Notes
- SESSION 2:
  - Changed: `path/file.dart`
  - Summary: [thay đổi thực tế]
  - Verify: not run / passed / failed: [lý do]
- SESSION VERIFY:
  - Result: [analyze/codegen result]
- SESSION SHIP:
  - Branch: `feat/TICKET-ID`
  - Commit: [hash]
  - Jira: [status/comment]
```

---

## Routing — Chỉ đọc steering file liên quan

| Loại task | Từ khóa | Steering file |
|-----------|---------|---------------|
| UI / màn hình | screen, view, widget, Figma | `ui_ux_standards.md`, `screen_business_logic.md` |
| Feature / UseCase | implement, tạo mới, UseCase | `architecture_standards.md`, `usecase_registry.md` |
| Data / Model / API | model, entity, API, response | `data_model_mapping.md`, `data_model_journey.md` |
| Cross-repo / core | khlc_core, shared, ảnh hưởng | `inter_module_dependency_map.md` |
| Shell / navigation | deep link, routing, notification | `module_detailed_functions.md` |

Steering files nằm tại `.kiro/steering/` trong repo `khlc-mobile`.

---

## Code Standards

- **Sizing**: `.sc()` cho mọi kích thước số cứng
- **Spacing**: `KHLCSpacing` — không dùng `SizedBox`/`EdgeInsets` trực tiếp
- **Colors**: `AliasColor` / `NeutralColor` / `PrimaryColor` — không hardcode hex
- **Typography**: `AppStyle` (Body2.medium, Caption1.bold…)
- **Entity**: extends `Equatable`, constructor `const`, fields `final`
- **Model**: extends Entity, `@JsonSerializable(createToJson: false)`
- **UseCase**: inject qua `Modular.get<T>()` — không gọi Repository từ UI
- **BLoC**: tách 3 file (bloc, event, state) trong folder `bloc/`
- **khlc_core first**: tìm xem đã có sẵn trong core chưa trước khi tạo mới

---

## flutter-context — Tool priority

```
grep_in_files("ClassName")            ← dùng trước
search_by_filename("feature_name")
query_context(query, top_k=3)
get_file_content(path, class_name=X)  ← chỉ khi cần
```

Giới hạn: `top_k` ≤ 3 · đọc ≤ 2 file · luôn dùng `class_name` param

---

## Implementation Rules

- Chỉ sửa file đã liệt kê trong spec. Nếu cần thêm file → cập nhật spec trước.
- Không tạo mới utility/widget/dependency nếu đã có trong `khlc_core`.
- Không sửa generated files (`.g.dart`, `.freezed.dart`) trừ khi spec yêu cầu.
- Không chạy destructive git commands khi chưa có user approval.
