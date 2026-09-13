# Kịch bản demo Lab 3 (khoảng 3 phút)

Bản chuẩn bị đầy đủ theo ảnh dàn ý coach: [PITCH_K4B.md](PITCH_K4B.md).

1. **Đề tài và lý do:** “Em làm trợ lý học vụ trên dữ liệu giả lập. Câu hỏi chung chỉ cần chatbot, nhưng yêu cầu tra cứu hồ sơ rồi tạo lịch với đúng cố vấn cần đọc dữ liệu và quyết định bước tiếp theo.”
2. **Agentic Fit:** Multi-step 4/5, Tool 5/5, Dynamic 4/5, Long Horizon 2/5 = 15/20. Bảng ba tiêu chí trên slide = 13/15. Điểm Long Horizon thấp vì tác vụ chỉ kéo dài vài bước, không có memory dài hạn.
3. **Workflow:** Mở [flowchart.md](flowchart.md). Agent hỏi LLM chọn bước, gọi `academic_query`, đọc observation. Chỉ khi SUCCESS và người dùng yêu cầu tạo lịch có giờ cụ thể mới gọi `schedule_appointment`; NOT_FOUND thì dừng.
4. **Công cụ:** `academic_query` tra hai hồ sơ DEMO theo mã, trả SUCCESS/NOT_FOUND; `schedule_appointment` tạo bản nháp lịch trong bộ nhớ, kiểm tra đã tra cứu, đúng cố vấn và đúng định dạng giờ. Cả hai không kết nối VinUni thật.
5. **Demo trực tiếp:** Chạy `python src/web_ui.py`, mở http://127.0.0.1:8765. Trong giao diện lấy bố cục từ FiProve, bấm **Bộ 5 tình huống** bên trái: TC01 cho 0 tool, TC03 cho một tool, TC04 cho chuỗi tra cứu → tạo lịch → final, TC05 cho NOT_FOUND và không có lịch. Chọn câu rồi bấm nút gửi ở ô hỏi phía dưới; bên phải mở **Xem tham số và kết quả** của từng bước trong waterfall trace.

Nếu API chậm lúc trình bày, mở sẵn [`ui_live.png`](ui_live.png) và
[`trace_waterfall.json`](trace_waterfall.json). Lượt nghiệm thu đã chạy API thật 5/5;
ảnh và trace là bằng chứng đã ghi, không phải lời hứa rằng gọi API mới sẽ luôn nhanh.
