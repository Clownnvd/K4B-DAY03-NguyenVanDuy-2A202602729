# Luồng xử lý: chatbot baseline và ReAct agent

```mermaid
flowchart TD
    U[Người dùng hỏi] --> B[Chatbot baseline: 1 LLM call, không tool]
    U --> A[ReAct agent: LLM chọn bước]
    A --> Q{Cần dữ liệu sinh viên?}
    Q -- Không --> F[Câu trả lời trực tiếp]
    Q -- Có --> T1[academic_query qua MCP-style adapter]
    T1 --> O1{Observation}
    O1 -- NOT_FOUND / lỗi --> E[Giải thích giới hạn; không tạo lịch]
    O1 -- SUCCESS --> D{Người dùng yêu cầu tạo lịch và có thời gian?}
    D -- Không --> F2[Trả GPA / cố vấn từ observation]
    D -- Có --> T2[schedule_appointment]
    T2 --> O2{Observation}
    O2 -- SUCCESS --> S[Thông báo bản nháp lịch DEMO, chưa gửi VinUni]
    O2 -- Lỗi --> E2[Giải thích lỗi, không nói đã đặt thành công]
    A -. Max iterations / lặp tool / lỗi API .-> H[Dừng và báo cần người kiểm tra]
```

Hai nhánh nhận cùng một câu hỏi trong 5 ca kiểm thử. Agent nối `assistant tool_call` và
`tool observation` vào hội thoại trước lần gọi LLM kế tiếp; TC04 vì vậy có chuỗi quan sát
được `academic_query → schedule_appointment → final answer`. Không suy diễn rằng hệ thống
đã gọi dữ liệu hoặc đặt lịch thật ở VinUni: cả hai tool dùng bộ dữ liệu giả lập trong repo.
