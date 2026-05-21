---
inclusion: auto
---

# Git Push Rules

## Repo IDs / source_id thường dùng

`chain_id`: `DS`

Khi dùng Flutter Context hoặc AI Context, ưu tiên dùng đúng repo/source_id dưới đây:
- Flutter Context `repo`: tên repo local, ví dụ `khlc-content`
- AI Context `source_id`: GitLab source id dạng `gitlab:<project_id>`, ví dụ `gitlab:3890`

Khi tạo branch/MR/pipeline bằng AI Context, luôn truyền đủ:
- `chain_id`: `DS`
- `source_id`: AI Context `source_id` trong bảng
- `branch`: branch hiện tại hoặc branch user yêu cầu

Ví dụ:
```text
create_merge_request(source_id="gitlab:1386", chain_id="DS", branch="feat/DSIP-3198", issue_key="DSIP-3198")
```

| Repo local | Flutter Context `repo` | AI Context `source_id` | GitLab path |
|-----------|-------------------------|--------------------------|-------------|
| `/Users/dungtv54/FPT/khlc-mobile` | `khlc-mobile` | `gitlab:414` | `mobile-team/khlc-mobile/khlc-mobile` |
| `/Users/dungtv54/FPT/khlc-core` | `khlc-core` | `gitlab:415` | `mobile-team/khlc-mobile/packages/khlc-core` |
| `/Users/dungtv54/FPT/khlc-authentication` | `khlc-authentication` | `gitlab:454` | `mobile-team/khlc-mobile/packages/khlc-authentication` |
| `/Users/dungtv54/FPT/khlc-profile` | `khlc-profile` | `gitlab:500` | `mobile-team/khlc-mobile/packages/khlc-profile` |
| `/Users/dungtv54/FPT/khlc-cart` | `khlc-cart` | `gitlab:513` | `mobile-team/khlc-mobile/packages/khlc-cart` |
| `/Users/dungtv54/FPT/khlc-product` | `khlc-product` | `gitlab:1142` | `mobile-team/khlc-mobile/packages/khlc-product` |
| `/Users/dungtv54/FPT/khlc-order` | `khlc-order` | `gitlab:1319` | `mobile-team/khlc-mobile/packages/khlc-order` |
| `/Users/dungtv54/FPT/khlc-fsell` | `khlc-fsell` | `gitlab:763` | `mobile-team/khlc-mobile/packages/khlc-fsell` |
| `/Users/dungtv54/FPT/khlc-messenger` | `khlc-messenger` | `gitlab:1386` | `mobile-team/khlc-mobile/packages/khlc-messenger` |
| `/Users/dungtv54/FPT/khlc-consultancy` | `khlc-consultancy` | `gitlab:1205` | `mobile-team/khlc-mobile/packages/khlc-consultancy` |
| `/Users/dungtv54/FPT/khlc-notification` | `khlc-notification` | `gitlab:512` | `mobile-team/khlc-mobile/packages/khlc-notification` |
| `/Users/dungtv54/FPT/khlc-finding-store` | `khlc-finding-store` | `gitlab:1425` | `mobile-team/khlc-mobile/packages/khlc-finding-store` |
| `/Users/dungtv54/FPT/khlc-landing` | `khlc-landing` | `gitlab:2332` | `mobile-team/khlc-mobile/packages/khlc-landing` |
| `/Users/dungtv54/FPT/khlc-content` | `khlc-content` | `gitlab:3890` | `mobile-team/khlc-mobile/packages/khlc-content` |
| `/Users/dungtv54/FPT/khlc-vaccine` | `khlc-vaccine` | `gitlab:2188` | `mobile-team/khlc-mobile/packages/khlc-vaccine` |
| `/Users/dungtv54/FPT/khlc-medicine-schedule` | `khlc-medicine-schedule` | `gitlab:3783` | `mobile-team/khlc-mobile/packages/khlc-medicine-schedule` |
| `/Users/dungtv54/FPT/khlc-247` | `khlc-247` | `gitlab:2400` | `mobile-team/khlc-mobile/packages/khlc-247` |
| `/Users/dungtv54/FPT/khlc-payment` | `khlc-payment` | `gitlab:4404` | `mobile-team/khlc-mobile/packages/khlc-payment` |
| `/Users/dungtv54/FPT/khlc-sso-integration` | `khlc-sso-integration` | `gitlab:5334` | `mobile-team/khlc-mobile/packages/khlc-sso-integration` |
| `/Users/dungtv54/FPT/khlc-ui` | `khlc-ui` | `gitlab:2259` | `mobile-team/khlc-mobile/packages/khlc-ui` |

## Quy tắc bắt buộc khi push code:

1. **KHÔNG push `pubspec.yaml`** mà không hỏi user trước. Luôn hỏi xác nhận trước khi stage/commit pubspec.yaml.

2. **Chỉ push code do AI tạo/sửa**. Không push những file mà user đã sửa riêng (kiểm tra `git diff` trước khi stage).

3. **Trước khi `git add`**, luôn kiểm tra danh sách file thay đổi bằng `git status` và chỉ stage những file mà AI đã trực tiếp tạo hoặc sửa trong session hiện tại.

4. **Không dùng `git add .`** — luôn stage từng file cụ thể.
