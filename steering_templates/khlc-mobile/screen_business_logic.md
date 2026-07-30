---
inclusion: manual
---

Granular Screen Business Logic Map (Siêu chi tiết)
Tài liệu này cấu trúc lại nghiệp vụ theo dạng "X-Ray" để AI truy vấn nhanh và tiết kiệm Token.

🛒 MODULE: KHLC-CART
🚩 Screen: CartConfirmView
Identifier: CartConfirmView | Path: khlc-cart/lib/src/features/cart_confirm/presentation/views/cart_confirm_view.dart
Logic Controllers (BLoCs):
ShoppingCartBloc: Quản lý item & giá tổng.
CartDeliveryPromissingBloc: Tính phí ship & Cam kết giao hàng.
OtcBloc: Xử lý thông tin người mua thuốc không kê đơn.
CreatingOrderBloc: Thu thập dữ liệu cuối cùng để Build Order.
Data Flow (Triggers):
initState: Gửi SetDeliveryMethod & LoadAddressDeliveryEvent.
DeliveryOrderPromissingDoneState: Nhận phí ship mới -> Gọi GetCart(shipmentPrice).
ConfirmCart Event:
Nếu isZeroPrice -> CreateOrderEvent(isZeroPrice: true).
Nếu price > 0 -> Gọi navigateToPaymentMethods.
Business Rules:
OTC Logic: Nếu giỏ hàng có thuốc OTC -> OtcBloc hiện BottomSheet -> User điền thông tin -> Tiếp tục luồng Verify.
Ship Fee: Nhận tại nhà thuốc (ShopSelected) -> Reset phí ship về 0.
Navigation:
Success (0đ): Sang OrderConfirmArgs.
Error: Hiện AppImageDynamicComfirmPopup với option "Về giỏ hàng" hoặc "Hỗ trợ".
📦 MODULE: KHLC-PRODUCT
🚩 Screen: ProductDetailView
Identifier: ProductDetailView | Path: khlc-product/lib/src/features/product_detail/presentation/view/product_detail_view.dart
Logic Controllers:
CommentBloc: Quản lý bình luận & đánh giá.
LongDescriptionBloc: Tải và hiển thị chi tiết sản phẩm.
Data Flow (Triggers):
LongDescriptionBloc.add(Init(sku)): Gọi GetProductLongDescriptionUseCase.
Filter logic: Chỉ hiển thị các items có value là String và longDescriptionTitle != null.
GlobalKey Generation: Mỗi item được gán một GlobalKey để quản lý view động.
Business Rules:
Consultancy Mode: Nếu detailConsultace == true -> Ẩn: Giá, Nút Add to Cart, AppBar, Sản phẩm liên quan.
Flash Sale: Nếu có promotionCode & unitCode -> Ưu tiên load giá Flash Sale thay vì giá thường.
Analytics:
logViewItem (Firebase/Snowplow) ngay khi load thành công.
visitProductDetailPage (Insider).
Ingredient Formatting (Ticket DSIP-632):
Label: Luôn hiển thị tiêu đề "Thành phần".
Content (Prefix): Tự động chèn biến ${ingredientFor} (ví dụ: "10ml") từ PIM và từ nối " chứa: " vào đầu danh sách thành phần.
Styling: Phân tách style trong IngredientDisplay: ${ingredientFor} dùng Body2.bold, " chứa: " dùng Body2.regular.
Fallback: Nếu ingredientFor null/empty -> Không hiển thị tiền tố.
Long Description Mapping:
short-description -> "Đặc điểm nổi bật".
ingredient -> "Thành phần".
description -> "Thông tin chi tiết sản phẩm".
uses/usage -> "Công dụng".
dosage -> "Liều dùng".
careful -> "Lưu ý".
preservation -> "Bảo quản".
adverseEffect -> "Tác dụng phụ".
💳 MODULE: KHLC-PAYMENT
🚩 Screen: PaymentMethodsPage
Identifier: PaymentMethodsPage | Path: khlc-payment/lib/page/payment_methods/presentation/payment_method_page/payment_methods_page.dart
Logic Controllers:
PaymentMethodsBloc: Danh sách phương thức khả dụng.
RepaymentBloc: Xử lý luồng thanh toán lại cho đơn hàng cũ.
PaymentMethodSelectionBloc: Lưu phương thức đang được chọn.
Business Rules:
Repayment Timeout: Nếu quá hạn thanh toán lại -> Hiện showRepaymentPopup (Error 403).
Flash Sale Constraint: Tự động gọi GetLatestPaymentMethodSelected và vô hiệu hóa COD nếu đơn hàng chứa Flash Sale.
VNPay SDK: Dùng Plvnpay.shared.registerHandler() để lắng nghe kết quả từ App VNPay.
LifeCycle Logic:
resumed: Khi người dùng quay lại từ App ví (Momo/ZaloPay), gọi CheckPaymentProcessEvent để cập nhật/kiểm tra trạng thái đơn.
Digital Wallet Flow (Momo/ZaloPay):
Launch Logic: Khi nhấn "Thanh toán", PaymentDigitalBloc set isProcessing = true -> Mở deep link sang App ví.
State Transition: Ngay khi mở app ví thành công -> Emit DigitalPaymentDoneState -> UI Listener thực hiện popAndPushNamed sang PaymentStatusPage.
Resumed Safeguard: Nếu user quay lại mà isProcessing vẫn true (do app ví không mở được hoặc treo) -> CheckPaymentProcessEvent sẽ emit PaymentFailedState để giải phóng màn hình.
Verification Page: PaymentStatusPage chịu trách nhiệm cuối cùng trong việc gọi API polling/check-status để hiển thị kết quả thực tế từ server.
💉 MODULE: KHLC-VACCINE
🚩 Screen: VaccineHomePage
Identifier: VaccineHomePage | Path: khlc-vaccine/lib/src/features/home/presentations/view/vaccine_home_page.dart
Logic Controllers:
SelectedProfileController: Quản lý hồ sơ người tiêm đang được chọn (Con cái/Người thân).
AppSharedBloc: Load Header & Profile User.
Navigation Structure:
Tab 0: VaccineHomeView (Tổng quan).
Tab 1: VaccinationRecordPage (Sổ tiêm National).
Tab 2: CalendarPage (Lịch tiêm).
Tab 3: ProfileDetailPage (Chi tiết hồ sơ).
📍 MODULE: KHLC-FINDING-STORE
🚩 Screen: FindingStoreMainView
Identifier: FindingStoreMainView | Path: khlc-finding-store/lib/src/features/finding_store/presentation/view/finding_store_main_view.dart
Logic Controllers:
FindingStoreBloc: Quản lý danh sách nhà thuốc.
MapsController: Điều khiển Google Maps.
Location Logic:
Gọi AppTrackingService.checkLocationPermission() khi khởi tạo.
Nếu thành công -> Lấy LatLng hiện tại -> RequestCurrentLocationPermission.
Nếu từ AddressResult -> FindingStoreByAddressEvent.
🏠 MODULE: HOME (CURRENT REPO)
🚩 Screen: HomeView
Identifier: HomeView | Path: lib/src/features/home/presentation/views/home_view.dart
Logic Controllers:
HomeConfigBloc: Quản lý cấu trúc các section trên trang chủ.
GlobalConfigBloc: Quản lý cấu hình chung (Background, Colors).
ConnectionBloc: Theo dõi trạng thái mạng.
Data Flow (Triggers):
initState: Đăng ký SnowPlow tracking, set up ScrollDepthTracker.
onRefresh: Gọi HomeFetchDataService.fetchAll() để làm mới toàn bộ data trang chủ.
HomeConfigDoneState: Render HomeContent với danh sách visibleSections.
Business Rules:
Dynamic Background: Tẩy background từ GlobalConfigBloc.backgroundUrl, fallback về asset bgAppbar.
Unauthenticated Flow: Nếu chưa đăng nhập (unauthenticated) -> Gọi AppAuth.inst.login() khi vào Home.
Skeleton & Offline: Nếu mất mạng -> Hiện DisconnectView. Nếu đang load -> Hiện HomeBodySkeleton.
Insider Tracking: Gọi FlutterInsider.Instance.visitHomePage() mỗi khi screen được active (Push/PopNext).
Navigation:
HomeFloatyNavigationButton: Nút điều hướng nổi đặc trưng.
Các section (Banner, Shortcuts, Flash Sale, etc.) được xây dựng động thông qua HomeContent.
📊 MODULE: DASHBOARD (SHELL)
🚩 Screen: DashboardPage
Identifier: DashboardPage | Path: lib/src/features/dashboard/presentations/dashboard_page.dart
Logic Controllers:
GlobalConfigBloc: Xử lý UI Mode (Main/Lite) và Text Scaling.
VersionFlagBloc: Kiểm tra Intro flag cho Onboarding.
DashboardTabFactory: Quản lý Tab navigation (Home, Category, Search, Profile, etc.).
LifeCycle (Services):
Sync Tasks: Thực thi SynchronousServices (Version, ChildWarrior, Noti, AppLink).
Async Tasks: Chạy nền AsynchronousServices (HomeData, Connection, Counter, etc.).
Business Rules:
LiteApp Mode: Nếu data từ Onboarding có liteAppConfigure -> Tự động chuyển UIMode.main sang mode lite tương ứng.
DeepLink Routing: DashboardModule sử dụng Modular.args.data để config theme/mode ngay tại route level trước khi build Page.
Cập nhật lần cuối: 02/04/2026 - Sync Dashboard & Long Description Logic
