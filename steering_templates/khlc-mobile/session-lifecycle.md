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

## SESSION 2..N — IMPLEMENT *(1 change cluster/session)*
1. Đọc spec.md → routing table → steering file
2. `get_file_content(path, class_name="X")` cho file chuẩn bị sửa
3. Implement đúng change cluster trong spec → `getDiagnostics` → sửa lỗi
4. Đánh dấu `[x]` file/session trong spec.md
5. Ghi `## Session Notes`: files thực tế đã sửa, tóm tắt thay đổi, verify đã chạy/chưa chạy

**Session sizing**
- Được gom nhiều file nếu cùng 1 flow, pattern đã rõ, blast radius thấp, đọc không quá 3 file hoặc 1 cụm BLoC.
- Không gom nếu task UI chưa qua SESSION 1.5, cần đọc nhiều context mới, chạm shared/core/cross-repo, API/model ảnh hưởng rộng, hoặc bắt đầu có nhiều assumption.

> ✅ SESSION N xong · 📋 Còn: [file chưa x] · 👉 Session mới: `"TICKET-ID SESSION N+1"` hoặc `"TICKET-ID VERIFY"`

## SESSION VERIFY
1. Đọc spec.md → kiểm tra `[x]` hết chưa
2. `dart run build_runner build --delete-conflicting-outputs` nếu có Model mới
3. `dart run slang` nếu có i18n mới
4. `flutter analyze` → sửa hết warning/error
5. Kiểm tra `git diff` chỉ gồm file đã liệt kê trong spec.md; nếu có file ngoài spec → cập nhật spec trước
6. Ghi kết quả verify vào spec.md

> ✅ VERIFY xong · 👉 Session mới: `"TICKET-ID SHIP"`

## SESSION SHIP
1. `git checkout -b feat/TICKET-ID`
2. `git add` đúng file trong spec
3. `git commit -m "feat(TICKET-ID): mô tả ngắn"`
4. `git push -u origin feat/TICKET-ID`
5. Jira: comment + transition → Build + label `AI-Native`
6. Ghi branch/commit/Jira status vào `## Session Notes`
7. Giữ task context; chưa xoá/archive ở SHIP, chỉ cleanup khi Done/Go-live

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
