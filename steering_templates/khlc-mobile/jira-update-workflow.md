---
inclusion: manual
---

# 🎫 Jira Update Workflow

Khi user yêu cầu update Jira ticket sau khi implement xong, thực hiện **tất cả** các bước sau trong 1 lượt:

## Checklist (thực hiện tuần tự)

### 1. Story Points
- Field: `customfield_10106` (type: float)
- Quy ước: **1 SP = 8h**
- Dùng `jira_update_issue` với `fields: {"customfield_10106": <số>}`

### 2. Log Work
- Dùng `jira_add_worklog` với `time_spent` format: `1h`, `4h`, `1d` (1d = 8h)
- Comment mô tả ngắn gọn công việc đã làm

### 3. Transition Status
- Dùng thẳng `jira_transition_issue` với ID bên dưới — **KHÔNG cần gọi `jira_get_transitions`**
- Transition IDs (DSIP project):
  - `461` — Build
  - `451` — Review Build
  - `331` — READY CI TESTING
  - `101` — IN CI TESTING
  - `361` — READY UAT
  - `51` — UAT
  - `61` — COMPLETED
  - `421` — RE-OPEN
  - `91` — OPEN
  - `391` — DEPLOYING
  - `81` — CANCELLED
  - `111` — Pending
  - `441` — BA Verifying
  - `21` — APPROVED BY TMO (2)
  - `511` — PLAN
  - `491` — Understand
  - `501` — Intent
  - `481` — Shape
  - `471` — Review Shape
  - `201` — Solution Ready
  - `191` — Discovery (2)

### 4. Comment
- Dùng `jira_add_comment` với nội dung:
  - Branch name
  - Summary changes ngắn gọn
  - Quality Gate result (nếu có)
  - Link ticket liên quan (nếu code chung branch)

### 5. Label
- Thêm label `AI_Native` nếu AI hỗ trợ implement (thường đã có sẵn)

## Ví dụ prompt từ user

> "Update Jira DSIP-3035: 3 point, logwork 21h, kéo Build"

→ Thực hiện:
1. `jira_update_issue(DSIP-3035, {"customfield_10106": 3})`
2. `jira_add_worklog(DSIP-3035, "21h", comment="...")`
3. `jira_transition_issue(DSIP-3035, "461")`
4. `jira_add_comment(DSIP-3035, "✅ Done — branch: feat/..., QG: PASS")`

## Lưu ý
- Nếu nhiều ticket cùng branch → comment cross-reference giữa các ticket
- Nếu user nói "est X point" → tính logwork = X × 8h
- Luôn dùng `customfield_10106` cho Story Point (KHÔNG dùng `story_points` trong fields)
- Transition IDs đã được hardcode cho DSIP project — không cần gọi `get_transitions`
