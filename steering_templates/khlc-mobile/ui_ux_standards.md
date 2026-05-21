---
inclusion: manual
---

Quy chuẩn Giao diện & UX (UI/UX Standards) - KHLC-Mobile
🎨 1. Hệ thống Màu sắc (Design Tokens - Colors)
TUYỆT ĐỐI KHÔNG sử dụng mã màu cứng. Luôn dùng AliasColor hoặc NeutralColor.

🗂 Bảng đối chiếu Figma-to-Code Mapping
Hex Code (Design)	Color Name (Core)	Code Property (Alias)	Vai trò
#FFFFFF	NeutralColor.white	AliasColor.background.white, layer.white	Nền trắng chủ đạo
#020B27	NeutralColor.gray10	AliasColor.text.primary, AliasColor.icon.black	Văn bản chính, tiêu đề (Black)
#1250DC	PrimaryColor.blue5	AliasColor.text.link, AliasColor.text.focus, AliasColor.icon.primary	Màu nhấn thương hiệu, links
#4A4F63	NeutralColor.gray7	AliasColor.text.secondary	Văn bản mô tả phụ (Grey)
#728091	NeutralColor.gray6	AliasColor.text.tertiary, AliasColor.text.placeholder, AliasColor.icon.secondary	Văn bản mờ, placeholder
#EDF0F3	NeutralColor.gray1_5	AliasColor.background.gray, AliasColor.layer.gray	Nền xám nhạt (Lọc/Section)
#F6F7F9	NeutralColor.gray1	AliasColor.background.graySecondary	Nền xám rất nhạt
#D92D20	ErrorColor.red8	AliasColor.semantic.error	Màu thông báo lỗi
#039855	SuccessColor.green8	AliasColor.semantic.success	Màu thông báo thành công
#F79009	WarningColor.yellow7	AliasColor.semantic.warning	Màu thông báo cảnh báo
✍️ 2. Hệ thống Kiểu chữ (Typography - AppStyle)
Bắt buộc sử dụng class AppStyle với các biến thể bold, semi, medium, regular.

Style Class	Font Size	Line Height	Cách dùng
Title1	36px	52 / 36	Màn hình giới thiệu, Hero Title lớn
Title2	28px	40 / 28	Tiêu đề màn hình đặc biệt
Title3	24px	36 / 24	Tiêu đề trang quan trọng
Title4	32px	40 / 32	Tiêu đề nổi bật lớn
Heading1	24px	36 / 24	Tiêu đề nhóm nội dung cấp 1
Heading2	20px	28 / 20	Tiêu đề nhóm nội dung cấp 2
Heading3	18px	24 / 18	Tiêu đề nhóm nội dung cấp 3
Body1	16px	24 / 16	Văn bản nội dung (mặc định)
Body2	14px	20 / 14	Văn bản nội dung (nhỏ hơn, card)
Label1	16px	24 / 16	Text trong Buttons, Labels
Label2	14px	20 / 14	Text trong Chips, Tags
Caption1	12px	16 / 12	Ghi chú nhỏ, phụ đề ảnh
Caption2	13px	18 / 13	Ghi chú trung bình
📏 3. Bố cục & Khoảng cách (Layout & Spacing)
Sử dụng KHLCSpacing (extension on double) thay cho SizedBox và EdgeInsets trực tiếp.

Các giá trị spacing có sẵn:
KHLCSpacing.small2 (2px), small3 (3px), small4 (4px), small6 (6px)
KHLCSpacing.small8 (8px), small10 (10px), small12 (12px), small14 (14px), small16 (16px)
KHLCSpacing.medium20 (20px), medium24 (24px), medium28 (28px)
KHLCSpacing.large32 (32px), large42 (42px), large48 (48px), large64 (64px)

Cú pháp Spacing:
KHLCSpacing.small8.verticalSpacing    → SizedBox(height: 8)
KHLCSpacing.small8.horizontalSpacing  → SizedBox(width: 8)
KHLCSpacing.small8.squaredSpacing     → SizedBox(height: 8, width: 8)

Cú pháp Padding (đầy đủ):
.paddingAll, .paddingHorizontal, .paddingVertical
.paddingLeft, .paddingRight, .paddingTop, .paddingBottom
.paddingTopLeft, .paddingTopRight, .paddingBottomLeft, .paddingBottomRight

📐 4. Bo góc (Border Radius)
Sử dụng KHLCRadius thay cho BorderRadius.circular() trực tiếp.

KHLCRadius.none   → 0px
KHLCRadius.small  → 2px
KHLCRadius.medium → 4px
KHLCRadius.large  → 8px
KHLCRadius.full   → 1000px (pill/circle shape)

🌑 5. Đổ bóng (Shadow)
Sử dụng KHLCShadow thay cho BoxShadow trực tiếp.

KHLCShadow.up   → Shadow hướng lên (dùng cho bottom sheet, sticky footer)
KHLCShadow.down → Shadow hướng xuống (dùng cho card, header)

🎨 6. AliasColor — Đầy đủ từ source code

AliasColor.background:
  .white, .newWhite, .blue, .gray, .graySecondary

AliasColor.bgOverlay:
  .primary (NeutralColor.gray10), .secondary (NeutralColor.gray10)

AliasColor.layer:
  .white, .gray, .blue1, .blue3, .red2, .red3, .yellow, .green, .onBlue, .gradient1

AliasColor.stroke:
  .$default (NeutralColor.gray4), .disable (NeutralColor.gray2), .focus (PrimaryColor.blue5)

AliasColor.divider:
  .$1pt (NeutralColor.gray2), .$1ptPrimary (PrimaryColor.blue5)

AliasColor.field:
  .defaultGray (NeutralColor.gray1_5), .defaultWhite, .active, .disable (NeutralColor.gray2)

AliasColor.text:
  .primary, .secondary, .tertiary, .white, .placeholder, .disable
  .hintTextGrey (NeutralColor.gray5), .hintTextWhite (NeutralColor.gray3)
  .focus (PrimaryColor.blue5), .link (PrimaryColor.blue5)

AliasColor.icon:
  .primary, .black, .secondary, .tertiary, .tertiary2, .white, .gradient, .gradient2

AliasColor.semantic:
  .error, .errorGradient, .errorDisable, .success, .successGradient, .warning, .warningGradient

AliasColor.button:
  .primaryActive (gradient), .primaryPressed, .secondaryActive, .secondaryPressed
  .textButtonPressed, .disable, .iconButton

🎨 7. Màu Gradient
Sử dụng GradientColor thay cho LinearGradient trực tiếp.

GradientColor.blue1  → #306de4 → #1250dc (Primary gradient)
GradientColor.blue2  → #769dea → #306de4
GradientColor.blue3  → #acc0f3 → #769dea
GradientColor.blue4  → #D3DFF9 → #E5EEFF (Light gradient)
GradientColor.green1 / green2 → #12b76a → #039855
GradientColor.yellow1 / yellow2 → #fdb022 → #f79009
GradientColor.red1 / red2 → #f04438 → #d92d20

🧩 8. Thành phần Lõi (Core Components)

AppBar/Header: Luôn dùng HeaderLv1Title(title: 'Tên trang').
Hình ảnh: Dùng AppNetworkPicture(url: ..., placeholderBuilder: (context) => ...).

Nút bấm (đầy đủ):
AppPrimaryButton       → Nút chính (gradient blue)
AppSecondaryButton     → Nút phụ (outline blue)
AppPrimaryWhiteButton  → Nút chính nền trắng
AppSecondaryGreenButton → Nút xanh lá
AppTextButton          → Text button
AppPrimaryTextButton   → Text button màu primary
AppIconButton          → Nút icon
AppOutlineButton       → Nút viền
AppOrderButton         → Nút đặt hàng
AppQrButton            → Nút QR

Button sizes (ButtonSize enum):
ButtonSize.size48 → Label1.medium, padding vertical 12
ButtonSize.size40 → Label2.medium, padding vertical 10
ButtonSize.size36 → Label2.medium, padding vertical 8
ButtonSize.size28 → Label2.medium, padding vertical 4

Popup/Dialog:
AppConfirmPopup, AppCustomPopup, AppGifPopup
AppImagePopup, AppImageComfirmPopup
AppOptionPopup, AppDynamicOptionPopup

TextField:
AppTextFieldHint, AppTextFieldLabel, AppTextFieldGray
AppTextArea, AppSearchView

Các widget khác:
AppDivider, AppVerticalDivider
AppCheckbox, AppRadioButton, AppSwitch
SlideCountDown (đếm ngược Flash Sale)
AppToast, AppToastV2, NotiToast (thông báo nhanh)
AppBadge, AppBadgeBuilder (badge số lượng)
SkeletonWidgets (AppSkeleton, TextSkeleton, ImageSkeleton)
AppInputSpinner, VoucherInputSpinner (tăng/giảm số lượng)
ExpandableWidget (mở rộng/thu gọn)
InformationTile, TextTile (hiển thị key-value)
BottomSheetActionPanel (action panel trong bottom sheet)
FlexibleHeader (header linh hoạt)
VoucherChip (chip voucher với custom clipper)
AppFilterChip, AppSelectableChip, SortRoundedChip (filter/sort chips)
RoundedChipTemplate<T> (chip template generic)
ImageSliderView (slider ảnh)
BaseCarouselSlider (carousel)
AppGifImages (hiển thị GIF)
MarqueeText (text chạy)
WalkthroughWidget (hướng dẫn sử dụng)

Hành động: GestureDetector thường kết hợp với KHLCAnalytics để tracking log.

🆕 10. Lite Design System (UIMode.lite)
Khi app ở UIMode.lite, sử dụng hệ thống token từ `src_lite/`:

**LiteSpacing** (enum-based, giá trị mở rộng hơn KHLCSpacing):
LiteSpacing.none(0), s2(2), s4(4), s6(6), s8(8), s10(10), s12(12), s16(16)
s20(20), s24(24), s28(28), s32(32), s36(36), s40(40), s48(48), s56(56), s64(64)
s80(80), s96(96), s100(100), s120(120)
Cú pháp: `LiteSpacing.s16.verticalSpacing`, `.horizontalSpacing`, `.paddingAll`, etc.

**LiteRadius** (enum-based, nhiều level hơn):
LiteRadius.none(0), r2xs(2), rXs(4), rSm(8), rMd(12), rLg(16), rXl(20), r2xl(24), fill(999)
Cú pháp: `LiteRadius.rSm.borderRadiusAll`, `.borderRadiusTop`, `.borderRadiusBottom`, `.borderRadiusLeft`, `.borderRadiusRight`

**LiteShadow** (enum-based, nhiều variant):
LiteShadow.xs, .sm, .md, .lg, .navigationBar, .handle, .tooltip, .floatIcon
Cú pháp: `LiteShadow.sm.boxShadows`

**LiteButton** (naming convention: `LBtn{Size}{Style}{Color}`):
Sizes: Xs, Sm, Md, Lg, Xl
Styles: Filled, Outlined, Text
Colors: Primary, Secondary, Gray, White, Destructive
Icon buttons: `LBtnIcon{Size}{Style}{Color}`
Ví dụ: `LBtnMdFilledPrimary(onPressed: ..., child: Text('Label'))`

**LiteTextField**: LTextFieldLG, LTextFieldMD, LTextFieldSM, LTextFieldXS
Variations: LTextFieldPasswordLG, LTextFieldSuffixCloseLG

**LiteTypography**: `LiteTextStyles` với `LiteTypographyScale` + `LiteTypographyWeight`

⚠️ Quy tắc: Nếu app đang ở UIMode.main → dùng KHLCSpacing/KHLCRadius/KHLCShadow/AppPrimaryButton.
Nếu UIMode.lite → dùng LiteSpacing/LiteRadius/LiteShadow/LBtn*.
KHÔNG trộn lẫn 2 hệ thống trong cùng 1 widget.

Cập nhật lần cuối: 21/05/2026 - Sync đầy đủ từ khlc-ui source code (bổ sung AliasColor, Lite DS, widgets)

📐 9. Responsive Sizing (.sc() extension)
Tất cả kích thước số cứng (width, height, icon size, radius cụ thể) PHẢI dùng extension `.sc()` để scale theo màn hình.

Ví dụ đúng:
```dart
Container(width: 28.sc(), height: 28.sc())
Icon(Icons.close, size: 16.sc())
SizedBox(width: 56.sc())
```

Ví dụ SAI:
```dart
Container(width: 28, height: 28)  // ← KHÔNG dùng số cứng
Icon(Icons.close, size: 16)       // ← KHÔNG dùng số cứng
```

Ngoại lệ — KHÔNG cần .sc():
- Các giá trị từ KHLCSpacing (vd: KHLCSpacing.small16) — đã handle bên trong
- Các giá trị từ KHLCRadius (vd: KHLCRadius.large) — đã handle bên trong
- Font size trong AppStyle (vd: Body2.medium) — đã handle bên trong

Cập nhật lần cuối: 06/05/2026 - Thêm rule .sc() responsive sizing
