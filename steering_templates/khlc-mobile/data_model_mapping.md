---
inclusion: manual
---

🏦 DATA MODEL MAPPING - FULL SYNC
Tài liệu này lưu trữ cấu trúc các Data Model và Entity quan trọng nhất của hệ sinh thái KHLC, được trích xuất trực tiếp từ mã nguồn để AI truy vấn nhanh mà không cần quét lại toàn bộ folder.

🛒 MODULE: KHLC-PRODUCT
Module này quản lý toàn bộ logic liên quan đến sản phẩm, chi tiết sản phẩm, và danh sách sản phẩm.

🚩 Feature: product_detail
Đây là feature phức tạp nhất, chứa thông tin đầy đủ về một sản phẩm từ PIM.

📄 ProductDetailEntity
Identifier: ProductDetailEntity | Path: khlc-product/lib/src/features/product_detail/domain/entities/product_detail_entity.dart
Key Fields:
sku: String? (Unique SKU của sản phẩm)
name: String? (Tên hiển thị)
ingredientFor: String? (DSIP-632: Lượng định mức như 10ml, 5mg... dùng làm tiền tố thành phần)
ingredient: List<IngredientEntity> (Danh sách thành phần chi tiết)
units: List<ProductPriceEntity> (Các đơn vị quy đổi như Hộp, Vỉ, Viên)
basicInfo: ProductBasicInfoEntity (Ảnh, Slug, Rating)
shortDescriptionMap: Map<String, dynamic> (Dữ liệu thô từ PIM cho các thuộc tính bổ sung)
📄 ProductPriceEntity
Identifier: ProductPriceEntity | Path: khlc-product/lib/src/features/product_detail/domain/entities/product_price_entity.dart
Key Fields:
unitCode: String?
unitName: String?
price: double? (Giá cuối cùng sau khi tính toán)
originalPrice: double? (Giá niêm yết)
isInventory: bool? (Trạng thái còn hàng)
📄 IngredientEntity
Identifier: IngredientEntity | Path: khlc-product/lib/src/features/product_detail/domain/entities/product_detail_entity.dart
Key Fields:
name: String?
shortDescription: String?
slug: String? (Dùng để deep link sang trang thành phần chi tiết)
📄 QuotasFlashSaleEntity
Identifier: QuotasFlashSaleEntity | Path: khlc-product/lib/src/features/product_detail/domain/entities/quotas_flashsale_entity.dart
Key Fields:
totalQuantity: int (Tổng suất Flash Sale)
usedQuantity: int (Số lượng đã bán/chiếm chỗ)
currentQuantity: int (Số lượng còn lại khả dụng)
Business Rule: Nếu totalQuantity == usedQuantity -> Sản phẩm Flash Sale sẽ báo Sold Out/Hết suất ưu đãi.
📄 ProductAttributeEntity
Identifier: ProductAttributeEntity | Path: khlc-product/lib/src/features/product_detail/domain/entities/product_attribute_entity.dart
Key Fields:
rank: int? (Thứ tự hiển thị thuộc tính)
name: String? (Tên hiển thị: Ví dụ "Thành phần", "Cách dùng")
key: String? (Enum key để mapping với widget builder)
📄 ProductPromotionItemEntity
Identifier: ProductPromotionItemEntity | Path: khlc-product/lib/src/features/product_detail/domain/entities/product_promotion_entity.dart
Key Fields:
promotionCode: String?
promotionName: String?
urlImage: String? (Ảnh banner chương trình khuyến mãi)
📄 ProductLongDescriptionEntity
Identifier: ProductLongDescriptionEntity | Path: khlc-product/lib/src/features/product_detail/domain/entities/product_long_description_entity.dart
Key Fields:
items: List<MapEntry<String, dynamic>> (Danh sách các phần mô tả như Chỉ định, Cách dùng, Bảo quản...)
ingredientFor: String? (Đồng bộ với ProductDetailEntity để render tiêu đề/prefix)
approver: Approver (Thông tin người duyệt bài viết)
🚩 Feature: products (Search & List)
📄 ProductEntityV2
Identifier: ProductEntityV2 | Path: khlc-product/lib/src/features/products/domain/entities/product_entity_v2.dart
Key Fields:
sku: String
displayName: String
imageUrl: String?
displayCode: int (Dùng để quyết định có hiển thị giá hay không)
brand: String?
categories: List<Category>
units: List<UnitEntityV2> (Chứa thông giá và khuyến mãi)
📄 ImageSearchResultEntity
Identifier: ImageSearchResultEntity | Path: khlc-product/lib/src/features/image_search/domain/entities/image_search_result_entity.dart
Key Fields:
engine: ImageSearchEngine (Cơ chế tìm kiếm: Image, Voice, Prescription...)
total: int
productList: List<ProductEntityV2>
productsGroup: List<ImageSearchGroupResult>
🚩 Feature: product_suggestion
📄 ProductSuggestionEntity
Identifier: ProductSuggestionEntity | Path: khlc-product/lib/src/features/product_suggestion/domain/entities/product_sugeestion.dart
Key Fields:
totalCount: int?
items: List<String>? (Danh sách các từ khóa gợi ý)
🛒 MODULE: KHLC-CART
Tài liệu này lưu trữ các Entity cốt lõi cho giỏ hàng.

🚩 Feature: cart
📄 CartEntity
Identifier: CartEntity | Path: khlc-cart/lib/src/features/cart/domain/entities/cart_entity.dart
Key Fields:
cart: List<CartItemEntity> (Các item đã chọn)
customer: List<CartItemEntity> (Các item chưa chọn)
gifts: List<CartItemEntity> (Quà tặng)
priceInfoEntity: PriceInfoEntity? (Thông tin giá tổng)
loyalty: double (Điểm thưởng fsell)
policy: CartRestrictPolicy? (Chính sách giới hạn bán)
📄 CartItemEntity
Identifier: CartItemEntity | Path: khlc-cart/lib/src/features/cart/domain/entities/cart_item_entity.dart
Key Fields:
product: ProductEntity? (Thông tin sản phẩm cơ bản)
quantity: int?
currentUnit: UnitEntity?
priceInfoEntity: DetailPriceInfoEntity? (Giá chi tiết cho từng item)
isSelected: bool
📄 PriceInfoEntity
Identifier: PriceInfoEntity | Path: khlc-cart/lib/src/features/cart/domain/entities/price_info_entity.dart
Key Fields:
total: double? (Tổng tiền hàng)
totalBill: double? (Thành tiền)
shipmentPrice: double? (Phí ship)
totalDiscount: double? (Giảm giá trực tiếp)
totalVoucherPrice: double? (Giảm giá voucher)
📦 MODULE: KHLC-ORDER
Xử lý thông tin đơn hàng và theo dõi trạng thái.

🚩 Feature: order_detail
📄 OrderDetailEntity
Identifier: OrderDetailEntity | Path: khlc-order/lib/src/features/order_detail/domain/entities/order_detail_entity.dart
Key Fields:
orderCodeDisplay: String?
orderDate: DateTime?
orderStatus: OrderStatusEntity? (Enum: processing, delivering, canceled, returned)
orderStatusDisplay: String?
shipment: OrderShipmentEntity?
products: List<OrderProductEntity>?
payment: List<OrderPaymentEntity>?
💳 MODULE: KHLC-PAYMENT
Quản lý luồng thanh toán và phương thức chọn lựa.

🚩 Feature: payment_methods
📄 OrderCreatedInfo
Identifier: OrderCreatedInfo | Path: khlc-payment/lib/page/payment_methods/domain/entities/order_created_info.dart
Key Fields:
orderCode: String?
paymentCode: String?
paymentLink: String? (Dùng để webview thanh toán VnPay/Momo)
qrInfo: QRInfoModel? (Dùng để parse và render mã QR thanh toán)
📄 PaymentMethodArgumentEntity
Identifier: PaymentMethodArgumentEntity | Path: khlc-payment/lib/page/payment_methods/domain/entities/payment_method_args.dart
Key Fields:
paymentMethod: PaymentMethodModel? (Phương thức đã chọn: Momo, VnPay, COD)
selectedCardEntity: PaymentSavedCardModel? (Thông tin thẻ đã lưu nếu có)
isSavingCard: bool (User có chọn lưu thẻ cho lần sau không)
🔐 MODULE: KHLC-AUTHENTICATION
Quản lý định danh và phiên đăng nhập.

🚩 Feature: login_section
📄 LoginMethodEntity
Identifier: LoginMethodEntity | Path: khlc-authentication/lib/src/features/login_section/domain/entities/login_method_entity.dart
Key Fields:
method: String (google, facebook, apple, phone)
isEnabled: bool
👤 MODULE: KHLC-PROFILE
Thông tin cá nhân và thiết lập tài khoản.

🚩 Feature: user_info
📄 UserInfoProfileEntity
Identifier: UserInfoProfileEntity | Path: khlc-profile/lib/src/features/user_info/domain/entities/user_info_entity.dart
Key Fields:
customerId: String?
fullName: String?
phoneNumber: String?
avatar: String?
qrCode: String? (Mã QR định danh khách hàng)
🔔 MODULE: KHLC-NOTIFICATION
Hệ thống thông báo và tin nhắn trong ứng dụng.

🚩 Feature: list_notification
📄 ItemNotificationEntity
Identifier: ItemNotificationEntity | Path: khlc-notification/lib/src/list_notification/domain/entities/item_notification_entity.dart
Key Fields:
id: String?
title: String?
body: String?
isRead: bool
creationTime: DateTime?
🏠 MODULE: KHLC-MOBILE (MAIN REPO)
Các tính năng cốt lõi của Shell App.

🚩 Feature: home
📄 HomeConfigureEntity
Identifier: HomeConfigureEntity | Path: khlc-mobile/lib/src/features/home/domain/entities/home_configure/home_configure_entity.dart
Key Fields:
sections: List<HomeSectionEntity> (Danh sách các section động trên Home)
backgroundFooter: String
📄 HomeSectionEntity
Identifier: HomeSectionEntity | Path: khlc-mobile/lib/src/features/home/domain/entities/home_configure/home_section.dart
Key Fields:
code: String (Identifier của section: shortcut, banner, flash_sale...)
isVisible: bool
elements: List<HomeElementEntity> (Dữ liệu con trong mỗi section)
🚀 Cập nhật tự động (Auto-Update Policy)
Mọi thay đổi tiếp theo đối với cấu trúc Model/Entity trong mã nguồn PHẢI được cập nhật ngay lập tức vào tài liệu này để duy trì sự nhất quán của Bộ não (Project Brain).

Cập nhật lần cuối: 01/04/2026 - Final Sync across All Modules
