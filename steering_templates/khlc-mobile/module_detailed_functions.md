---
inclusion: manual
---

# 🔧 Module Detailed Functions

Tài liệu này mô tả các function/service/bloc quan trọng trong Shell App và cách chúng hoạt động.
Mục tiêu: AI có thể hiểu "ai làm gì" mà không cần đọc lại toàn bộ code.

---

## 🚀 1. Dashboard Lifecycle Services

### DashboardServices (mixin)
Path: `lib/src/features/dashboard/presentations/services/dashboard_services.dart`

Chia làm 2 nhóm service chạy khi Dashboard khởi động:

**synchronousServices()** - Chạy tuần tự (theo thứ tự):
| Service | Vai trò |
|---|---|
| `VersionService` | Kiểm tra version mới, force update nếu cần |
| `ChildWarriorService` | Kiểm tra chính sách bảo vệ trẻ em |
| `AppNotiServices` | Khởi tạo push notification (OneSignal) |
| `AppLinkServices` | Xử lý deeplink/app link khi mở app |

**asynchronousServices()** - Chạy song song (gần như đồng thời):
| Service | Vai trò |
|---|---|
| `HomeFetchDataService` | Fetch toàn bộ data trang chủ |
| `ConnectionService` | Theo dõi trạng thái mạng |
| `CounterServices` | Đồng bộ badge (giỏ hàng, thông báo, tin nhắn) |
| `ProductSuggestionService` | Tải gợi ý tìm kiếm |
| `InAppMessageServices` | Tải in-app message/popup |
| `HealthCheckService` | Kiểm tra sức khỏe hệ thống |
| `VaccineService` | Khởi tạo dữ liệu vaccine |
| `LiteThemeService` | Áp dụng theme Lite App nếu có |

---

## 🏠 2. HomeFetchDataService

Path: `lib/src/features/home/presentation/services/home_service.dart`

### fetchAll()
Được gọi khi: `onInit()`, `onForegroundGained()` (app từ background về foreground).
```
fetchAll() gọi:
├── GlobalConfigBloc.add(FetchGlobalConfigEvent)   → Lấy background, màu sắc, UIMode
├── HomeConfigBloc.add(FetchHomeConfigEvent)        → Lấy cấu trúc sections trang chủ
├── cleanProductCacheUseCase(null)                  → Xóa cache sản phẩm cũ
├── searchSettingBloc.add(GetSearchSettting)        → Lấy cấu hình tìm kiếm
├── loginManagerBloc.add(GetLoginManager)           → Kiểm tra trạng thái đăng nhập
└── homeLiteBloc.add(FetchHomeLiteConfigEvent)      → Lấy config Lite App
```

### fetchIfHomeDone()
Được gọi sau khi `HomeConfigDoneState` emit (trang chủ đã load xong).
```
fetchIfHomeDone() gọi:
├── shortcutBloc.add(GetShortcutsEvent)             → Tải shortcuts (luôn gọi)
└── Nếu authenticated:
    ├── ratingBloc.add(GetListOrderRatingEvent)     → Tải đánh giá đơn hàng chờ
    ├── homeNotiBloc.add(GetHomeNotiEvent)          → Tải thông báo trang chủ
    └── rebuyBloc.add(GetHistoryOrderEvent)         → Tải đơn hàng mua lại
```

---

## 🔐 3. AppLoginUseCase

Path: `lib/application/src/domain/usecase/login_usecase.dart`

Được gọi khi: Đăng nhập thành công VÀ mỗi lần khởi động app (nếu đã có token).

**Flag quan trọng:** `shouldMergeCart`
- Lần đầu vào app: `false` → KHÔNG merge cart (tránh ghi đè giỏ hàng cũ)
- Sau lần đầu: `true` → Merge guest cart vào user cart khi đăng nhập

**Luồng thực thi:**
```
execute()
├── Lấy token từ TokenUseCase
├── Decode token → lấy customerId
├── GetUserInfoUseCase → lấy thông tin user
├── Nếu shouldMergeCart == true:
│   ├── _registerDevice()     → Đăng ký device với OneSignal
│   └── _mergeCart()          → Merge guest cart → user cart
├── cartHomeUseCase.execute() → Sync giỏ hàng
├── countUnreadMessage        → Đếm tin nhắn chưa đọc
├── getCountNotificationUseCase → Đếm thông báo chưa đọc
├── getLoyaltyPointUseCase    → Lấy điểm Fsell
└── KhlcWidget.reloadWidget("LC247Widget") → Reload home widget
```

---

## 🚪 4. AppLogoutUseCase

Path: `lib/application/src/domain/usecase/logout_usecase.dart`

**Luồng thực thi:**
```
execute()
├── _clearInsiderSyncFlag()           → Xóa flag sync Insider + logout Insider SDK
├── XIDFlagFactory.inst.reset()       → Reset XID tracking
├── chatCleanSessionUseCase()         → Xóa session chat (khlc_messenger)
├── Analytics reset userId            → Snowplow setUserId(null)
├── removeUserNumberPhoneUseCase()    → Xóa số điện thoại lưu local
├── Reset factories:
│   ├── cartCountFactory → CartCount()
│   ├── loyaltyPointFactory.point = 0
│   └── notificationFactory → NotificationEntity()
├── MBCoreProfileController.logout()  → Logout mom_baby_care
├── _removeDevice()                   → Hủy đăng ký device push notification
├── AppRemoveTokenUseCase()           → Xóa token (khlc_authentication)
├── _removeCartData()                 → Xóa session giỏ hàng (khlc_cart)
└── _reloadAllWidgets():
    ├── KhlcWidget.clearWidgetCache()
    └── KhlcWidget.reloadWidget("LC247Widget")
```

---

## 🛒 5. AddProductsToCartUseCaseImpl

Path: `lib/application/src/domain/usecase/add_products_to_cart_usecase_impl.dart`

Cross-module usecase: kết hợp `khlc_cart` + `khlc_order` + `khlc_core`.

**Params mapping:**
```
ProductInfoAddToCartParams (input từ khlc_product)
    ↓ map sang
AddProductToCartParam (input của khlc_cart)
    ├── sessionId    ← GetSessionIdUseCase
    ├── customerId   ← UserInfoUseCase
    ├── phoneNumber  ← UserInfoUseCase
    └── cartItem:
        ├── unitCode
        ├── quantity
        └── itemCart (sku)
```

---

## 🔗 6. DeepLink Handling

Path: `lib/application/src/domain/delegate/link_handle/`

**Thứ tự xử lý deeplink (delegate chain):**
```
LinkHandle.delegates (theo thứ tự ưu tiên):
1. AwareDuplicateLink      → Chặn duplicate link (tránh navigate 2 lần)
2. InitialLinkDelegate     → Xử lý link khi app cold start
3. DeepLinkDelegate        → Map type → route nội bộ
4. VaccineDeepLinkDelegate → Deeplink riêng cho module vaccine
5. MomBabyDeeplink         → Deeplink riêng cho mom_baby_care
6. DeepLinkGuardDelegate   → Kiểm tra auth trước khi navigate
7. WebLinkDelegate         → Fallback: mở browser nếu không match route nào
```

---

## 🏠 7. Home BLoCs Overview

| BLoC | Path | Vai trò |
|---|---|---|
| `GlobalConfigBloc` | `bloc/global_config/` | UIMode (main/lite), background URL, text scaling |
| `HomeConfigBloc` | `bloc/home_config/` | Danh sách sections động trên trang chủ |
| `ShortcutBloc` | `bloc/shortcuts/` | Các shortcut icon trên trang chủ |
| `RebuyBloc` | `bloc/rebuy/` | Đơn hàng gần đây để mua lại |
| `HomeNotiBloc` | `bloc/noti/` | Thông báo hiển thị trên trang chủ |
| `SearchSettingBloc` | `bloc/search/` | Cấu hình thanh tìm kiếm |
| `LoginManagerBloc` | `bloc/login_manager/` | Quản lý trạng thái đăng nhập |

---

## ⚙️ 8. Route Guards

| Guard | Điều kiện | Redirect về |
|---|---|---|
| `KHLCGuard` | App chưa init xong | Splash screen |
| `HomeGuard` | Chưa pass onboarding | Onboarding |
| `AuthenticationGuard` | Chưa đăng nhập | Login screen |
| `VaccineAuthenticationGuard` | Chưa đăng nhập (vaccine) | Login screen |
| `InitialGuard` | SSO integration check | - |
| `OnboardingGuard` | Đã xem onboarding rồi | Home |

---

## 🗺️ Navigation / Routing

### SlugRouter
Path: `lib/application/navigation/slug/slug_router.dart`

Singleton điều phối tất cả deeplink/redirect URL. First-match wins theo thứ tự:
```
SlugRouter.I.navigate(context, redirectUrl: url)
  → DeepLinkSlugHandler      ← deeplink nội bộ (scheme khlc://)
  → InternalPageSlugHandler  ← trang nội bộ (path /product, /cart...)
  → ExternalUrlHandler       ← URL bên ngoài → mở browser
  → FallbackSlugHandler      ← fallback cuối cùng
```
Dùng khi: banner tap, notification tap, CMS redirect.

---

### MainRoute
Path: `lib/application/src/main_route.dart`

Root route tree — mapping toàn bộ module vào path:

| Path | Module |
|------|--------|
| `/` | KHLCHomeRoute (home + splash) |
| `/auth` | AuthRoute |
| `/profile` | ProfileRoute |
| `/product` | ProductRoute |
| `/search` | SearchProductsRoute |
| `/cart` | ShoppingCartRoute |
| `/fsell` | FsellRoute (loyalty) |
| `/messenger` | MessengerRoute |
| `/listNotification` | NotificationRoute |
| `/historyOrder` | KHLCOrderRoute |
| `/vaccine` | KHLCVaccineRoute |
| `/consultancy` | ConsultancyRoute |
| `/longchau247` | Lc247Route |
| `/medicineScheduleModule` | MedicineScheduleRoute |
| `/sso-integration` | SSOIntegrationRoute |
| `/maintenance` | MaintenanceRoute |

---

### KHLCHomeRoute
Path: `lib/src/khlc_home_route.dart`

Sub-route của `/` — chứa các màn hình shell chính:
- `/home` → `DashboardRoute`
- `/` → `KHLCSplashRoute` (splash)
- `/maintenance` → `MaintenanceRoute`
- `/web` → WebView
- `/miniGame` → `GameUnityRoute`

---

### KHLCAuthService
Path: `khlc-authentication/lib/src/shared/manager/auth_service.dart`

ValueNotifier quản lý trạng thái auth toàn app. Các màn hình lắng nghe qua `IAuthentication`:

| Method | Tác dụng |
|--------|---------|
| `authenticated(UserInfoEntity)` | Set state → `IAuth.authenticated`, lưu `_current` + `_previous` |
| `unauthenticated()` | Set state → `IAuth.unauthenticated`, clear `_current` |
| `expired()` | Set state → `IAuth.expired` (token hết hạn) |

Inject qua `Modular.get<KHLCAuthService>()`. Không gọi trực tiếp từ UI — dùng UseCase.

---

Cập nhật lần cuối: 14/05/2026 - Bổ sung Routes + KHLCAuthService từ graph analysis
