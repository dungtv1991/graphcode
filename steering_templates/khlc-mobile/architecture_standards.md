---
inclusion: manual
---

Quy chuẩn Kiến trúc KHLC-Mobile (Architecture Standards)
🚨 0. BẮT BUỘC: GIAO THỨC TRUY VẤN BỘ NÃO (BRAIN FIRST PROTOCOL)
Trước khi thực hiện bất kỳ yêu cầu sửa code, phân tích hay tạo mới nào, AI PHẢI thực hiện các bước sau:

Truy vấn Screen Map: Đọc screen_business_logic.md để hiểu luồng nghiệp vụ của màn hình/module liên quan.
Truy vấn Code Standard: Đọc architecture_standards.md (file này) để đảm bảo tuân thủ quy tắc đặt tên và cấu trúc Model/Entity.
Truy vấn UI Standard: Đọc ui_ux_standards.md để nắm vững AliasColor, AppStyle và KHLCSpacing (Bắt buộc khi code UI).
Đối chiếu thực tế: Chỉ sau khi nắm rõ "Lý thuyết" từ Bộ não, mới được phép đọc code thực tế để "Thực hành".
🏛 1. Kiến trúc Tổng thể (Core Arch)
Kiến trúc: Feature-first. Code nằm trong lib/src/features/.
Phân lớp: Tách biệt 3 lớp: Presentation (UI/Bloc), Domain (Entities), Data (Models/DataSources/Repos).
Hệ thống Plugin: Sử dụng flutter_modular để Dependency Injection (DI) và Routing.
🏷 2. Quy tắc Đặt tên (Naming Rules)
Class: PascalCase (vd: BrandItemWidget).
Biến/Hàm: camelCase (vd: getBrandList()).
Hệ thống Hậu tố (Naming Convention):
Chấp nhận song song 2 cách đặt tên: Dấu chấm (.) (Legacy/Standard) hoặc Dấu gạch dưới (_) (New/SnakeCase).
Widget: .widget.dart hoặc _widget.dart.
Screen/View: .screen.dart, .view.dart hoặc _view.dart, _screen.dart.
Model: .model.dart hoặc _model.dart.
Entity: .entity.dart hoặc _entity.dart.
UseCase: .usecase.dart hoặc _usecase.dart.
Repository: .repository.dart hoặc _repository.dart.
🏗 3. Mẫu Thiết kế Model & Entity (Modeling Pattern)
✅ Entity (Lớp Domain)
Bắt buộc: Phải kế thừa Equatable. Constructor const, thuộc tính final.
Logic: Không chứa Json annotations.
✅ Model (Lớp Data)
Bắt buộc: Phải kế thừa Entity tương ứng.
Annotation: Sử dụng @JsonSerializable(createToJson: false).
Quy tắc List: Bắt buộc dùng kiểu Model cho các List lồng nhau (vd: List<ProductModel>).
🚀 4. Quy trình Vận hành (Workflow)
Generation: Dùng lệnh terminal: dart run build_runner build --delete-conflicting-outputs.
Localization: dart run slang.
Cập nhật lần cuối: 01/04/2026 - Brain First Protocol Enabled
