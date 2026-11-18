# LĨNH VỰC 5: GIÁO DỤC, TRƯỜNG HỌC & ĐÀO TẠO (EDUCATION & LEARNING)
======================================================================

> **Mức độ ưu tiên:** 🔵 **NỀN TẢNG PHÁT TRIỂN (Tier 3)**  
> **Ý nghĩa:** Trẻ em và thanh thiếu niên khiếm thính khi theo học hòa nhập hoặc chuyên biệt rất cần hệ thống hỗ trợ tương tác với giáo viên, bạn bè, tiếp thu kiến thức và làm bài tập.

---

## 1. Danh Mục Ký Hiệu Cốt Lõi (Dataset Candidates)

| STT | Tên Thư Mục (`DATA/dynamic/`) | Ký Hiệu (Gloss) | Loại Cử Chỉ | Số Tay | Vị Trí (Location) | Mô Tả Động Tác Chuẩn | Trạng Thái Thu Thập |
| :---: | :--- | :--- | :--- | :---: | :--- | :--- | :---: |
| 1 | `thay_co` | **THẦY_CÔ / GIÁO_VIÊN** | Động | 2 tay | Trước ngực | Hai bàn tay khép hơi nghiêng, đưa song song dứt khoát về phía trước (thể hiện việc truyền đạt/dạy dỗ) kết hợp ký hiệu `NGƯỜI`. | ⏳ Chưa quay |
| 2 | `ban_be` | **BẠN_BÈ** | Động | 2 tay | Trước ngực | Hai ngón trỏ móc vào nhau lần lượt qua lại 2 lần (thể hiện sự gắn kết, thân thiết). | ⏳ Chưa quay |
| 3 | `hieu` | **HIỂU** | Động | 1 tay | Trán | Bàn tay nắm đặt sát trán, sau đó bung xòe ngón trỏ hoặc cả bàn tay ra ngoài (mô phỏng tư tưởng thông suốt, sáng tỏ). Gật đầu. | ⏳ Chưa quay |
| 4 | `khong_hieu` | **KHÔNG_HIỂU** | Động | 1 tay | Trán | Ngón trỏ chạm vào thái dương rồi phẩy dứt khoát sang bên, đầu lắc nhẹ, mặt nhíu mày bối rối. | ⏳ Chưa quay |
| 5 | `bai_tap` | **BÀI_TẬP** | Động | 2 tay | Trước ngực | Ký hiệu `SÁCH/VỞ` (hai bàn tay mở ra như trang sách) + động tác viết nhanh. | ⏳ Chưa quay |
| 6 | `lop_hoc` | **LỚP_HỌC** | Động | 2 tay | Trước ngực | Hai bàn tay làm dấu chữ C đối xứng nhau, xoay tròn tạo thành một không gian phòng kín (phòng học). | ⏳ Chưa quay |
| 7 | `doc_sach` | **ĐỌC_SÁCH** | Động | 2 tay | Trước ngực | Tay trái mở phẳng làm trang sách, hai ngón tay phải (trỏ và giữa) làm mắt nhìn lướt từ trên xuống dưới trang sách. | ⏳ Chưa quay |
| 8 | `viet_bai` | **VIẾT_BÀI** | Động | 2 tay | Lòng bàn tay | Lòng bàn tay trái mở ngửa, ngón cái và trỏ tay phải chụm lại như cầm bút di chuyển lia lịa trên tay trái. | ⏳ Chưa quay |
| 9 | `cau_hoi` | **CÂU_HỎI / HỎI** | Động | 1 tay | Trước mặt | Ngón trỏ dựng đứng cong lại thành hình móc câu `?`, gập nhẹ về phía trước 1-2 lần. | ⏳ Chưa quay |
| 10 | `cham_chi` | **CHĂM_CHỈ** | Động | 2 tay | Trước ngực | Hai bàn tay nắm lại, hai ngón cái dựng lên, hai tay luân phiên đẩy tới lui nhanh nhẹn. | ⏳ Chưa quay |

---

## 2. Ngữ Pháp & Mẫu Câu Lớp Học Thực Tế

Trong môi trường giáo dục, sự phản hồi của học sinh và hướng dẫn của giáo viên là trung tâm:

### Mẫu 1: Phản hồi độ hiểu bài
* **Tiếng Việt nói:** *"Thưa cô, phần bài giảng này em chưa hiểu rõ."*
* **Chuỗi ký hiệu VSL:** `CÔ_GIÁO` + `BÀI_NÀY` + `EM` + `HIỂU` + `CHƯA` (hoặc `KHÔNG_HIỂU`)
* **Quy tắc VSL:** Xưng hô giáo viên $\rightarrow$ Chủ đề bài học $\rightarrow$ Bản thân $\rightarrow$ Trạng thái nhận thức (`KHÔNG_HIỂU`) kèm nét mặt thắc mắc.

### Mẫu 2: Hỏi về bài tập về nhà
* **Tiếng Việt nói:** *"Hôm nay lớp chúng ta có bài tập về nhà không thầy?"*
* **Chuỗi ký hiệu VSL:** `THẦY` + `HÔM_NAY` + `BÀI_TẬP` + `CÓ` + `KHÔNG`?
* **Quy tắc VSL:** Thời gian (`HÔM_NAY`) đứng ngay sau đại từ xưng hô, cặp từ nghi vấn `CÓ KHÔNG` chốt đuôi câu.

### Mẫu 3: Tương tác nhóm bạn bè
* **Tiếng Việt nói:** *"Bạn ơi, chỉ bài này cho mình với!"*
* **Chuỗi ký hiệu VSL:** `BẠN` + `BÀI_NÀY` + `DẠY/CHỈ` + `TÔI` + `GIÚP`
* **Quy tắc VSL:** Động từ `CHỈ/DẠY` đi kèm trợ từ cầu khiến `GIÚP`.

---

## 3. Khuyến Nghị Kỹ Thuật Khi Quay Dataset

1. **Phân biệt cặp từ trái nghĩa:**
   - Cặp từ `HIỂU` (gật đầu, ngón tay bung sáng) và `KHÔNG_HIỂU` (lắc đầu, tay phẩy bỏ). Cần chú trọng tracking vị trí tay so với thái dương/trán.
2. **Cử chỉ mắt & đầu (Head movement):**
   - Với câu hỏi và câu phủ định, cử chỉ gật/lắc đầu (Head Nod / Head Shake) đóng vai trò tương đương từ phủ định trong câu nói.
