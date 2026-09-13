"""Local, dependency-free demo UI for comparing baseline and ReAct traces."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from agent_provider import get_provider
from app import run_baseline_chatbot, run_react_agent


HTML = r"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Day 03 · Chatbot vs ReAct Agent</title>
<style>
:root{color-scheme:dark;font-family:Inter,Segoe UI,Arial,sans-serif;background:#090d18;color:#e9eefc}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 20% 0,#183052 0,transparent 34%),#090d18}
.wrap{max-width:1100px;margin:auto;padding:34px 22px 60px}.tag{color:#85b6ff;font-weight:700;letter-spacing:.13em;font-size:12px}
h1{font-size:clamp(30px,5vw,54px);line-height:1.05;max-width:780px;margin:14px 0}.sub{color:#aab7d0;max-width:780px;line-height:1.6}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.card{background:#121b2d;border:1px solid #2b3e5c;border-radius:18px;padding:22px;box-shadow:0 20px 60px #0002}
.card h2{margin:0 0 8px;font-size:20px}.muted{color:#9dacca}.query{margin:28px 0 16px}.query label{display:block;margin-bottom:9px;font-weight:700}
textarea{width:100%;resize:vertical;min-height:96px;padding:14px;border-radius:12px;border:1px solid #46658a;background:#0c1424;color:white;font:inherit;line-height:1.5}
.actions{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:12px 0 20px}button{border:0;border-radius:10px;padding:11px 16px;background:#74a7ff;color:#061121;font-weight:800;cursor:pointer;font:inherit}button:disabled{opacity:.55;cursor:wait}
.sample{background:#1c2b42;color:#d6e6ff;font-size:13px;padding:9px 12px}.meta{font-size:13px;color:#a9b9d3}.answer{white-space:pre-wrap;line-height:1.6;min-height:90px}
.flow{display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin:25px 0}.node{padding:9px 12px;border:1px solid #385781;background:#152542;border-radius:10px;font-size:13px}.arrow{color:#7caaff}
.trace{margin-top:18px}.event{border-left:2px solid #6ca5ff;margin:14px 0 0 6px;padding:4px 0 6px 18px}.event b{color:#a8ccff}.event pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#0b1425;border:1px solid #2a3a55;border-radius:8px;padding:11px;color:#d8e5ff}
.warn{color:#f1c57f;font-size:13px;line-height:1.5}.pill{display:inline-block;border:1px solid #486f9f;border-radius:999px;padding:5px 9px;color:#add1ff;font-size:12px;margin-bottom:10px}
@media(max-width:760px){.grid{grid-template-columns:1fr}.wrap{padding:24px 14px}}
</style></head><body><main class="wrap">
<div class="tag">AI20K · DAY 03 · LIVE COMPARISON</div><h1>Cùng một câu hỏi.<br>Hai cách xử lý.</h1>
<p class="sub">Chatbot baseline trả lời bằng một lượt LLM, không có công cụ. ReAct agent chọn công cụ, đọc kết quả và quyết định bước tiếp theo. Dữ liệu sinh viên và lịch hẹn trong demo đều là giả lập.</p>
<div class="flow"><span class="node">Câu hỏi</span><span class="arrow">→</span><span class="node">LLM chọn bước</span><span class="arrow">→</span><span class="node">academic_query</span><span class="arrow">→</span><span class="node">Observation</span><span class="arrow">→</span><span class="node">schedule_appointment nếu đủ điều kiện</span><span class="arrow">→</span><span class="node">Trả lời</span></div>
<section class="card query"><label for="q">Hỏi thử một tình huống</label><textarea id="q">Trong dữ liệu DEMO, hãy tra cứu SV2026002 rồi tạo bản nháp lịch tư vấn với đúng cố vấn của bạn ấy lúc 14:00 15/09/2026.</textarea>
<div class="actions"><button id="run">So sánh hai hệ thống</button><button class="sample" data-q="Đây là bản demo gì và hỗ trợ những việc nào?">Câu đơn giản</button><button class="sample" data-q="Trong dữ liệu DEMO, tra cứu SV2026001: GPA và cố vấn của bạn ấy là ai?">Tra cứu</button><button class="sample" data-q="Trong dữ liệu DEMO, hãy tra cứu SV9999999 và chỉ tạo bản nháp lịch tư vấn lúc 15:00 15/09/2026 nếu có hồ sơ.">Ca biên</button><span id="status" class="meta"></span></div>
<p class="warn">Bản demo không kết nối hệ thống học vụ VinUni và không tạo lịch thật. Trace ghi các quyết định gọi tool quan sát được, không phải suy luận riêng tư của model.</p></section>
<section class="grid"><div class="card"><span class="pill">Cấp 2 · một lượt, không tool</span><h2>Chatbot baseline</h2><div id="base" class="answer muted">Chưa chạy.</div><div id="baseMeta" class="meta"></div></div>
<div class="card"><span class="pill">Cấp 3 · vòng ReAct</span><h2>ReAct agent</h2><div id="agent" class="answer muted">Chưa chạy.</div><div id="agentMeta" class="meta"></div></div></section>
<section class="card trace"><h2>Waterfall trace</h2><p class="muted">Đọc từ trên xuống: model chọn bước → tool thực thi → observation → câu trả lời.</p><div id="trace">Chưa có trace.</div></section>
</main><script>
const $=id=>document.getElementById(id);const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
document.querySelectorAll('.sample').forEach(b=>b.onclick=()=>{$('q').value=b.dataset.q});
$('run').onclick=async()=>{const q=$('q').value.trim();if(!q)return;$('run').disabled=true;$('status').textContent='Đang gọi model và ghi trace…';
try{const r=await fetch('/api/compare',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q})});const d=await r.json();if(!r.ok)throw Error(d.error||'Không chạy được');
$('base').textContent=d.baseline.answer;$('agent').textContent=d.agent.answer;
$('baseMeta').textContent=d.baseline.latency_ms+' ms · 0 tool';$('agentMeta').textContent=d.agent.latency_ms+' ms · '+d.agent.tool_calls+' tool call · '+d.agent.model;
$('trace').innerHTML=d.agent.trace.map(e=>'<div class="event"><b>Step '+esc(e.step)+' · '+esc(e.action_type)+'</b><div>'+esc(e.thought||'')+'</div>'+(e.tool_name?'<pre>'+esc(e.tool_name+'('+JSON.stringify(e.arguments)+')\nObservation: '+JSON.stringify(e.observation))+'</pre>':'')+(e.output?'<pre>'+esc(e.output)+'</pre>':'')+'</div>').join('');
$('status').textContent='Đã chạy xong';}catch(e){$('status').textContent='Lỗi: '+e.message}finally{$('run').disabled=false}};
</script></body></html>"""


def make_handler(provider):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/":
                self._reply(200, HTML.encode("utf-8"), "text/html; charset=utf-8")
            elif self.path == "/health":
                self._json(200, {"status": "ok", "model": provider.model_name,
                                 "live_api": provider.is_live})
            else:
                self._json(404, {"error": "Not found"})

        def do_POST(self):
            if self.path != "/api/compare":
                self._json(404, {"error": "Not found"})
                return
            size = int(self.headers.get("Content-Length", "0"))
            if size < 1 or size > 10000:
                self._json(400, {"error": "Invalid request size"})
                return
            try:
                payload = json.loads(self.rfile.read(size))
                query = payload.get("question", "").strip()
                if not 1 <= len(query) <= 500:
                    raise ValueError("Câu hỏi phải dài 1–500 ký tự.")
                baseline = run_baseline_chatbot(query, provider)
                agent = run_react_agent(query, provider)
                self._json(200, {"baseline": baseline, "agent": agent})
            except (ValueError, json.JSONDecodeError) as exc:
                self._json(400, {"error": str(exc)})
            except Exception as exc:
                self._json(500, {"error": f"{type(exc).__name__}: {exc}"})

        def _json(self, status, data):
            self._reply(status, json.dumps(data, ensure_ascii=False).encode("utf-8"),
                        "application/json; charset=utf-8")

        def _reply(self, status, body, content_type):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):
            pass

    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()
    provider = get_provider(mock=args.mock)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(provider))
    print(f"Demo UI: http://127.0.0.1:{args.port} | {provider.model_name} "
          f"| live_api={provider.is_live}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
