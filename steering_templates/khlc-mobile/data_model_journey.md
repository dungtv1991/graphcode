---
inclusion: manual
---

🔄 Data Flow & Model Journey (Bản đồ đường đi dữ liệu)
Tài liệu này ghi nhận cách các Model cốt lõi biến đổi khi đi xuyên qua các module khác nhau. Điều này giúp AI hiểu được sơ đồ map dữ liệu mà không cần đọc lại toàn bộ định nghĩa class.

🛍️ 1. Luồng Sản phẩm & Đơn hàng (Product to Order Flow)
Luồng đi: Product Module ➡️ Cart Module ➡️ Payment Module

A. Giai đoạn: Xem Sản phẩm (ProductDetailEntity)
Cấu trúc quan trọng tại khlc_product:

sku: Mã định danh sản phẩm.
units: Danh sách đơn vị tính (ProductPriceEntity).
unitDefault: Đơn vị mặc định (chứa price, isInventory).
isPrescription: Flag thuốc kê đơn (Nếu true sẽ chặn mua nhanh).
B. Giai đoạn: Chốt đơn (PaymentMethodsArgs / ItemParams)
Khi từ giỏ hàng sang xác nhận thanh toán, dữ liệu được "thu gọn" thành:

ItemParams:
sku: String
quantity: int
price: num
unitCode: int
C. Giai đoạn: Thanh toán (OrderCreatedInfo)
Sau khi API Create Order thành công, dữ liệu chuyển hóa thành:

orderCode: Mã đơn hàng (dùng để tra cứu lịch sử).
paymentCode: Mã giao dịch thanh toán.
paymentLink: Link thanh toán (VNPay/Momo) nếu có.
🔔 2. Luồng Thông báo & Hành động (Notification Flow)
Luồng đi: Push Notification / DeepLink ➡️ Shell App ➡️ Guest Module

A. Raw Data (DeepLink/Payload)
json
{
  "notificationId": "123",
  "type": "order-detail",
  "id": "ORD_001",
  "de-inbound": "tracking_token"
}
B. Transformation (DeepLinkDelegate)
type: order-detail ➡️ Map sang route /order-detail.
id ➡️ Chuyển thành tham số orderCode.
de-inbound ➡️ Chuyển thành tham số token (dùng cho Snowplow tracking).
👤 3. Luồng Cấu hình & Trạng thái (Config Flow)
Luồng đi: Shell App (GlobalConfig) ➡️ Content/Dashboard Module

A. Global State (GlobalConfigEntity)
uiMode: main hoặc lite (Dùng để thay đổi giao diện toàn app).
backgroundUrl: Hình nền AppBar động.
textScaler: Cấp độ phóng to chữ (1.0, 1.2, 1.5).
B. Content Integration (UserInterfaceConfig)
Module Content nhận các giá trị này để render WebView hoặc Text chính xác theo cấu hình của người dùng.

📉 Summary of Key Models Mapping
Model Gốc	Module Đích	Model Chuyển hóa	Key Fields mapping
ProductDetailEntity	Cart	CartItem	sku, selectUnit.unitCode, price
CartEntity	Payment	PaymentMethodsArgs	items, orderCode, promotionInfos
OrderCreatedInfo	History	OrderDetailEntity	orderCode, paymentCode
TIP

Khi cần code một tính năng "Mua ngay" từ màn hình chi tiết sản phẩm, hãy đảm bảo map đúng sku và unitCode từ ProductDetailEntity sang ItemParams của PaymentMethodsArgs.
