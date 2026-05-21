---
inclusion: manual
---

# Session Lifecycle

## SESSION 1 — PLAN
1. `git pull`
2. `jira_get_issue(TICKET_ID)` → AC, business rules, API
3. `get_confluence_page()` nếu có link
4. flutter-context theo tool priority
5. `get_blast_radius()` nếu sửa class dùng chung
6. Figma: `get_selection()` nếu có UI
7. Ghi vào `.kiro/specs/TICKET-ID/spec.md`

> ✅ SESSION 1 xong · 👉 Session mới: `"TICKET-ID SESSION 1.5"` (có UI) hoặc `"TICKET-ID SESSION 2"`

## SESSION 1.5 — DESIGN *(chỉ khi có UI)*
1. Đọc spec.md
2. `get_selection()` → `get_design_context(level="compact")`
3. Ghi vào spec.md phần `## Design`

> ✅ SESSION 1.5 xong · 👉 Session mới: `"TICKET-ID SESSION 2"`

## SESSION 2..N — IMPLEMENT *(1 file/session)*
1. Đọc spec.md → routing table → steering file
2. `get_file_content(path, class_name="X")`
3. Implement → `getDiagnostics` → sửa lỗi
4. Đánh dấu `[x]` trong spec.md

> ✅ SESSION N xong · 📋 Còn: [file chưa x] · 👉 Session mới: `"TICKET-ID SESSION N+1"` hoặc `"TICKET-ID VERIFY"`

## SESSION VERIFY
1. Đọc spec.md → kiểm tra `[x]` hết chưa
2. `dart run build_runner build --delete-conflicting-outputs` nếu có Model mới
3. `dart run slang` nếu có i18n mới
4. `flutter analyze` → sửa hết warning/error

> ✅ VERIFY xong · 👉 Session mới: `"TICKET-ID SHIP"`

## SESSION SHIP
1. `git checkout -b feat/TICKET-ID`
2. `git add` đúng file trong spec
3. `git commit -m "feat(TICKET-ID): mô tả ngắn"`
4. `git push -u origin feat/TICKET-ID`
5. Jira: comment + transition → Build + label `AI-Native`

> ✅ TICKET-ID hoàn thành · 🌿 Branch pushed · 🎫 Jira updated

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
