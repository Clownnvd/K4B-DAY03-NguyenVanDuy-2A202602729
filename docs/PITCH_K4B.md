# Kịch bản pitching Lab 3 K4B — Nguyễn Văn Duy

**Mở giao diện:** http://127.0.0.1:8765
**Repo nộp:** https://github.com/Clownnvd/K4B-DAY03-NguyenVanDuy-2A202602729
**Ảnh dự phòng:** [ui_live.png](ui_live.png) · **Trace gốc:** [trace_waterfall.json](trace_waterfall.json)
**Nguồn dàn ý:** [ảnh bảng coach trong #3b-lab-e403](https://discord.com/channels/1543625766837952622/1547290260877344798/1548598874879557714).

## Bài nói 3 phút theo đúng 5 ý của coach

**0:00–0:30 — 1. Đề tài và vì sao chọn.**
“Em chọn **trợ lý học vụ DEMO**. Một câu hỏi như ‘bản demo làm được gì?’ chỉ cần chatbot. Nhưng khi người dùng yêu cầu tra cứu một sinh viên rồi tạo lịch với **đúng cố vấn của sinh viên đó**, hệ thống phải đọc dữ liệu, chọn bước tiếp theo theo kết quả và thực hiện công cụ. Em dùng cùng một bài toán để so sánh chatbot baseline với ReAct agent. Dữ liệu và lịch hẹn là giả lập, không kết nối VinUni thật.”

**0:30–1:05 — 2. Bốn tiêu chí Agentic Fit.**
“Multi-step **4/5** vì phải tra cứu rồi mới có tên cố vấn để tạo lịch. Tool Interaction **5/5** vì một tool đọc hồ sơ và một tool tạo bản nháp. Dynamic Decision **4/5** vì nếu không có hồ sơ thì dừng, có hồ sơ mới đi tiếp. Long Horizon **2/5** vì mục tiêu chỉ kéo dài vài vòng trong một yêu cầu, chưa có memory dài hạn. Tổng là **15/20** theo mẫu Lab; ba tiêu chí trên slide là **13/15**, vượt ngưỡng ‘agent đáng thử’. Em không chấm Long Horizon 5 chỉ để làm tổng đẹp.”

**1:05–1:40 — 3. Kiến trúc.**
“Màn hình giữa so hai đường đi. Baseline gọi LLM một lượt, **không có tool**. Agent gọi LLM với tool schema, nhận tool call, gửi qua adapter MCP-style, đọc observation rồi gọi LLM tiếp. Ở ca đặt lịch, vết thật là **academic_query → schedule_appointment → final answer**. Nếu observation là NOT_FOUND, nhánh tạo lịch không chạy. Giới hạn 5 vòng và chặn gọi lại cùng tool/args để tránh loop.”
**Chỉ vào:** sơ đồ ở slide 3 hoặc nút **Quy trình** trong UI.

**1:40–2:05 — 4. Công cụ.**
“academic_query nhận mã sinh viên, trả dữ liệu DEMO hoặc NOT_FOUND. schedule_appointment nhận mã, giờ và tên cố vấn; backend kiểm tra đã tra cứu trong phiên, tên cố vấn khớp, giờ đúng định dạng. Nó chỉ tạo **bản nháp trong bộ nhớ**, không đặt lịch thật. Vì vậy điều kiện an toàn nằm cả ở code, không phụ thuộc hoàn toàn vào lời model.”

**2:05–3:10 — 5. Demo 1–2 câu và trace.**
Mở http://127.0.0.1:8765 → bên trái bấm **Bộ 5 tình huống**:

1. Chọn **TC01**, bấm nút gửi ở ô cuối màn hình. Nói: “Câu một bước, agent không gọi tool; chatbot đủ.”
2. Chọn **TC04**, bấm gửi. Nói: “Agent đọc SV2026002, observation trả cố vấn **TS. Lê Thị B**; bước sau dùng đúng tên này để tạo bản nháp lịch **14:00 15/09/2026**. Bảng bên phải cho thấy hai tool và câu trả lời cuối.” Mở **Xem tham số và kết quả** ở hai thẻ trace.

Nếu còn thời gian, chọn **TC05**: mã SV9999999 trả NOT_FOUND, không có schedule_appointment. Kết bài: “Lượt nghiệm thu của em chạy **5/5 ca bằng OpenAI gpt-4.1-mini thật**, có 4 tool calls đúng. Median 5 ca là **1202.30 ms** baseline và **1997.90 ms** agent; mẫu nhỏ, em không nói agent luôn nhanh hơn.”

## Chuẩn bị màn hình trước khi lên

1. Mở file [slide pitching](../presentation/Day03_K4B_Kingpro_Pitch.pptx) bằng PowerPoint và giữ UI http://127.0.0.1:8765 ở tab bên cạnh. Dùng chế độ trình chiếu 16:9.
2. Mở sẵn [repo K4B](https://github.com/Clownnvd/K4B-DAY03-NguyenVanDuy-2A202602729) để chỉ vào code/report khi được hỏi.
3. Kiểm tra http://127.0.0.1:8765/health hiển thị live_api: true và model: gpt-4.1-mini. Nếu server đã tắt, trong thư mục repo chạy .venv\Scripts\python.exe src/web_ui.py.
4. Nhớ rằng mỗi câu live gọi API có thể chậm. Nếu timeout hoặc mạng chập chờn, mở [ảnh UI đã chạy thật](ui_live.png) và [TC04 trong trace gốc](trace_waterfall.json), nói rõ đây là **kết quả đã ghi trước**, rồi giải thích từng bước. Không giả vờ đó là lần chạy mới.
5. Không mở file .env trên máy chiếu và không hiện API key.

## 5 câu hỏi dễ bị hỏi

| Hỏi | Trả lời ngắn |
| --- | --- |
| Vì sao không chỉ làm FAQ chatbot? | FAQ nội bộ HR trên slide có 1 + 1 + 1 = 3/15; use case này có bước tra cứu rồi hành động phụ thuộc observation, 13/15. |
| Đây có phải dữ liệu/lịch VinUni thật? | Không. Dữ liệu starter là DEMO, bản nháp lưu trong bộ nhớ. API **LLM** là thật, còn hệ thống học vụ là mô phỏng. |
| MCP đã chạy độc lập qua mạng chưa? | Chưa. Repo starter dùng adapter MCP-style trong cùng tiến trình với envelope JSON-RPC; native function calling đến OpenAI là thật. |
| Trace có phải chain-of-thought riêng tư? | Không. Trường thought là tóm tắt quyết định gọi tool **quan sát được**; log ghi action, args, observation và final answer. |
| Nếu model gọi sai tool/đặt sai cố vấn thì sao? | Tool backend kiểm tra tham số, yêu cầu tra cứu trước, từ chối cố vấn sai; agent có max 5 vòng và chặn lặp tool. |

**Con số cần nhớ:** 15/20 Agentic Fit · 13/15 theo bảng slide · 2 tools · 5/5 test API thật · 4 tool calls · repo K4B đã nộp VLearn lúc 15:05:55 ngày 13/09/2026. Mức 5/5 sao trên form VLearn là đánh giá do học viên chọn, chưa phải điểm giảng viên.
