"""LLM giả theo kịch bản: test harness + đồ thị OFFLINE, không tốn API.
Chạy:  python fake_llm.py
Mỗi tin nhắn trong kịch bản phải là một object RIÊNG (LangGraph gộp các tin nhắn trùng id).
"""
import itertools
from dataclasses import replace

from langchain_core.messages import AIMessage

_ids = itertools.count(1)


def call(name: str, **args) -> AIMessage:
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": f"c{next(_ids)}"}])


class ScriptedLLM:
    def __init__(self, script):
        self.script = list(script)

    def bind_tools(self, tools):
        return self

    def invoke(self, messages, *a, **k):
        return self.script.pop(0) if self.script else AIMessage(content="xong")


if __name__ == "__main__":
    from agents import run_agent
    from harness import Harness, Task, load_constraints
    from tools import WORLD

    P = "Nguyen Van A"
    task = Task("SGN", "HAN", "2026-10-15", P)
    S = dict(origin="SGN", dest="HAN", date="2026-10-15")
    search = lambda: call("search_flights", **S)
    hold = lambda f: call("hold_seat", flight_id=f, passenger=P)
    pay = lambda b="BK001": call("pay", booking_id=b)
    DONE_TEXT = lambda: AIMessage("Đã đặt QH303 giá 1.900.000đ, booking BK001 đã thanh toán.")

    def run(pattern, script, constraints=None, world=None, confirm=None, layers=None):
        WORLD.reset(**(world or {}))
        kw = {"confirm": confirm} if confirm else {}
        if layers is not None:
            kw["layers"] = layers
        h = Harness(task, constraints or load_constraints(), **kw)
        out, _ = run_agent(pattern, ScriptedLLM(script), h, task.to_prompt())
        return out, h

    # 1) cả 3 pattern: giữ chỗ -> thanh toán -> done
    for pattern, script in {
        "react": [search(), hold("QH303"), pay(), DONE_TEXT()],
        "plan_execute": [AIMessage('["tìm", "giữ chỗ", "thanh toán"]'), search(), hold("QH303"), pay()],
        "hybrid": [AIMessage('["tìm", "giữ chỗ", "thanh toán"]'), search(), AIMessage("tìm xong"),
                   hold("QH303"), AIMessage("giữ xong"), pay(), AIMessage("xong")],
    }.items():
        out, h = run(pattern, script)
        print(f"{pattern:13s} outcome={out['outcome']:8s} stats={h.stats()}")
        assert out["outcome"] == "done", pattern

    # 2) injection: bị dụ giữ chỗ VN404 -> authz chặn -> đổi sang QH303
    out, h = run("react", [search(), hold("VN404"), hold("QH303"), pay(), DONE_TEXT()])
    print("injection     outcome=%s stats=%s" % (out["outcome"], h.stats()))
    assert out["outcome"] == "done" and h.stats()["denied"] == 1

    # 3) không có chuyến hợp lệ -> bàn giao, câu hỏi nêu chuyến gần đạt nhất
    out, h = run("react", [search(), AIMessage("không có chuyến"), AIMessage("không có chuyến"), AIMessage("không có chuyến")],
                 constraints=replace(load_constraints(), max_price=1_000_000))
    print("handoff       outcome=%s | hỏi: %s" % (out["outcome"], out["handoff"]["question"][:95]))
    assert out["outcome"] == "handoff" and "XX707" in out["handoff"]["question"]

    # 4) gọi lặp cùng kết quả 3 lần -> phát hiện LẶP
    out, h = run("react", [search() for _ in range(5)])
    print("loop          outcome=%s reason=%s" % (out["outcome"], out["handoff"]["reason"]))
    assert out["outcome"] == "handoff" and "lặp" in out["handoff"]["reason"] and h.calls == 3

    # 5) timeout rồi thử lại thành công KHÔNG bị coi là lặp
    out, h = run("react", [search(), search(), hold("QH303"), pay(), DONE_TEXT()], world=dict(flaky_search=True))
    print("retry         outcome=%s stats=%s" % (out["outcome"], h.stats()))
    assert out["outcome"] == "done" and h.stats()["errors"] == 1

    # 6) cần duyệt thanh toán mà người không duyệt -> DỪNG và hỏi; vé chỉ ở trạng thái giữ chỗ
    out, h = run("react", [search(), hold("QH303"), pay()], constraints=replace(load_constraints(), require_confirm_above=1_000_000),
                 confirm=lambda n, a: False)
    print("approval      outcome=%s | hỏi: %s" % (out["outcome"], out["handoff"]["question"][:70]))
    assert out["outcome"] == "handoff" and "cần người duyệt" in out["handoff"]["reason"]
    assert [b["state"] for b in WORLD.bookings.values()] == ["HELD"] and not h.paid_bookings()

    # 7) chống ảo giác: câu trả lời bịa mã chuyến/giá không có trong kết quả tool
    out, h = run("react", [search(), AIMessage("Xong! Đã đặt VN999, ghế 5C, giá 1.200.000đ."),
                           AIMessage("Xong! Đã đặt VN999, ghế 5C, giá 1.200.000đ."), AIMessage("Xong! Đã đặt VN999, ghế 5C, giá 1.200.000đ.")])
    print("hallucination outcome=%s reason=%s" % (out["outcome"], out["handoff"]["reason"][:90]))
    assert out["outcome"] == "handoff" and out["handoff"]["reason"].startswith("ảo giác")

    # 8) tool trả rỗng âm thầm -> coi là LỖI TOOL (không phải 'không có chuyến'); dừng vì lặp, câu hỏi nói rõ dịch vụ rỗng
    out, h = run("react", [search() for _ in range(4)], world=dict(search_mode="silent_empty"))
    print("silent_empty  outcome=%s | hỏi: %s" % (out["outcome"], out["handoff"]["question"][:80]))
    assert out["outcome"] == "handoff" and "RỖNG" in out["handoff"]["question"]

    # 9) mới giữ chỗ mà chưa thanh toán -> check_done từ chối -> agent phải thanh toán
    out, h = run("react", [search(), hold("QH303"), AIMessage("xong"), pay(), AIMessage("Đã thanh toán BK001.")])
    print("unpaid->pay   outcome=%s paid=%d" % (out["outcome"], len(h.paid_bookings())))
    assert out["outcome"] == "done" and len(h.paid_bookings()) == 1

    # 10) chuyến đầu tiên giữ chỗ luôn hết ghế -> phải đổi chuyến
    out, h = run("react", [search(), hold("VN101"), hold("QH303"), pay(), DONE_TEXT()], world=dict(sold_out_first=True))
    print("sold_out_1st  outcome=%s stats=%s" % (out["outcome"], h.stats()))
    assert out["outcome"] == "done" and h.stats()["errors"] == 1

    # 11) ngân sách số lần gọi LLM luôn bật (kể cả khi tắt hết các lớp)
    out, h = run("react", [search() for _ in range(15)], layers=())
    print("llm budget    outcome=%s reason=%s" % (out["outcome"], out["handoff"]["reason"]))
    assert out["outcome"] == "handoff" and "ngân sách" in out["handoff"]["reason"]

    # 12) đếm token thật từ usage_metadata
    meta = {"input_tokens": 100, "output_tokens": 20, "total_tokens": 120}
    mk = lambda m: (setattr(m, "usage_metadata", meta), m)[1]
    out, h = run("react", [mk(search()), mk(hold("QH303")), mk(pay()), mk(DONE_TEXT())])
    print("token         usage=%s" % out["usage"])
    assert out["usage"] == {"tokens": 480, "llm_calls": 4}
    print("OK: tất cả smoke test đạt")
