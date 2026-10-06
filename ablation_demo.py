"""Demo ablation TẤT ĐỊNH: 4 kiểu lỗi kinh điển của agent × harness TẮT / BẬT (dùng LLM giả có kịch bản).

Vì sao dùng LLM giả: LLM thật hiếm khi tự mắc đúng lỗi mình cần minh họa, nên không thể dùng để CHỨNG MINH
một lớp harness có tác dụng. Ở đây "model" cố tình mắc lỗi, nên kết quả tái hiện được 100% và chỉ phụ thuộc vào code harness.
(Số liệu so sánh 3 pattern vẫn phải đo bằng LLM thật với evaluate.py.)

    1. loop           lặp vô hạn một lời gọi tool        -> lớp `loop`
    2. hallucination  câu trả lời chứa dữ kiện bịa        -> lớp `grounding`
    3. drift          quên ràng buộc (chạy theo giá rẻ)   -> lớp `authz`
    4. state          tool trả rỗng, bị hiểu là 'hết chuyến' -> lớp `validate`

Harness TẮT = layers rỗng (vẫn còn ngân sách tool/LLM, vì ngân sách luôn bật). Harness BẬT = mọi lớp.
Chạy:  python ablation_demo.py          (kết quả in ra màn hình và lưu traces/ablation_demo.md)
"""
import json
import os

from langchain_core.messages import AIMessage

from agents import run_agent
from fake_llm import ScriptedLLM, call
from harness import ALL_LAYERS, Harness, Task, load_constraints
from tools import WORLD

P = "Nguyen Van A"
TASK = Task("SGN", "HAN", "2026-10-15", P)
S = dict(origin="SGN", dest="HAN", date="2026-10-15")
search = lambda: call("search_flights", **S)
hold = lambda f: call("hold_seat", flight_id=f, passenger=P)
pay = lambda b="BK001": call("pay", booking_id=b)
HALLU = lambda: AIMessage("Xong! Đã đặt VN999, ghế 5C, giá 1.200.000đ.")
OK_TEXT = lambda: AIMessage("Đã đặt QH303 giá 1.900.000đ, booking BK001 đã thanh toán.")

# mỗi kịch bản: (tiêu đề, lớp chống lỗi, mô tả lỗi, tham số thế giới giả, hàm tạo kịch bản(on: bool))
MODES = {
    "loop": ("Vòng lặp vô hạn", "loop",
             "Tool chỉ trả lỗi mơ hồ 'not found' nên model cứ gọi lại y hệt.",
             dict(search_mode="vague_error"),
             lambda on: [search() for _ in range(12)]),
    "hallucination": ("Ảo giác về dữ liệu tool", "grounding",
                      "Model không đặt gì nhưng báo 'đã đặt VN999, 1.200.000đ' (bịa).",
                      {},
                      lambda on: [search()] + [HALLU() for _ in range(3 if on else 1)]),
    "drift": ("Trôi mục tiêu", "authz",
              "Model chạy theo 'rẻ nhất' và quên giờ bay >= 06:00: chọn VJ202 (05:10).",
              {},
              lambda on: ([search(), hold("VJ202"), hold("QH303"), pay(), OK_TEXT()] if on
                          else [search(), hold("VJ202"), pay(), AIMessage("Đã đặt VJ202 giá 1.300.000đ, rẻ nhất.")])),
    "state": ("Hỏng trạng thái do kết quả rỗng", "validate",
              "search lỗi nhưng im lặng trả {}; model hiểu thành 'không có chuyến bay nào'.",
              dict(search_mode="silent_empty"),
              lambda on: ([search() for _ in range(4)] if on
                          else [search(), AIMessage("Không có chuyến bay nào từ SGN đến HAN ngày 2026-10-15.")])),
}


def short(args):
    return ", ".join(f"{k}={v}" for k, v in args.items())


def run_case(key, on):
    title, layer, desc, world, make = MODES[key]
    WORLD.reset(**world)
    h = Harness(TASK, load_constraints(), layers=ALL_LAYERS if on else ())
    out, _ = run_agent("react", ScriptedLLM(make(on)), h, TASK.to_prompt())
    outcome = out["outcome"]
    truly_ok, errs = h.check_done(force=True)
    active = h.active_bookings()
    return {
        "key": key, "on": on, "outcome": outcome, "calls": h.calls, "llm_calls": out["usage"]["llm_calls"],
        "false_done": outcome == "done" and not truly_ok,
        "violation": any(h.flight_errors(b) for b in active),
        "reason": out.get("handoff", {}).get("reason", ""), "question": out.get("handoff", {}).get("question", ""),
        "trace": [f"{e['tool']}({short(e['args'])}) → {e['status']}" + (f": {e['result'][:90]}" if e["status"] != "OK" else "")
                  for e in h.log],
    }


def main():
    rows = [run_case(k, on) for k in MODES for on in (False, True)]
    md = ["# Demo ablation: 4 kiểu lỗi × harness tắt/bật (LLM giả có kịch bản, tái hiện 100%)\n",
          "| Lỗi | Lớp chống lỗi | Harness | Kết cục | Tool call | Báo xong nhưng sai | Booking vi phạm | Lý do dừng |",
          "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        title, layer, *_ = MODES[r["key"]]
        md.append(f"| {title} | `{layer}` | {'BẬT' if r['on'] else 'TẮT'} | {r['outcome']} | {r['calls']} | "
                  f"{'CÓ ❌' if r['false_done'] else 'không'} | {'CÓ ❌' if r['violation'] else 'không'} | {r['reason'] or '—'} |")
    md.append("")
    for k, (title, layer, desc, *_) in MODES.items():
        md.append(f"## {title} (lớp `{layer}`)\n\n{desc}\n")
        for r in [x for x in rows if x["key"] == k]:
            md.append(f"**Harness {'BẬT' if r['on'] else 'TẮT'}** — kết cục `{r['outcome']}`")
            md += [f"{i}. {t}" for i, t in enumerate(r["trace"], 1)] or ["(không gọi tool nào)"]
            if r["question"]:
                md.append(f"\nCâu hỏi bàn giao: {r['question']}")
            md.append("")
    text = "\n".join(md)
    print(text)
    os.makedirs("traces", exist_ok=True)
    with open(os.path.join("traces", "ablation_demo.md"), "w", encoding="utf-8") as f:
        f.write(text)
    print("\n→ đã lưu traces/ablation_demo.md")


if __name__ == "__main__":
    main()
