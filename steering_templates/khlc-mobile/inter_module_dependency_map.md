---
inclusion: manual
---

# 🗺️ Inter-Module Dependency Map

Tài liệu này mô tả sơ đồ phụ thuộc giữa các module trong hệ sinh thái KHLC-Mobile.
Shell App (`khlc-mobile`) đóng vai trò là **orchestrator** - nó import và wire tất cả các package lại với nhau.

---

## 🏗️ Sơ đồ tổng quan (Dependency Tree)

```
khlc-mobile (Shell App)
├── khlc_core              ← Base UI, design system, shared utilities (tất cả module đều phụ thuộc)
├── khlc_authentication    ← Auth/OTP (login_usecase, logout_usecase dùng trực tiếp)
├── khlc_profile           ← User info (AppLoginUseCase dùng GetUserInfoUseCase)
├── khlc_product           ← Sản phẩm (ProductModule, ProductDetailModule, SearchProductsModule)
├── khlc_cart              ← Giỏ hàng (ShoppingCartModule, CartConfirmModule)
│   └── phụ thuộc: khlc_product (CartItemEntity chứa ProductEntity)
├── khlc_order             ← Đơn hàng (KHLCOrderModule, DetailOrderModule, RebuyModule)
│   └── phụ thuộc: khlc_cart (dùng CartEntity để tạo order)
├── khlc_payment           ← Thanh toán (được gọi từ CartConfirmModule)
│   └── phụ thuộc: khlc_cart, khlc_order
├── khlc_notification      ← Thông báo (NotificationModule, AppLoginUseCase sync count)
│   └── phụ thuộc: khlc_authentication (cần token để register device)
├── khlc_messenger         ← Chat (MessengerModule, AppLogoutUseCase clean session)
│   └── phụ thuộc: khlc_authentication
├── khlc_fsell             ← Tích điểm Fsell (FsellModule, LoyaltyModule)
│   └── phụ thuộc: khlc_authentication, khlc_cart
├── khlc_vaccine           ← Tiêm chủng (KHLCVaccineModule)
│   └── phụ thuộc: khlc_authentication, khlc_core
├── khlc_finding_store     ← Tìm nhà thuốc (FindAStoreModule)
├── khlc_content           ← Bài viết/CMS (ContentModule, ContentSharedModule)
├── khlc_content_vaccine   ← Nội dung vaccine (ContentVaccineModule)
├── khlc_landing           ← Landing pages (LandingPageModule)
├── khlc_medicine_schedule ← Lịch uống thuốc (MedicineScheduleModule)
├── khlc_247               ← Dịch vụ 24/7 (Lc247Module)
│   └── phụ thuộc: khlc_authentication
├── khlc_consultancy       ← Tư vấn (ConsultancyModule)
├── khlc_widget            ← Home screen widget (reload sau login/logout)
├── mom_baby_care          ← Module mẹ & bé (MBCareModule, MBCareGlobalModule)
├── khlc_family_package    ← Gói gia đình (FamilyPackageModule)
├── frt_ai_chat            ← AI Chat (TimChatModule)
└── external_onboarding    ← Onboarding flow (OnboardingModule, AppOnboardingModule)
```

---

## 🔗 Chi tiết phụ thuộc theo luồng nghiệp vụ

### Luồng Đăng nhập (Login Flow)
```
khlc_authentication  →  AppLoginUseCase (shell)
    ↓ sau login thành công
khlc_profile         →  GetUserInfoUseCase
khlc_cart            →  MergeCartUseCase (merge guest cart → user cart)
khlc_notification    →  GetCountNotificationUseCase
khlc_fsell           →  GetLoyaltyPointUseCase
khlc_messenger       →  CountMessageUnreadUseCase
khlc_widget          →  KhlcWidget.reloadWidget("LC247Widget")
```

### Luồng Đăng xuất (Logout Flow)
```
AppLogoutUseCase (shell)
    ↓
khlc_authentication  →  AppRemoveTokenUseCase (xóa token)
khlc_cart            →  RemoveSessionIdUseCase (xóa session giỏ hàng)
khlc_notification    →  RemoveRegisteredDeviceUseCase
khlc_messenger       →  ChatCleanSessionUseCase
mom_baby_care        →  MBCoreProfileController.logout()
khlc_widget          →  KhlcWidget.clearWidgetCache() + reloadWidget()
```

### Luồng Mua hàng (Purchase Flow)
```
khlc_product  →  ProductDetailEntity (sku, unitCode, price)
    ↓
khlc_cart     →  AddProductsToCartUseCase / BuyNowProdsListUseCase
    ↓
khlc_cart     →  CartConfirmModule (CartEntity → ItemParams)
    ↓
khlc_payment  →  PaymentMethodsPage (chọn PTTT)
    ↓
khlc_order    →  OrderDetailEntity (kết quả đơn hàng)
```

---

## 📦 Shared Factories (Global Singletons - inject qua MainModule)

| Factory | Vai trò | Được dùng bởi |
|---|---|---|
| `CartCountFactory` | Badge số lượng giỏ hàng | khlc_cart, shell |
| `LoyaltyPointFactory` | Điểm Fsell hiển thị | khlc_fsell, shell |
| `NotificationFactory` | Badge thông báo | khlc_notification, shell |
| `DashboardTabFactory` | Điều hướng tab chính | shell, khlc_core |
| `FlashSaleFactory` | Trạng thái Flash Sale | khlc_product, khlc_cart |
| `UserDataFactory` | Thông tin user global | tất cả module |
| `HomePopupFactory` | Popup toàn app | shell, khlc_cart |

---

## ⚠️ Quy tắc quan trọng

- `khlc_core` là dependency bắt buộc của **tất cả** module. Không bao giờ bypass.
- Các module **KHÔNG** được import lẫn nhau trực tiếp. Mọi cross-module communication đi qua **Factory** hoặc **UseCase** được inject từ Shell App.
- Shell App là nơi duy nhất wire các UseCase cross-module (ví dụ: `AppLoginUseCase` kết hợp `khlc_authentication` + `khlc_cart` + `khlc_profile`).

Cập nhật lần cuối: 13/04/2026 - Generated from MainModule & import_module.dart
