# KHLC Mobile — Workflow Rules

## Ngôn ngữ & Phong cách
- Luôn trả lời bằng tiếng Việt. Code, tên class, tên file giữ nguyên tiếng Anh.
- Chỉ trả lời đúng trọng tâm yêu cầu. Không giải thích thừa, không tóm tắt lại những gì vừa làm.
- Ngắn gọn tối đa. Chất lượng thực thi không giảm.

---

## Nguyên tắc cốt lõi
- Mỗi session chỉ làm 1 việc. Kết thúc ngay khi xong.
- `spec.md` tại `.kiro/specs/TICKET-ID/spec.md` là bộ nhớ dùng chung giữa các session.

---

## Routing — Chỉ đọc steering file liên quan

| Task | Từ khóa | Steering file |
|------|---------|---------------|
| UI | screen, view, widget, Figma | `ui_ux_standards.md`, `screen_business_logic.md` |
| Feature | implement, UseCase, business logic | `architecture_standards.md`, `usecase_registry.md` |
| Data/API | model, entity, API, response | `data_model_mapping.md`, `data_model_journey.md` |
| Core | khlc_core, shared, cross-module | `inter_module_dependency_map.md` |
| Navigation | deep link, routing, notification | `module_detailed_functions.md` |
| Git | push, branch, commit | `git-push-rules.md` |
| Jira | comment, transition, update | `jira-update-workflow.md` |

---

## Vòng đời 1 task

### SESSION 1 — PLAN
1. `git pull`
2. `jira_get_issue(TICKET_ID)` → extract: AC, business rules, API
3. `get_confluence_page()` nếu có link
4. flutter-context theo tool priority
5. `get_blast_radius()` nếu sửa class dùng chung
6. `get_selection()` nếu có UI (Figma MCP bật)
7. Ghi vào `.kiro/specs/TICKET-ID/spec.md`

> ✅ SESSION 1 xong · 👉 Session mới: `"TICKET-ID SESSION 1.5"` (có UI) hoặc `"TICKET-ID SESSION 2"`

### SESSION 1.5 — DESIGN *(chỉ khi có UI)*
1. Đọc spec.md
2. `get_selection()` → `get_design_context(level="compact")`
3. Ghi vào spec.md phần `## Design`

> ✅ SESSION 1.5 xong · 👉 Session mới: `"TICKET-ID SESSION 2"`

### SESSION 2..N — IMPLEMENT *(1 file/session)*
1. Đọc spec.md → routing table → đọc steering file liên quan
2. `get_file_content(path, class_name="X")`
3. Implement → `getDiagnostics` → sửa lỗi
4. Đánh dấu `[x]` trong spec.md

> ✅ SESSION N xong · 📋 Còn: [file chưa x] · 👉 Session mới: `"TICKET-ID SESSION N+1"` hoặc `"TICKET-ID VERIFY"`

### SESSION VERIFY
1. Đọc spec.md → kiểm tra `[x]` hết chưa
2. `dart run build_runner build --delete-conflicting-outputs` nếu có Model mới
3. `dart run slang` nếu có i18n mới
4. `flutter analyze` → sửa hết warning/error

> ✅ VERIFY xong · 👉 Session mới: `"TICKET-ID SHIP"`

### SESSION SHIP
1. `git checkout -b feat/TICKET-ID`
2. `git add` đúng file trong spec
3. `git commit -m "feat(TICKET-ID): mô tả ngắn"`
4. `git push -u origin feat/TICKET-ID`
5. Jira: comment + transition → Build + label `AI-Native`

> ✅ TICKET-ID hoàn thành · 🌿 Branch pushed · 🎫 Jira updated

---

## flutter-context — Tool priority

```
grep_in_files("ClassName")           ← dùng trước
search_by_filename("feature_name")
query_context(query, top_k=3)
get_file_content(path, class_name=X) ← luôn dùng class_name
```

`top_k` ≤ 3 · đọc ≤ 2 file · **bắt buộc** dùng `class_name` param

---

## Code Standards

- **Sizing**: `.sc()` cho mọi kích thước số cứng
- **Spacing**: `KHLCSpacing` — không dùng `SizedBox`/`EdgeInsets` trực tiếp
- **Colors**: `AliasColor` / `NeutralColor` / `PrimaryColor` — không hardcode hex
- **Typography**: `AppStyle` (Body2.medium, Caption1.bold…)
- **Entity**: extends `Equatable`, constructor `const`, fields `final`
- **Model**: extends Entity, `@JsonSerializable(createToJson: false)`
- **UseCase**: inject qua `Modular.get<T>()` — không gọi Repository từ UI
- **BLoC**: tách 3 file riêng (bloc, event, state) trong folder `bloc/`
- **khlc_core first**: tìm xem đã có sẵn trong core trước khi tạo mới

---

## spec.md template

```markdown
# TICKET-ID — [summary]

## Yêu cầu
- [AC]

## Business Rules
- [từ Confluence]

## Files cần sửa
- [ ] `path/file.dart` — class `X` — [thay đổi]

## Design *(bỏ nếu không có UI)*
- Layout / Spacing / Colors / Typography / Components

## Dependencies
- Blast radius: [nếu có]

## Codegen
- [ ] build_runner · [ ] slang

## Progress
- [ ] SESSION 2: file.dart
- [ ] SESSION VERIFY
- [ ] SESSION SHIP
```
