---
inclusion: manual
---

# KHLC SnowPlow DC5 Tracking Flow

## Nguyên tắc
- Mỗi event tracking phải đi qua token method tương ứng trong `khlc_core`.
- UI/widget không gọi trực tiếp `tracking()` hoặc `filledParam()`.
- Nếu event chưa có token method, thêm method vào đúng screen token trước.
- `Param: Basic` nghĩa là không truyền thêm param ở call-site; token sẽ tự fill Basic mặc định.
- Chỉ truyền `Dc5Param` khi ticket yêu cầu field cụ thể ngoài Basic.
- Chọn đúng `Dc5*Model` theo schema/param được yêu cầu, không mặc định mọi param đều đưa vào `Dc5BasicModel`.

## Flow chuẩn
1. Xác định `screen_location` của event.
2. Tìm screen token tương ứng trong `KHLCSnowPlowDc5`.
3. Kiểm tra event đã có method trong token class chưa.
4. Nếu chưa có, thêm method event vào đúng token class trong `khlc_core`.
5. Call-site chỉ gọi token method.

## Token method
```dart
Future<void> clickExampleEvent([
  Dc5Param Function()? paramBuilder,
]) =>
    tracking(
      () => filledParam(
        eventName: 'click_example_event',
        paramBuilder: paramBuilder,
      ),
    );
```

## Dc5Param
```dart
Dc5Param({
  Dc5BaseModel? data,
  Dc5BasicModel basic = const Dc5BasicModel(),
  List<Dc5BaseModel> contexts = const [],
})
```

- `data`: schema chính của event, thường dùng `Dc5ProductModel`, `Dc5EcomModel`, `Dc5SearchModel`.
- `basic`: context basic chung, token tự fill `event_name`, `screen_location`, `location_type`.
- `contexts`: context phụ đi kèm event nếu ticket yêu cầu.

## Các Dc5 Model dùng chính
- `Dc5BasicModel`: basic context chung như `screen_location`, `location_name`, `location_type`, `click_text`, `label`, `value`, `conversation_id`.
- `Dc5ProductModel`: schema `product`, dùng cho product/category fields.
- `Dc5EcomModel`: schema `ecommerce`, dùng cho order/cart/ecommerce fields; item dùng `Dc5EcomItem`.
- `Dc5SearchModel`: schema `search`, dùng cho search value/result/index/total.

## Cách chọn model
- Ticket ghi `Param: Basic`: gọi token method không truyền `Dc5Param`.
- Ticket yêu cầu field nằm trong Basic: truyền `Dc5Param(basic: Dc5BasicModel(...))`.
- Ticket yêu cầu schema riêng như `product`, `search`, `ecommerce`: truyền model đó vào `data`.
- Ticket yêu cầu thêm context phụ: truyền model vào `contexts`.
- Nếu chưa chắc field thuộc model nào, đọc file model trong `khlc-core/lib/src/services/analytics/snowplow_dc5/model/` trước.

## Call-site Basic
```dart
KHLCSnowPlowDc5.exampleToken.clickExampleEvent();
```

## Call-site có Basic field bổ sung
```dart
KHLCSnowPlowDc5.exampleToken.clickExampleEvent(
  () => Dc5Param(
    basic: Dc5BasicModel(clickText: clickText),
  ),
);
```

## Call-site có data schema riêng
```dart
KHLCSnowPlowDc5.exampleToken.clickExampleEvent(
  () => Dc5Param(
    data: Dc5ProductModel(productId: productId),
  ),
);
```

## Lưu ý
- Không hardcode `screen_location` ở widget nếu token đã tự fill được.
- Không tạo helper tracking riêng trong UI nếu token method đã đủ dùng.
- Không sửa generated files (`.g.dart`) cho tracking.
