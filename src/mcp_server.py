"""
🔌 MODEL CONTEXT PROTOCOL (MCP) SERVER MODULE
Mô phỏng kiến trúc MCP Server (Client-Server Architecture) cung cấp công cụ chuẩn hóa.
"""

import json
import sys
from typing import Dict, Any, List
from tools import TOOLS_SCHEMA, dispatch_tool_call

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

class MCPAcademicServer:
    """
    In-process MCP-style teaching adapter using the starter JSON-RPC envelope.
    It does not connect to VinUni's production systems.
    """
    def __init__(self, server_name: str = "vinuni-academic-mcp-server"):
        self.server_name = server_name
        self.version = "2026.1.0"
        self.verified_student_ids: set[str] = set()
        
    def list_tools(self) -> List[Dict[str, Any]]:
        """Trả về danh sách các Tools chuẩn giao thức MCP"""
        return TOOLS_SCHEMA
        
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Validate arguments, dispatch a tool, and package its observation."""
        spec = next((t for t in TOOLS_SCHEMA if t["name"] == tool_name), None)
        if spec is None:
            content = {"status": "UNKNOWN_TOOL", "message": f"Tool {tool_name} không tồn tại."}
        elif not isinstance(arguments, dict):
            content = {"status": "INVALID_ARGUMENTS", "message": "Arguments phải là JSON object."}
        else:
            schema = spec["parameters"]
            missing = [key for key in schema.get("required", []) if key not in arguments]
            extra = [key for key in arguments if key not in schema.get("properties", {})]
            wrong_type = [key for key, value in arguments.items()
                          if key in schema.get("properties", {}) and not isinstance(value, str)]
            if missing or extra or wrong_type:
                content = {"status": "INVALID_ARGUMENTS", "missing": missing,
                           "extra": extra, "wrong_type": wrong_type}
            elif (tool_name == "schedule_appointment" and
                  arguments["student_id"].strip().upper() not in self.verified_student_ids):
                content = {"status": "PRECONDITION_REQUIRED",
                           "message": "Tra cứu academic_query thành công trong phiên này trước khi tạo lịch DEMO."}
            else:
                content = json.loads(dispatch_tool_call(tool_name, arguments))
                if tool_name == "academic_query" and content.get("status") == "SUCCESS":
                    self.verified_student_ids.add(arguments["student_id"].strip().upper())
        return {"jsonrpc": "2.0", "server": self.server_name,
                "tool": tool_name, "result": content}


if __name__ == "__main__":
    print("==========================================================")
    print("🔌 KIỂM THỬ ĐỘC LẬP MCP SERVER (vinuni-academic-mcp-server)")
    print("==========================================================")
    
    server = MCPAcademicServer()
    tools = server.list_tools()
    print(f"✅ Khởi tạo thành công MCP Server: {server.server_name} (Version: {server.version})")
    print(f"📦 Số lượng Tools công bố: {len(tools)}")
    
    # Verify both advertised tool schemas.
    sched_tool = next((t for t in tools if t.get("name") == "schedule_appointment"), None)
    if sched_tool and not sched_tool.get("parameters", {}).get("properties"):
        print("❌ Tool 'schedule_appointment' chưa có schema đầy đủ.")
    else:
        print("✅ Tool 'schedule_appointment' đã có schema đầy đủ.")

    # Verify dispatch and JSON-RPC-shaped response.
    test_result = server.call_tool("academic_query", {"student_id": "SV2026001"})
    if not test_result:
        print("❌ Hàm call_tool() trả về rỗng.")
    else:
        print(f"✅ Test dispatch tool 'academic_query' thành công:")
        print(f"   Phản hồi JSON-RPC: {json.dumps(test_result, ensure_ascii=False)}")
