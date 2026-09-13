"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND
Mã nguồn chứa danh sách Tool Schemas (JSON Schema) và Execution Layer phục vụ cho MCP Server.
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, Any

# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS CHUẨN NATIVE JSON SCHEMA (TASK 1.2)
# ==============================================================================

TOOLS_SCHEMA = [
    # Tool 1: Đã được định nghĩa mẫu sẵn cho Học viên tham khảo
    {
        "name": "academic_query",
        "description": (
            "Tra cứu hồ sơ sinh viên trong bộ dữ liệu DEMO bằng mã SVxxxxxxx. "
            "Trả SUCCESS với GPA và cố vấn hoặc NOT_FOUND; dùng trước khi tạo lịch. "
            "Không truy cập dữ liệu VinUni thật."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần tra cứu (ví dụ: 'SV2026001')"
                }
            },
            "required": ["student_id"]
        }
    },
    
    # --------------------------------------------------------------------------
    {
        "name": "schedule_appointment",
        "description": (
            "Tạo bản nháp lịch tư vấn trong dữ liệu DEMO, không đặt lịch VinUni thật. "
            "Chỉ dùng khi người dùng yêu cầu đặt lịch, đã tra cứu academic_query thành công "
            "trong phiên này và có thời gian cụ thể. advisor_name phải lấy đúng từ kết quả tra cứu."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên DEMO đã tra cứu, ví dụ SV2026001."
                },
                "datetime_str": {
                    "type": "string",
                    "description": "Thời gian hẹn theo định dạng HH:MM DD/MM/YYYY, ví dụ 14:00 15/09/2026."
                },
                "advisor_name": {
                    "type": "string",
                    "description": "Tên cố vấn chính xác trong observation của academic_query."
                }
            },
            "required": ["student_id", "datetime_str", "advisor_name"],
            "additionalProperties": False
        }
    }
]

# ==============================================================================
# 2. MÔ PHỎNG DỮ LIỆU & HÀM THỰC THI TOOL (EXECUTION LAYER)
# ==============================================================================

MOCK_DATABASE = {
    "SV2026001": {
        "full_name": "Nguyễn Văn An",
        "class": "AI-K4",
        "gpa": 3.85,
        "email": "an.nv@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "PGS.TS Nguyễn Văn A"
    },
    "SV2026002": {
        "full_name": "Trần Thị Bình",
        "class": "AI-K4",
        "gpa": 3.60,
        "email": "binh.tt@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "TS. Lê Thị B"
    }
}

# Trạng thái phiên demo: không ghi sang hệ thống học vụ thật.
BOOKING_DRAFTS: Dict[str, Dict[str, Any]] = {}


def execute_academic_query(student_id: str) -> str:
    """Thực thi tra cứu học vụ theo mã sinh viên"""
    student = MOCK_DATABASE.get(student_id.strip().upper())
    if student:
        return json.dumps({
            "status": "SUCCESS",
            "student_id": student_id,
            "data": student
        }, ensure_ascii=False)
    else:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy dữ liệu sinh viên có mã '{student_id}'"
        }, ensure_ascii=False)


def execute_schedule_appointment(student_id: str, datetime_str: str, advisor_name: str) -> str:
    """Tạo bản nháp lịch hẹn trong bộ dữ liệu giả lập, có kiểm tra điều kiện."""
    student_id = student_id.strip().upper()
    student = MOCK_DATABASE.get(student_id)
    if student is None:
        return json.dumps({"status": "NOT_FOUND", "student_id": student_id,
                           "message": "Không có sinh viên DEMO này; không tạo lịch."}, ensure_ascii=False)
    if advisor_name.strip() != student["advisor"]:
        return json.dumps({"status": "ADVISOR_MISMATCH", "student_id": student_id,
                           "message": "Cố vấn không khớp hồ sơ DEMO; không tạo lịch."}, ensure_ascii=False)
    try:
        datetime.strptime(datetime_str.strip(), "%H:%M %d/%m/%Y")
    except ValueError:
        return json.dumps({"status": "INVALID_DATETIME",
                           "message": "Dùng định dạng HH:MM DD/MM/YYYY; không tạo lịch."}, ensure_ascii=False)
    booking_id = "DEMO-" + hashlib.sha256(
        f"{student_id}|{datetime_str}|{advisor_name}".encode("utf-8")
    ).hexdigest()[:10].upper()
    booking = {
        "status": "SUCCESS", "simulated": True, "booking_id": booking_id,
        "student_id": student_id, "datetime": datetime_str.strip(),
        "advisor": advisor_name, "message": "Đã tạo bản nháp lịch tư vấn DEMO; chưa gửi tới VinUni."
    }
    BOOKING_DRAFTS[booking_id] = booking
    return json.dumps(booking, ensure_ascii=False)


# Router gọi tool thực tế
TOOL_ROUTER = {
    "academic_query": execute_academic_query,
    "schedule_appointment": execute_schedule_appointment
}

def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Hàm trung chuyển thực thi tool"""
    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)
        except Exception as e:
            return json.dumps({"status": "EXECUTION_ERROR", "error": str(e)}, ensure_ascii=False)
    return json.dumps({"status": "UNKNOWN_TOOL", "error": f"Tool '{tool_name}' không tồn tại!"}, ensure_ascii=False)
