---
inclusion: manual
---

🧠 UseCase Registry (Bản đồ Logic nghiệp vụ)
Tài liệu này liệt kê các "động cơ" (UseCase) chính của 12 module. Đây là lớp thông tin quan trọng nhất để AI có thể tự triển khai logic nghiệp vụ đúng chuẩn 100%.

🏗️ 1. Module Sản phẩm (Product Detail Logic)
UseCase Name	Input (Parameters)	Output (Return)	Purpose
GetProductDetailUseCase	sku (String)	ProductDetailEntity	Lấy thông tin chi tiết sản phẩm.
GetProductPromotionUseCase	pimCategoryId, sku	PromotionEntity	Lấy CTKM đang áp dụng cho SKU.
PostRatingsUseCase	sku, score, content	bool	Gửi đánh giá sản phẩm.
GetProductPacksUseCase	sku, limit, offset	List<PackEntity>	Lấy danh sách combo/pack.
🛒 2. Module Giỏ hàng & Mua hàng (Cart Logic)
UseCase Name	Input (Parameters)	Output (Return)	Purpose
AddProductsToCartUseCase	sku, quantity, unitCode	CartEntity	Thêm sản phẩm vào giỏ hàng.
BuyNowProdsListUseCase	List<ItemParams>	PaymentMethodsArgs	Luồng "Mua ngay" - bỏ qua giỏ hàng.
CheckFsellPolicyUseCase	CartEntity	bool	Kiểm tra chính sách tích điểm Fsell.
💳 3. Module Thanh toán (Payment Logic)
UseCase Name	Input (Parameters)	Output (Return)	Purpose
CheckPaymentStatusUseCase	orderCode, paymentCode	PaymentStatus	Kiểm tra trạng thái thực tế đơn hàng.
GetPaymentMethodUseCase	ItemParams	List<PaymentMethod>	Lấy danh sách PTTT khả dụng.
MomoPaymentUseCase	orderCode, amount	momo_url (String)	Tạo link thanh toán Momo.
ZaloPayPaymentUseCase	orderCode, amount	zalopay_url (String)	Tạo link thanh toán ZaloPay.
🔐 4. Module Xác thực & Thông báo (Auth & Registry)
UseCase Name	Input (Parameters)	Output (Return)	Purpose
AppLoginUseCase	phone, otp	UserInfo	Xử lý đăng nhập & đồng bộ giỏ hàng.
AppLogoutUseCase	-	bool	Xử lý đăng xuất & xóa session.
InitialDeepLinkUseCase	Uri	RouteName	Phân tích link và trả về route cần đi.
🚀 5. Các UseCase dùng chung (Shared Logic)
CheckVersionUseCase: Kiểm tra phiên bản mới nhất từ backend.
GetCurrentLocationUseCase: Lấy tọa độ GPS người dùng (cho module Finding Store).
GetCountUnreadMessagesUsecase: Lấy số lượng thông báo chưa đọc.
IMPORTANT

Luôn sử dụng UseCase thay vì gọi trực tiếp Repository để đảm bảo đúng quy tắc Clean Architecture của dự án. AI cũng cần tuân thủ việc Inject UseCase thông qua hàm Modular.get<T>().

TIP

Nếu bạn cần viết một luồng "Xác nhận đơn hàng", hãy kết hợp chuỗi: AddProductsToCartUseCase ➡️ BuyNowProdsListUseCase ➡️ GetPaymentMethodUseCase.
