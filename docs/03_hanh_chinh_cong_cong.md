# LĨNH VỰC 3: HÀNH CHÍNH & DỊCH VỤ CÔNG CỘNG (PUBLIC ADMINISTRATION & SERVICES)
================================================================================

> **Mức độ ưu tiên:** 🟡 **QUAN TRỌNG & PHỨC TẠP (Tier 2)**  
> **Ý nghĩa:** Người Điếc thường xuyên gặp khó khăn lớn khi làm các thủ tục giấy tờ tại cơ quan nhà nước, ngân hàng, công an hoặc bưu điện do tính pháp lý cao, nhiều thuật ngữ hành chính trừu tượng và không có nhân viên hỗ trợ ngôn ngữ ký hiệu.

---

## 1. Danh Mục Ký Hiệu Cốt Lõi (Dataset Candidates)

| STT | Tên Thư Mục (`DATA/dynamic/`) | Ký Hiệu (Gloss) | Loại Cử Chỉ | Số Tay | Vị Trí (Location) | Mô Tả Động Tác Chuẩn | Trạng Thái Thu Thập |
| :---: | :--- | :--- | :--- | :---: | :--- | :--- | :---: |
| 1 | `cccd` | **CCCD / THẺ_CĂN_CƯỚC** | Động | 2 tay | Trước ngực | Hai bàn tay dùng ngón cái và ngón trỏ vẽ thành hình chữ nhật chiếc thẻ nhỏ trước ngực, sau đó chỉ ngón trỏ vào mặt mình (thể hiện thẻ có ảnh/nhận dạng). | ⏳ Chưa quay |
| 2 | `ky_ten` | **KÝ_TÊN** | Động | 2 tay | Lòng bàn tay trái | Lòng bàn tay trái ngửa phẳng làm mặt giấy, tay phải cầm cây bút vô hình (chụm 3 ngón) vẽ đường lượn sóng nhanh trên tay trái. | ⏳ Chưa quay |
| 3 | `giay_to` | **GIẤY_TỜ** | Động | 2 tay | Trước ngực | Hai bàn tay mở phẳng, lòng bàn tay hướng vào nhau, vỗ nhẹ các mép tay vào nhau 2 lần mô phỏng tập hồ sơ/tờ giấy. | ⏳ Chưa quay |
| 4 | `cong_an` | **CÔNG_AN / CẢNH_SÁT** | Động | 1 tay | Trán / Mũ | Bàn tay khum hình chữ C đặt ngang trước trán mô phỏng vành mũ kepi hoặc phù hiệu công an. | ⏳ Chưa quay |
| 5 | `ngan_hang` | **NGÂN_HÀNG** | Động | 2 tay | Trước ngực | Kết hợp cử chỉ `TIỀN` (cọ xát ngón cái vào đầu ngón trỏ) + cử chỉ `NHÀ/TÒA_NHÀ` (úp 2 bàn tay tạo mái nhà). | ⏳ Chưa quay |
| 6 | `gui_tien` | **GỬI_TIỀN** | Động | 2 tay | Trước ngực | Bàn tay làm dấu hiệu tiền hoặc tập phong bì đẩy từ ngực mình ra phía trước (đưa cho nhân viên giao dịch). | ⏳ Chưa quay |
| 7 | `rut_tien` | **RÚT_TIỀN** | Động | 2 tay | Trước ngực | Bàn tay làm cử chỉ cắm thẻ vào khe máy ATM rồi kéo nắm tiền về phía lòng mình. | ⏳ Chưa quay |
| 8 | `dia_chi` | **ĐỊA_CHỈ** | Động | 2 tay | Trước ngực | Ký hiệu `NHÀ` kết hợp ngón trỏ chỉ xuống định vị một điểm cụ thể. | ⏳ Chưa quay |
| 9 | `so_dien_thoai` | **SỐ_ĐIỆN_THOẠI** | Động | 1 tay | Tai | Bàn tay làm hình chữ Y (ngón cái và ngón út xòe, 3 ngón giữa cụp) áp ngón cái vào tai, ngón út hướng vào miệng. | ⏳ Chưa quay |
| 10 | `cho_doi` | **CHỜ_ĐỢI** | Động | 2 tay | Ngực | Hai bàn tay úp ngang ngực, các ngón tay gõ nhịp nhẹ lên xuống mô tả sự kiên nhẫn đợi đến số thứ tự. | ⏳ Chưa quay |

---

## 2. Ngữ Pháp & Mẫu Câu Hành Chính Thực Tế

Thủ tục hành chính đòi hỏi truyền đạt rõ ràng mục đích giao dịch và thông tin định danh:

### Mẫu 1: Làm thẻ Căn cước công dân
* **Tiếng Việt nói:** *"Tôi đến đây để làm lại thẻ Căn cước công dân bị mất."*
* **Chuỗi ký hiệu VSL:** `TÔI` + `CCCD` + `MẤT` + `MUỐN` + `LÀM_LẠI`
* **Quy tắc VSL:** Sự vật/vấn đề cần giải quyết (`CCCD MẤT`) được nêu trước nhu cầu (`LÀM LẠI`).

### Mẫu 2: Giao dịch tại ngân hàng
* **Tiếng Việt nói:** *"Tôi muốn rút 5 triệu đồng từ tài khoản ngân hàng."*
* **Chuỗi ký hiệu VSL:** `TÔI` + `NGÂN_HÀNG` + `TIỀN` + `5_TRIỆU` + `RÚT` + `MUỐN`
* **Quy tắc VSL:** Đối tượng giao dịch + Số lượng (`5_TRIỆU`) đứng trước hành động chính (`RÚT`).

### Mẫu 3: Báo mất giấy tờ tại công an
* **Tiếng Việt nói:** *"Chào đồng chí công an, tôi bị mất ví tiền và toàn bộ giấy tờ."*
* **Chuỗi ký hiệu VSL:** `CÔNG_AN` + `XIN_CHÀO` + `TÔI` + `VÍ_TIỀN` + `GIẤY_TỜ` + `TẤT_CẢ` + `MẤT`
* **Quy tắc VSL:** Gọi người thi hành công vụ $\rightarrow$ Chào $\rightarrow$ Danh sách đồ đạc bị ảnh hưởng $\rightarrow$ Biến cố (`MẤT`).

---

## 3. Khuyến Nghị Kỹ Thuật Khi Quay Dataset

1. **Sử dụng cử chỉ kết hợp (Compound Signs):**
   - Từ như `ngan_hang` thường gồm 2 động tác nối tiếp: `TIỀN` + `NHÀ`.
   - Khi quay mẫu dữ liệu cho dynamic recognizer, nên thu thập cả dạng viết tắt 1 cử chỉ và dạng ghép chuẩn để mô hình nhận diện mượt mà.
2. **Ký hiệu số ngón tay (Finger spelling):**
   - Với số tiền hoặc số CCCD, hệ thống nên kết hợp mô hình nhận diện bàn tay tĩnh (`BE/static/`) để người dùng đánh vần từng con số.
