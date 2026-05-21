---
inclusion: always
---

# Workflow Rules

## Routing — chỉ đọc file liên quan

| Task | Từ khóa | File |
|------|---------|------|
| UI | screen, view, widget, Figma | `ui_ux_standards.md`, `screen_business_logic.md` |
| Feature | implement, UseCase, business logic | `architecture_standards.md`, `usecase_registry.md` |
| Data/API | model, entity, API, response | `data_model_mapping.md`, `data_model_journey.md` |
| Core | khlc_core, shared, cross-module | `inter_module_dependency_map.md` |
| Navigation | deep link, routing, notification | `module_detailed_functions.md` |
| Git | push, branch, commit | `git-push-rules.md` |
| Jira | comment, transition, update | `jira-update-workflow.md` |

**Không đọc file không có trong bảng trên.**

---

## Session rules

- Mỗi session chỉ làm **1 việc**. Kết thúc ngay khi xong.
- `spec.md` tại `.kiro/specs/TICKET-ID/spec.md` là bộ nhớ dùng chung giữa các session.
- Chi tiết vòng đời task → đọc `session-lifecycle.md` (manual).

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

- Sizing: `.sc()` · Spacing: `KHLCSpacing` · Colors: `AliasColor`/`NeutralColor`
- Typography: `AppStyle` · Entity: `extends Equatable`, `const`, `final`
- Model: `@JsonSerializable(createToJson: false)` · UseCase: `Modular.get<T>()`
- BLoC: 3 file riêng (bloc/event/state) · khlc_core first
