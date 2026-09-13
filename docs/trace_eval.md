# Báo cáo nghiệm thu Lab 3 — Chatbot vs ReAct Agent

> **Họ tên:** NGUYỄN VĂN DUY<br>
> **MSSV:** 2A202602729<br>
> **Đề tài:** Trợ lý học vụ DEMO: tra cứu sinh viên rồi tạo bản nháp lịch với đúng cố vấn<br>
> **Hình thức:** Bài cá nhân, fork repo K4A của lớp sáng<br>
> **LLM nghiệm thu:** OpenAI `gpt-4.1-mini` qua API thật; key chỉ nằm trong biến môi trường Windows.

## 1. Agentic Fit Scoring Matrix

| Tiêu chí | Điểm / 5 | Lý do dựa trên workflow |
| --- | ---: | --- |
| Multi-step Reasoning | 4 | Yêu cầu tạo lịch phải tra cứu hồ sơ, lấy cố vấn từ kết quả, rồi mới tạo bản nháp. Câu hỏi chung vẫn chỉ cần một bước. |
| Tool Interaction | 5 | Cần `academic_query` để đọc dữ liệu DEMO và `schedule_appointment` để ghi bản nháp; LLM không được tự bịa kết quả. |
| Dynamic Decision | 4 | `NOT_FOUND` thì dừng; `SUCCESS` và có giờ hẹn mới tạo lịch. Tên cố vấn và bước sau phụ thuộc observation. |
| Long Horizon Goal | 2 | Giữ mục tiêu qua vài lượt trong một yêu cầu; không có memory dài hạn hay nhiệm vụ tự trị nhiều ngày. |
| **Tổng** | **15/20** | Vượt ngưỡng `>12/20` của mẫu báo cáo Lab 3. |

Nếu dùng **bảng 3 tiêu chí trong slide** (Reasoning, Tool use, Dynamic Decision),
use case đạt **13/15**. Đây là yêu cầu nhiều bước có bước phụ thuộc nhau, khác FAQ nội bộ HR
trên slide (1 + 1 + 1 = 3/15). Điểm Long Horizon được giữ thấp thay vì nâng để làm đẹp số.

## 2. Thiết kế và ranh giới

- Cùng một câu hỏi chạy qua **chatbot baseline** (một lượt LLM, không tool) và **ReAct agent**.
- Agent dùng native function calling, nối tool call và observation vào hội thoại trước lần gọi LLM kế tiếp.
- `src/mcp_server.py` là adapter **MCP-style trong cùng tiến trình** theo starter repo, trả envelope `jsonrpc: "2.0"`. Đây không phải MCP server chạy từ xa hay tích hợp VinUni thật.
- `academic_query` đọc hai hồ sơ giả lập; `schedule_appointment` chỉ tạo bản nháp trong bộ nhớ, kiểm tra đã tra cứu cùng phiên, tên cố vấn và định dạng thời gian.
- Sơ đồ đầy đủ: [flowchart.md](flowchart.md). Prompt có điều kiện dừng, `MAX_ITERATIONS=5`, chặn gọi lại cùng tool/args, trả lỗi đúng khi tool/API thất bại.
- Trường `thought` trong trace là **tóm tắt công khai từ quyết định gọi tool quan sát được**. Nó không được trình bày như chain-of-thought riêng tư của model.

## 3. Nghiệm thu bằng API thật và so sánh cùng 5 câu hỏi

Chạy `python src/app.py --all` trên Python 3.11. Dữ liệu dưới đây lấy từ
[`test_results.json`](test_results.json) và [`trace_waterfall.json`](trace_waterfall.json)
ở lượt nghiệm thu cuối, không lấy từ Mock Provider.

| Ca | Mục đích | Chatbot baseline | ReAct agent | Tool/status thực tế | Kết quả |
| --- | --- | ---: | ---: | --- | --- |
| TC01 | Câu hỏi về chức năng demo, không cần tool | 3162.39 ms | 2609.84 ms | không gọi tool | PASS |
| TC02 | Cần cung cấp gì để tra cứu? | 1122.96 ms | 1184.37 ms | không gọi tool | PASS |
| TC03 | Hỏi GPA và cố vấn của SV2026001 | 1105.74 ms | 1842.84 ms | `academic_query → SUCCESS` | PASS |
| TC04 | Tra cứu SV2026002 rồi tạo lịch với đúng cố vấn | 1385.08 ms | 3265.50 ms | `academic_query → SUCCESS; schedule_appointment → SUCCESS` | PASS |
| TC05 | Mã SV9999999 không tồn tại | 1273.91 ms | 2719.73 ms | `academic_query → NOT_FOUND`; không tạo lịch | PASS |

**Kết quả:** 5/5 ca đạt kỳ vọng; **4 tool calls** đúng trong 5 ca; median độ trễ
baseline **1273.91 ms**, agent **2609.84 ms**. Đây chỉ là 5 lần gọi trên một máy,
không đủ để kết luận hiệu năng tổng quát. TC01 baseline chậm hơn agent trong lượt này;
không tô vẽ rằng chatbot luôn nhanh hơn. Giá trị tăng thêm của agent thể hiện ở TC03–TC05:
baseline không thể xác minh hồ sơ hay tạo lịch, còn agent dùng observation và dừng đúng ca lỗi.

### Trích đoạn waterfall trace thật của TC04

```json
[
  {
    "step": 1,
    "action_type": "TOOL_EXECUTION",
    "tool_name": "academic_query",
    "arguments": {"student_id": "SV2026002"},
    "observation": {"status": "SUCCESS", "data": {"advisor": "TS. Lê Thị B", "gpa": 3.6}},
    "latency_ms": 964.75
  },
  {
    "step": 2,
    "action_type": "TOOL_EXECUTION",
    "tool_name": "schedule_appointment",
    "arguments": {"student_id": "SV2026002", "datetime_str": "14:00 15/09/2026", "advisor_name": "TS. Lê Thị B"},
    "observation": {"status": "SUCCESS", "simulated": true, "booking_id": "DEMO-99F49B87E9"},
    "latency_ms": 1122.44
  },
  {
    "step": 3,
    "action_type": "FINAL_ANSWER",
    "output": "Đã tạo bản nháp lịch tư vấn DEMO cho SV2026002 với cố vấn TS. Lê Thị B lúc 14:00 15/09/2026; lịch này chưa gửi tới VinUni.",
    "latency_ms": 1178.05
  }
]
```

Trace gốc chứa toàn bộ observation và metadata của từng lượt, không chỉ trích đoạn trên.
TC05 cho thấy `NOT_FOUND` rồi `FINAL_ANSWER`, không có `schedule_appointment`.

## 4. Tự kiểm và nhận định

- [x] Chạy 4 unit tests cho điều kiện tạo lịch, dữ liệu không tồn tại, chuỗi nhiều bước và chống lặp tool.
- [x] Chạy offline Mock 5/5 để kiểm tra luồng code; file Mock được đặt riêng, không dùng làm bằng chứng nghiệm thu.
- [x] Chạy 5/5 ca với OpenAI API thật, model `gpt-4.1-mini`; trace ghi `response_id`, latency và observation từng bước.
- [x] Có UI địa phương tại `python src/web_ui.py` để demo hai câu trả lời và waterfall trace cạnh nhau.
- [x] UI đã được kiểm tra bằng một lượt gọi API thật; [ảnh minh chứng](ui_live.png) hiển thị hai tool calls và câu trả lời cuối.
- [ ] Push repo cá nhân và nộp link trên VLearn — cập nhật sau bước cuối.

**Kết luận dựa trên kết quả:** Với câu hỏi chức năng đơn giản, chatbot baseline đủ và
không cần trả thêm chi phí tool loop. Với câu hỏi hồ sơ và chuỗi tra cứu → tạo lịch,
agent tạo giá trị vì dùng đúng dữ liệu và kiểm tra bước sau từ observation. Muốn dùng
thực tế phải thay dữ liệu giả lập bằng hệ thống được cấp quyền, thêm xác thực người hỏi,
kiểm tra lịch trống và xác nhận trước mọi thao tác ghi thật.
