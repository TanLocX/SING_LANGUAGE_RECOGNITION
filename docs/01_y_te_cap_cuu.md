# LĨNH VỰC 1: Y TẾ, SỨC KHỎE & CẤP CỨU (HEALTHCARE & EMERGENCY)
==================================================================

> **Mức độ ưu tiên:** 🔴 **CẤP BÁCH NHẤT (Tier 1)**  
> **Ý nghĩa xã hội:** Rào cản giao tiếp tại bệnh viện là một trong những nguy cơ lớn nhất đe dọa trực tiếp tới tính mạng và sức khỏe người Điếc/Khiếm thính do đội ngũ y bác sĩ, điều dưỡng hầu như không biết ngôn ngữ ký hiệu.

---

## 1. Danh Mục Ký Hiệu Cốt Lõi (Dataset Candidates)

| STT | Tên Thư Mục (`DATA/dynamic/`) | Ký Hiệu (Gloss) | Loại Cử Chỉ | Số Tay | Vị Trí (Location) | Mô Tả Động Tác Chuẩn | Trạng Thái Thu Thập |
| :---: | :--- | :--- | :--- | :---: | :--- | :--- | :---: |
| 1 | `dau` | **ĐAU** | Động | 1 tay | Đầu / Bụng / Vị trí đau | Ngón trỏ chỉ vào vị trí đau (đầu, bụng...), lắc hoặc nhấp 2 lần; nét mặt nhăn nhó, khó chịu. | ⏳ Chưa quay |
| 2 | `sot` | **SỐT** | Động | 1 tay | Trán | Mu bàn tay áp lên trán, sau đó ngửa lòng bàn tay hất ra ngoài mô phỏng nhiệt độ cơ thể bốc nóng. | ⏳ Chưa quay |
| 3 | `uong_thuoc` | **UỐNG_THUỐC** | Động | 1 tay | Miệng | Ngón cái và ngón trỏ chụm lại mô phỏng cầm viên thuốc đưa vào miệng, ngửa đầu nuốt. | ⏳ Chưa quay |
| 4 | `bac_si` | **BÁC_SĨ** | Động | 2 tay | Cổ tay trái | Cánh tay trái đưa ngang làm cổ tay, 3 ngón tay phải (trỏ, giữa, nhẫn) gõ nhẹ vào cổ tay trái (bắt mạch). | ⏳ Chưa quay |
| 5 | `benh_vien` | **BỆNH_VIỆN** | Động | 2 tay | Trước ngực | Hai ngón trỏ bắt chéo nhau tạo hình chữ thập đỏ y tế trước ngực. | ⏳ Chưa quay |
| 6 | `cap_cuu` | **CẤP_CỨU** | Động | 2 tay | Không gian ngực | Hai bàn tay xòe hướng về trước, đẩy nhanh về phía trước liên tục kết hợp rung lắc báo sự khẩn cấp. | ⏳ Chưa quay |
| 7 | `tiem_thuoc` | **TIÊM** | Động | 2 tay | Bắp tay trái | Tay trái đưa ngang, tay phải tạo hình ống tiêm chọc vào bắp tay và ấn ngón cái xuống. | ⏳ Chưa quay |
| 8 | `kham_benh` | **KHÁM_BỆNH** | Động | 2 tay | Ngực | Tay phải nắm hờ như ống nghe khám bệnh, đặt lần lượt lên ngực trái rồi ngực phải. | ⏳ Chưa quay |
| 9 | `chong_mat` | **CHÓNG_MẶT** | Động | 1 tay | Trán | Bàn tay xòe xoay tròn trước trán theo hình xoắn ốc; mắt hơi nhắm, đầu lắc lư nhẹ. | ⏳ Chưa quay |
| 10 | `di_ung` | **DỊ_ỨNG** | Động | 1 tay | Cẳng tay | Các đầu ngón tay cào nhẹ lên cẳng tay đối diện (mô phỏng gãi ngứa nổi mẩn). | ⏳ Chưa quay |

---

## 2. Ngữ Pháp & Mẫu Câu Giao Tiếp Y Tế Thực Tế

Trong giao tiếp y tế, người Điếc áp dụng triệt để quy tắc:  
**Thời gian phát bệnh $\rightarrow$ Vị trí cơ thể $\rightarrow$ Triệu chứng cụ thể $\rightarrow$ Yêu cầu/Hành động**

### Mẫu 1: Báo cáo triệu chứng bệnh
* **Tiếng Việt nói:** *"Hôm qua tôi bị đau đầu dữ dội."*
* **Chuỗi ký hiệu VSL:** `HÔM_QUA` + `TÔI` + `ĐẦU` + `ĐAU` + `NHIỀU`
* **Quy tắc VSL:** Thời gian (`HÔM_QUA`) đặt đầu câu; bộ phận (`ĐẦU`) nêu trước hiện tượng (`ĐAU`); mức độ (`NHIỀU`) ở cuối.

### Mẫu 2: Tình huống cấp cứu khẩn cấp
* **Tiếng Việt nói:** *"Bác sĩ ơi mau cấp cứu cho tôi, tôi khó thở quá!"*
* **Chuỗi ký hiệu VSL:** `BÁC_SĨ` + `TÔI` + `CẤP_CỨU` + `NHANH` + `THỞ` + `KHÔNG_ĐƯỢC`
* **Quy tắc VSL:** Nêu danh xưng (`BÁC_SĨ`), sự việc khẩn (`CẤP_CỨU`), tốc độ (`NHANH`), nguyên nhân (`THỞ KHÔNG ĐƯỢC`).

### Mẫu 3: Bệnh nhân hỏi cách dùng thuốc
* **Tiếng Việt nói:** *"Tôi đau bụng thì uống thuốc này như thế nào?"*
* **Chuỗi ký hiệu VSL:** `TÔI` + `BỤNG` + `ĐAU` + `THUỐC` + `NÀY` + `UỐNG_THUỐC` + `THẾ_NÀO`?
* **Quy tắc VSL:** Đại từ nghi vấn (`THẾ_NÀO`) đặt ở cuối câu; nét mặt nhíu mày, đầu hơi chúi về phía trước.

---

## 3. Khuyến Nghị Kỹ Thuật Khi Quay Dataset & Nhận Diện

1. **Khung hình chuẩn:** Quay nửa thân trên (từ thắt lưng lên qua đầu). Cần giữ khoảng cách 1.2m - 1.8m với camera để thấy rõ cử chỉ tiếp xúc với trán, tai, cổ và bụng.
2. **Biểu cảm nét mặt (Non-manual Markers):**
   - Với từ `ĐAU`: Nét mặt nhăn, mắt nheo.
   - Với từ `CẤP_CỨU`: Mặt hốt hoảng, miệng mấp máy khẩn trương.
3. **DTW Tuning:**
   - Cử chỉ `cap_cuu` có tần số dao động cao, nên quay ở 30 FPS với ít nhất 15-20 frames/lượt.
