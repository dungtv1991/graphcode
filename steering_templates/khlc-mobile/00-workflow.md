---
inclusion: always
---

# Workflow Rules

## Routing — chỉ đọc file liên quan

| Task | Từ khóa | File |
|------|---------|------|
| UI | screen, view, widget, Figma | `ui_ux_standards.md`, `screen_business_logic.md` |
| Tracking DC5 | tracking, analytics, SnowPlow, KHLCSnowPlowDc5, Dc5 | `khlc_snowplow_dc5_tracking_flow.md` |
| Feature | implement, UseCase, business logic | `architecture_standards.md`, `usecase_registry.md` |
| Data/API | model, entity, API, response | `data_model_mapping.md`, `data_model_journey.md` |
| Core | khlc_core, shared, cross-module | `inter_module_dependency_map.md` |
| Navigation | deep link, routing, notification | `module_detailed_functions.md` |
| Git | push, branch, commit | `git-push-rules.md` |
| Jira | comment, transition, update | `jira-update-workflow.md` |
| Session | lifecycle, vòng đời, session | `session-lifecycle.md` |

**Không đọc file không có trong bảng trên.**

---

## Session rules

- Mỗi session chỉ làm **1 việc = 1 change cluster có thể verify được**. Kết thúc ngay khi xong.
- Không chia máy móc theo từng file/layer nếu cùng một flow và context thấp.
- Nếu cùng một flow, context ít, blast radius thấp thì được gom nhiều file trong 1 session.
- Task có UI/Figma: luôn có SESSION 1.5 trước khi implement.
- Được gom nhiều file nếu cùng 1 flow, pattern đã rõ, blast radius thấp, đọc không quá 3 file hoặc 1 cụm BLoC.
- Không gom nếu cần đọc nhiều context mới, chạm shared/core/cross-repo, API/model ảnh hưởng rộng, UI chưa qua SESSION 1.5, hoặc bắt đầu có nhiều assumption.
- Với tracking/logging/analytics, mapping nhỏ, text nhỏ, UI nhỏ đã rõ design: ưu tiên làm gọn trong ít session.
- `spec.md` tại `.kiro/specs/TICKET-ID/spec.md` là bộ nhớ dùng chung giữa các session.
- Cuối mỗi IMPLEMENT session phải cập nhật `## Session Notes`: files thực tế đã sửa, tóm tắt thay đổi, verify đã chạy/chưa chạy.
- VERIFY phải kiểm tra `git diff` chỉ gồm file đã liệt kê trong `spec.md`; nếu có file ngoài spec → cập nhật spec trước.
- SHIP chỉ push/lead review; giữ task context, chưa xoá/archive. Cleanup chỉ làm khi Done/Go-live.
- Chi tiết vòng đời task → đọc `session-lifecycle.md` (manual).

---

## flutter-context — Tool decision tree

```
Biết tên class chính xác?
  → grep_in_files("ClassName")

Biết tên file/feature nhưng không rõ path?
  → search_by_filename("cart_bloc")

Chỉ biết mô tả / yêu cầu business?
  → query_context(query, top_k=5, snippet_chars=0)
    (snippet_chars=0 vì node đã có summary — chỉ cần path + graph)

Cần đọc code thật?
  → get_file_content(path, class_name="X")
```

**Quy tắc:**
- `snippet_chars=0` khi chỉ cần biết file nào liên quan (tiết kiệm token)
- `snippet_chars=300` chỉ khi node chưa có summary (graph cũ)
- `class_name` param **bắt buộc** khi đọc file — jump thẳng đến class
- Đọc tối đa **3 file/session** (BLoC = bloc+event+state tính 1 cụm)
- `call_api(url)` khi cần verify response thật vs model

---

## Code Standards

- Sizing: `.sc()` · Spacing: `KHLCSpacing` · Colors: `AliasColor`/`NeutralColor`
- Typography: `AppStyle` · Entity: `extends Equatable`, `const`, `final`
- Model: `@JsonSerializable(createToJson: false)` · UseCase: `Modular.get<T>()`
- BLoC: 3 file riêng (bloc/event/state) · khlc_core first
