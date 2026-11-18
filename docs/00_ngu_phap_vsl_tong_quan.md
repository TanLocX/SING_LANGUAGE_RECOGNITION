# TỔNG QUAN NGỮ PHÁP NGÔN NGỮ KÝ HIỆU VIỆT NAM (VSL)
=====================================================

Tài liệu này đóng vai trò là **kim chỉ nam ngôn ngữ học** giúp nhóm phát triển hiểu đúng cách tư duy của người Điếc/Khiếm thính, từ đó xây dựng bộ dữ liệu (dataset) và thuật toán dịch thuật (Sign Language Translation) chính xác.

---

## I. BẢN CHẤT CỐT LÕI CỦA NGÔN NGỮ KÝ HIỆU

1. **Không phải là "Tiếng Việt nói chuyển sang cử chỉ tay"**:
   - Ngôn ngữ Ký hiệu Việt Nam (VSL - Vietnamese Sign Language) là một **ngôn ngữ độc lập hoàn chỉnh**, có hệ thống từ vựng, ngữ pháp và cấu trúc không gian riêng biệt, không phụ thuộc vào tiếng Việt có dấu hay văn phạm ngữ pháp của tiếng nói.
2. **Ngôn ngữ Không gian - Thời gian - Hình ảnh (Spatial-Temporal Language)**:
   - Thay vì dùng âm thanh, VSL dùng không gian 3 chiều trước ngực (Signing Space), hướng di chuyển của bàn tay, và biểu cảm khuôn mặt/đầu (Non-Manual Signals).
3. **Gloss (Tên Ký hiệu Viết Hoa)**:
   - Mỗi cử chỉ ký hiệu tương ứng với một khái niệm, được quy ước viết bằng chữ in hoa không dấu hoặc có dấu nối: `XIN_CHAO`, `BAC_SI`, `DAU_DAU`.

---

## II. 5 QUY TẮC NGỮ PHÁP CƠ BẢN TRONG VSL

### 1. Quy tắc "Thời Gian Đặt Đầu Câu" (Time-First)
Trong tiếng Việt nói, từ chỉ thời gian có thể đứng đầu hoặc cuối câu, và động từ có các từ biểu thị thì (đã, đang, sẽ).  
Trong VSL, **từ chỉ thời gian luôn đứng ở vị trí đầu tiên** để thiết lập bối cảnh thời gian trước khi diễn ra hành động:
* *Tiếng Việt:* "Tôi đã đi khám bệnh hôm qua."
* *Ký hiệu VSL:* `HOM_QUA` + `TOI` + `KHAM_BENH` + `DI`

### 2. Cấu trúc "Chủ Đề - Thuyết Minh" (Topic - Comment)
Người Điếc luôn đưa **đối tượng/vật thể chính ra trước**, sau đó mới mô tả hành động, tính chất hoặc nhận xét:
* *Tiếng Việt:* "Cái áo này đắt quá."
* *Ký hiệu VSL:* `AO` + `NAY` + `DAT` + `QUA`
* *Tiếng Việt:* "Tôi thích ăn táo."
* *Ký hiệu VSL:* `TAO` + `TOI` + `THICH` + `AN`

### 3. Quy tắc "Từ Để Hỏi Luôn Đặt Cuối Câu" (Wh-Questions at End)
Trong câu hỏi, các từ như *Ở ĐÂU, MẤY GIỜ, GÌ, AI, BAO NHIÊU* hầu như luôn nằm ở **vị trí cuối câu**, kết hợp cùng biểu cảm nhíu mày hoặc rướn người về phía trước:
* *Tiếng Việt:* "Bao nhiêu tiền một cái bánh?"
* *Ký hiệu VSL:* `BANH` + `TIEN` + `BAO_NHIEU`?
* *Tiếng Việt:* "Nhà vệ sinh ở đâu?"
* *Ký hiệu VSL:* `NHA_VE_SINH` + `O_DAU`?
* *Tiếng Việt:* "Bạn tên là gì?"
* *Ký hiệu VSL:* `BAN` + `TEN` + `GI`?

### 4. Quy tắc "Từ Phủ Định Đặt Cuối Câu" (Negation at End)
Các từ phủ định như `KHONG`, `CHUA` thường đặt ở cuối cụm vị ngữ hoặc cuối câu, đi kèm với động tác lắc đầu:
* *Tiếng Việt:* "Tôi không hiểu bài này."
* *Ký hiệu VSL:* `BAI` + `NAY` + `TOI` + `HIEU` + `KHONG` *(kèm lắc đầu)*
* *Tiếng Việt:* "Tôi chưa uống thuốc."
* *Ký hiệu VSL:* `THUOC` + `TOI` + `UONG` + `CHUA`

### 5. Lược Bỏ Hoàn Toàn Hư Từ (Zero Stopwords)
VSL loại bỏ 100% các từ nối, giới từ, hư từ không mang tải thông tin hình ảnh:
- Loại bỏ: *thì, là, mà, ở, của, những, các, được, bị, sẽ, đã, v.v.*
* *Tiếng Việt:* "Bác sĩ của bệnh viện này rất nhiệt tình."
* *Ký hiệu VSL:* `BENH_VIEN` + `NAY` + `BAC_SI` + `NHIET_TINH`

---

## III. QUY ƯỚC ĐẶT TÊN THƯ MỤC TRONG DATASET (`DATA/dynamic/`)

Để đồng bộ với mã nguồn và thuật toán nhận diện, các thư mục cử chỉ trong `DATA/dynamic/` cần tuân thủ quy tắc:
1. **Viết thường, không dấu, nối bằng dấu gạch dưới `_`**:
   - Ví dụ: `dau_dau`, `uong_thuoc`, `xin_chao`, `bao_nhieu_tien`.
2. **Tránh đặt tên quá dài**: Tối đa 2 đến 3 từ ghép phản ánh đúng hành vi cử chỉ.
3. **Mỗi thư mục đại diện cho 1 từ/ký hiệu độc lập**: Hệ thống sẽ tự động nạp mẫu `.npy` và rule trong thư mục đó.
