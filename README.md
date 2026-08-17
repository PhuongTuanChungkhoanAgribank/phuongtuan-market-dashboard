# PHƯƠNG TUẤN - CHỨNG KHOÁN AGRIBANK CHI NHÁNH MIỀN TRUNG

**NGƯỜI AGRIBANK LÀM CHỨNG KHOÁN**  
**Daily Market**

Dashboard bản tin thị trường dùng Streamlit, lấy dữ liệu từ RSS và cập nhật tự động bằng GitHub Actions.

## Cơ chế hoạt động

1. Google News RSS được dùng làm lớp tổng hợp tin miễn phí.
2. Hệ thống chia tin thành: **Thế giới / Vĩ mô / Trong nước / Doanh nghiệp / Quỹ**.
3. Tiêu đề và tóm tắt được làm sạch HTML/entity, chuẩn hóa khoảng trắng và dịch sang tiếng Việt theo cơ chế best-effort.
4. Hệ thống loại tin trùng giữa các nguồn, không tự đoán sàn giao dịch khi chưa có thông tin rõ ràng.
5. Mỗi tin có thêm trường **importance 1–5** để phục vụ xếp hạng bản tin ở các bước tiếp theo; đây chỉ là điểm mức độ liên quan thông tin, không phải tín hiệu đầu tư.
6. Tin được lưu vào `data/daily_news.json`.
7. GitHub Actions tự chạy lúc **07:00, 11:00 và 15:00 giờ Việt Nam** mỗi ngày (UTC tương ứng 00:00, 04:00 và 08:00).
8. Streamlit đọc file dữ liệu mới nhất và hiển thị dashboard.

## Chạy thủ công

Trong GitHub vào **Actions → Update Daily Market News → Run workflow** để cập nhật ngay, không cần chờ lịch tự động.

## Nguyên tắc nội dung

Dashboard chỉ trình bày thông tin và liên kết nguồn. Không tự động thêm nhận định, dự báo giá hay khuyến nghị mua/bán.

## Chạy local

```bash
pip install -r requirements.txt
streamlit run app.py
```
