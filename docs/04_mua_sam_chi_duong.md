# LĨNH VỰC 4: MUA SẮM & CHỈ ĐƯỜNG (SHOPPING & DIRECTIONS)
==================================================================

> **Mức độ ưu tiên:** 🟡 **THIẾT THỰC TRONG SINH HOẠT (Tier 2)**  
> **Ý nghĩa:** Người khiếm thính di chuyển ngoài đường phố, chợ dân sinh, siêu thị hoặc nhà hàng rất cần các cử chỉ để hỏi giá cả, thanh toán, tìm kiếm địa điểm công cộng như nhà vệ sinh, trạm xe buýt.

---

## 1. Danh Mục Ký Hiệu Cốt Lõi (Dataset Candidates)

| STT | Tên Thư Mục (`DATA/dynamic/`) | Ký Hiệu (Gloss) | Loại Cử Chỉ | Số Tay | Vị Trí (Location) | Mô Tả Động Tác Chuẩn | Trạng Thái Thu Thập |
| :---: | :--- | :--- | :--- | :---: | :--- | :--- | :---: |
| 1 | `bao_nhieu` | **BAO_NHIÊU** | Động | 1 hoặc 2 tay | Trước ngực | Lòng bàn tay ngửa, các ngón tay rung nhẹ hoặc búng lách tách lần lượt từ ngón út đến ngón trỏ; mặt hơi nhíu mày thắc mắc. | ⏳ Chưa quay |
| 2 | `mua` | **MUA** | Động | 1 hoặc 2 tay | Trước ngực | Bàn tay ngửa, ngón cái xoa nhẹ lên ngón trỏ và ngón giữa rồi đưa tay về phía trước (trao đổi lấy hàng). | ⏳ Chưa quay |
| 3 | `ban` | **BÁN** | Động | 2 tay | Trước ngực | Hai bàn tay nắm hờ lật ngửa đẩy thẳng ra phía người đối diện (trao đồ cho khách). | ⏳ Chưa quay |
| 4 | `dat` | **ĐẮT / MẮC** | Động | 1 tay | Trán / Ngực | Bàn tay mở bung mạnh lên cao hướng chếch lên trời; mắt mở to, miệng hơi xuýt xoa thể hiện giá quá cao. | ⏳ Chưa quay |
| 5 | `re` | **RẺ** | Động | 1 tay | Ngực | Lòng bàn tay úp, ấn nhẹ từ trên xuống dưới một cách thoải mái, thể hiện mức giá hạ thấp/vừa túi tiền. | ⏳ Chưa quay |
| 6 | `o_dau` | **Ở_ĐÂU** | Động | 1 tay | Trước ngực | Bàn tay ngửa hơi khum, lắc cổ tay nhẹ sang trái sang phải 2 lần; mắt nhìn xung quanh tìm kiếm. | ⏳ Chưa quay |
| 7 | `nha_ve_sinh` | **NHÀ_VỆ_SINH / WC** | Tĩnh/Động | 1 tay | Ngang vai | Bàn tay tạo hình chữ W (3 ngón trỏ, giữa, nhẫn giơ thẳng) hoặc chữ C, lắc nhẹ cổ tay 2 lần. | ⏳ Chưa quay |
| 8 | `re_trai` | **RẼ_TRÁI** | Động | 1 tay | Trước mặt | Ngón trỏ hoặc cả bàn tay khép đưa thẳng rồi ngoặt vuông góc dứt khoát sang bên trái. | ⏳ Chưa quay |
| 9 | `re_phai` | **RẼ_PHẢI** | Động | 1 tay | Trước mặt | Ngón trỏ hoặc cả bàn tay khép đưa thẳng rồi ngoặt vuông góc dứt khoát sang bên phải. | ⏳ Chưa quay |
| 10 | `di_thang` | **ĐI_THẲNG** | Động | 1 tay | Trước mặt | Bàn tay dựng đứng dọc (ngón trỏ hoặc cả mép bàn tay) đưa thẳng về phía trước theo một đường thẳng. | ⏳ Chưa quay |

---

## 2. Ngữ Pháp & Mẫu Câu Mua Bán & Chỉ Đường

### Mẫu 1: Hỏi giá tiền món hàng
* **Tiếng Việt nói:** *"Cái áo này giá bao nhiêu tiền?"*
* **Chuỗi ký hiệu VSL:** `ÁO` + `NÀY` + `TIỀN` + `BAO_NHIÊU`?
* **Quy tắc VSL:** Vật được trỏ tới (`ÁO NÀY`) đứng đầu câu; từ chỉ giá trị (`TIỀN`) và từ để hỏi (`BAO_NHIÊU`) đứng cuối.

### Mẫu 2: Mặc cả giá bán
* **Tiếng Việt nói:** *"Món này đắt quá, có bớt rẻ hơn được không?"*
* **Chuỗi ký hiệu VSL:** `CÁI_NÀY` + `ĐẮT` + `QUÁ` + `BỚT` + `RẺ` + `ĐƯỢC_KHÔNG`?
* **Quy tắc VSL:** Biểu cảm gương mặt khi làm ký hiệu `ĐẮT` rất quan trọng (nét mặt nhăn nhó, mắt tròn ngạc nhiên).

### Mẫu 3: Hỏi đường tới địa điểm công cộng
* **Tiếng Việt nói:** *"Xin lỗi, cho tôi hỏi nhà vệ sinh ở đâu?"*
* **Chuỗi ký hiệu VSL:** `XIN_LỖI` + `NHÀ_VỆ_SINH` + `Ở_ĐÂU`?
* **Quy tắc VSL:** Lời xin lỗi mở đầu $\rightarrow$ Địa điểm cần đến $\rightarrow$ Từ chỉ vị trí nghi vấn `Ở_ĐÂU` ở cuối cùng.

---

## 3. Khuyến Nghị Kỹ Thuật Khi Quay Dataset

1. **Không gian cử chỉ định hướng (Spatial Signing):**
   - Các từ chỉ đường (`RẼ_TRÁI`, `RẼ_PHẢI`, `ĐI_THẲNG`) phụ thuộc trực tiếp vào góc nhìn của camera (Viewpoint).
   - Khi quay mẫu, người làm mẫu cần quay theo góc nhìn thứ nhất hoặc góc nhìn giao tiếp trực diện để tránh nhầm lẫn giữa trái và phải.
2. **Cử chỉ vi mô ngón tay (Finger Flutter):**
   - Động tác `BAO_NHIÊU` có sự rung của các ngón tay. Camera cần FPS ổn định $\ge 25\text{ FPS}$ và ánh sáng đủ rõ để MediaPipe Hand tracking bắt trọn các khớp ngón tay (phalanges).
