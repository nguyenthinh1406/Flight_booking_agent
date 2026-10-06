"""3 mẫu thiết kế agent trên LangGraph: ReAct, Plan-then-Execute, Hybrid.

Cả 3 dùng CHUNG tool + Harness; khác nhau ở cấu trúc đồ thị.
  react         : agent <-> tools, rồi check_done (kèm vòng sửa lỗi)
  plan_execute  : planner -> executor(từng bước, 1 lượt tool, KHÔNG quan sát lại/re-plan) -> check
  hybrid        : planner -> executor(từng bước = ReAct nhỏ) -> re-plan khi bước hỏng / check_done fail
"""
import json
import os
import re
import time
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from harness import Harness
from tools import TOOLS


def get_llm(model: str | None = None):
    """Cấu hình đọc từ .env: LLM_PROVIDER (google|ollama|openai), LLM_MODEL, LLM_BASE_URL (tuỳ chọn),
    GOOGLE_API_KEY (provider google) hoặc OPENAI_API_KEY (provider openai: mọi API tương thích OpenAI).
    Biến môi trường đã export sẵn được ưu tiên hơn .env."""
    from dotenv import load_dotenv

    load_dotenv()
    import logging
    logging.getLogger("google_genai").setLevel(logging.ERROR)   # ẩn cảnh báo AFC (chỉ là thông báo)

    provider = os.getenv("LLM_PROVIDER", "google").lower()
    name = model or os.getenv("LLM_MODEL", "gemini-2.5-flash")
    for prefix in ("google_genai:", "google_vertexai:", "google:"):   # chỉ bỏ tiền tố provider, giữ nguyên tên như qwen2.5:7b
        if name.startswith(prefix):
            name = name[len(prefix):]
    base_url = os.getenv("LLM_BASE_URL") or None   # để trống = endpoint mặc định

    if provider == "google":
        # Không dùng init_chat_model: nó suy ra provider từ tên "gemini-*" và có thể chọn nhầm Vertex AI.
        from langchain_google_genai import ChatGoogleGenerativeAI   # Gemini API (khoá AI Studio), KHÔNG phải Vertex
        kw = {"model": name, "temperature": 0,
              "timeout": float(os.getenv("LLM_TIMEOUT", "90")),          # tránh treo vô hạn khi 1 request bị kẹt
              "max_retries": int(os.getenv("LLM_MAX_RETRIES", "2"))}     # mặc định của thư viện cao hơn, dễ làm chạy rất lâu khi bị 429
        if base_url:
            kw["base_url"] = base_url
        if os.getenv("LLM_THINKING_BUDGET"):                             # tuỳ chọn: 0 = tắt "suy nghĩ" -> nhanh hơn nhiều (model hỗ trợ)
            kw["thinking_budget"] = int(os.environ["LLM_THINKING_BUDGET"])
        return ChatGoogleGenerativeAI(**kw)
    raise ValueError(f"LLM_PROVIDER không hợp lệ: {provider} (chọn google | ollama | openai)")


class CountingLLM:
    """Bọc LLM để (1) cộng dồn token THẬT (usage_metadata), (2) ghi lại từng lần gọi LLM cho bản ghi diễn biến."""

    def __init__(self, llm, usage=None, events=None, bound=False):
        self.llm = llm
        self.usage = usage if usage is not None else {"tokens": 0, "llm_calls": 0}
        self.events = events if events is not None else []
        self.bound = bound            # True: LLM có gắn tool (chọn tool); False: LLM thường (vd. planner)

    def bind_tools(self, tools):
        return CountingLLM(self.llm.bind_tools(tools), self.usage, self.events, bound=True)

    def invoke(self, *args, **kwargs):
        t0 = time.time()
        r = self.llm.invoke(*args, **kwargs)
        t1 = time.time()
        u = getattr(r, "usage_metadata", None) or {}
        tokens = u.get("total_tokens") or (u.get("input_tokens", 0) + u.get("output_tokens", 0))
        self.usage["tokens"] += tokens
        self.usage["llm_calls"] += 1
        msgs = args[0] if args else kwargs.get("input")
        if isinstance(msgs, list) and msgs:
            last = f"[{type(msgs[-1]).__name__}] {_text(msgs[-1])}"
        else:
            last = str(msgs)
        self.events.append({
            "kind": "llm", "t_start": t0, "t": t1, "ms": (t1 - t0) * 1000, "bound": self.bound,
            "input_last": last[:600], "text": _text(r)[:1500],
            "tool_calls": [(c["name"], c["args"]) for c in (getattr(r, "tool_calls", None) or [])],
            "tokens": tokens,
        })
        return r


class State(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    plan: list[str]
    step: int
    step_failed: bool
    replans: int
    retries: int
    outcome: str     # "done" | "handoff" | "replan"
    handoff: dict    # tên node KHÔNG được trùng tên key của state -> node đặt là "to_handoff"


def _text(msg) -> str:
    c = msg.content
    if isinstance(c, str):
        return c
    # Gemini có thể trả content là list các block: [{"type": "text", "text": "..."}, ...]
    return "".join(b if isinstance(b, str) else b.get("text", "") for b in c)


def _finalize_stop(h: Harness) -> dict:
    """Dừng vì ngân sách/lỗi liên tiếp: nếu thực ra đã xong thì vẫn tính là done."""
    ok, errs = h.check_done()
    if ok and "done" in h.layers:           # lớp done tắt thì không có cơ sở để khẳng định "đã xong"
        return {"outcome": "done"}
    return {"outcome": "handoff", "handoff": h.make_handoff(h.stop_reason or "; ".join(errs))}


# ═════════════════════════ 1. ReAct ═════════════════════════
def build_react(llm, h: Harness, max_retries: int = 2):
    llm_t = llm.bind_tools(list(TOOLS.values()))

    def agent(s: State):
        h.llm_calls += 1
        if h.llm_calls > h.c.max_llm_calls:                       # ngân sách số lần gọi LLM (luôn bật)
            h.stop_reason = f"hết ngân sách {h.c.max_llm_calls} lần gọi LLM"
            return {"messages": [AIMessage(content="(dừng: hết ngân sách gọi LLM)")]}
        return {"messages": [llm_t.invoke([SystemMessage(h.system_prompt())] + s["messages"])]}

    def tools(s: State):
        return {"messages": [h.execute(c) for c in s["messages"][-1].tool_calls]}

    def check(s: State):
        final = _text(s["messages"][-1])
        bad = h.ungrounded_facts(final) if "grounding" in h.layers else []   # dữ kiện không có trong kết quả tool
        ok, errs = h.check_done()
        problems = ([f"câu trả lời chứa dữ kiện KHÔNG có trong kết quả tool: {bad}"] if bad else []) + ([] if ok else errs)
        if not problems:
            return {"outcome": "done"}
        if s.get("retries", 0) >= max_retries:
            reason = ("ảo giác: " + problems[0]) if bad else "tiêu chí hoàn thành chưa đạt: " + "; ".join(errs)
            return {"outcome": "handoff", "handoff": h.make_handoff(reason)}
        return {"retries": s.get("retries", 0) + 1,
                "messages": [HumanMessage("CHƯA hoàn thành (hệ thống kiểm bằng code): " + "; ".join(problems))]}

    g = StateGraph(State)
    g.add_node("agent", agent)
    g.add_node("tools", tools)
    g.add_node("check", check)
    g.add_node("to_handoff", lambda s: _finalize_stop(h))
    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", lambda s: ("to_handoff" if h.should_stop else
                                                 "tools" if getattr(s["messages"][-1], "tool_calls", None) else "check"),
                            {"to_handoff": "to_handoff", "tools": "tools", "check": "check"})
    g.add_conditional_edges("tools", lambda s: "to_handoff" if h.should_stop else "agent",
                            {"to_handoff": "to_handoff", "agent": "agent"})
    g.add_conditional_edges("check", lambda s: END if s.get("outcome") else "agent", {END: END, "agent": "agent"})
    g.add_edge("to_handoff", END)
    return g.compile()


# ═════════════════ 2 & 3. Plan-then-Execute / Hybrid ═════════════════
PLANNER_INSTR = ('\nHãy lập kế hoạch. CHỈ trả về một mảng JSON gồm 3-5 bước ngắn (chuỗi), '
                 'ví dụ ["Tìm chuyến bay", "Chọn chuyến rẻ nhất thỏa ràng buộc", "Đặt vé"].')


def parse_plan(text: str) -> list[str]:
    m = re.search(r"\[.*\]", text, re.S)
    try:
        plan = [str(x) for x in json.loads(m.group(0))]
    except Exception:
        plan = [ln.strip("-•* 0123456789.") for ln in text.splitlines() if ln.strip()]
    return plan[:6] or ["Thực hiện yêu cầu của người dùng"]


def build_plan_graph(llm, h: Harness, replan: bool, max_turns: int, max_replans: int = 2):
    llm_t = llm.bind_tools(list(TOOLS.values()))

    def planner(s: State):
        n = s.get("replans", -1) + 1
        request = s["messages"][0].content
        if n > 0:
            request += f"\n\nKế hoạch trước chưa thành công. Đã thực hiện:\n{h.progress()}\nHãy lập kế hoạch MỚI để sửa."
        raw = llm.invoke([SystemMessage(h.system_prompt() + PLANNER_INSTR), HumanMessage(request)])
        plan = parse_plan(_text(raw))
        return {"plan": plan, "step": 0, "step_failed": False, "replans": n,
                "messages": [AIMessage(f"[planner #{n}] {plan}")]}

    def executor(s: State):
        i, plan = s["step"], s["plan"]
        msgs = [SystemMessage(h.system_prompt()),
                HumanMessage(f"Yêu cầu gốc: {s['messages'][0].content}\nKế hoạch: {plan}\n"
                             f"Đã làm:\n{h.progress()}\n\nBây giờ CHỈ thực hiện bước {i + 1}: {plan[i]}")]
        failed = False
        for _ in range(max_turns):            # max_turns=1: không quan sát lại; >1: ReAct nhỏ
            ai = llm_t.invoke(msgs)
            msgs.append(ai)
            if not getattr(ai, "tool_calls", None):
                break
            for c in ai.tool_calls:
                tm = h.execute(c)
                msgs.append(tm)
                failed |= tm.content.startswith(("ERROR", "DENIED"))
            if h.should_stop:
                break
        return {"step": i + 1, "step_failed": failed,
                "messages": [AIMessage(f"[step {i + 1}] {'FAILED' if failed else 'ok'}: {plan[i]}")]}

    def check(s: State):
        ok, errs = h.check_done()
        if ok:
            return {"outcome": "done"}
        if replan and s.get("replans", 0) < max_replans:
            return {"outcome": "replan"}
        return {"outcome": "handoff", "handoff": h.make_handoff("tiêu chí hoàn thành chưa đạt: " + "; ".join(errs))}

    def route_exec(s: State):
        if h.should_stop:
            return "to_handoff"
        if s["step_failed"] and replan and s.get("replans", 0) < max_replans:
            return "planner"                   # chỉ Hybrid mới re-plan giữa chừng
        return "executor" if s["step"] < len(s["plan"]) else "check"

    g = StateGraph(State)
    g.add_node("planner", planner)
    g.add_node("executor", executor)
    g.add_node("check", check)
    g.add_node("to_handoff", lambda s: _finalize_stop(h))
    g.add_edge(START, "planner")
    g.add_edge("planner", "executor")
    g.add_conditional_edges("executor", route_exec,
                            {"to_handoff": "to_handoff", "planner": "planner", "executor": "executor", "check": "check"})
    g.add_conditional_edges("check", lambda s: {"done": END, "handoff": END, "replan": "planner"}[s["outcome"]],
                            {END: END, "planner": "planner"})
    g.add_edge("to_handoff", END)
    return g.compile()


PATTERNS = {
    "react": lambda llm, h: build_react(llm, h),
    "plan_execute": lambda llm, h: build_plan_graph(llm, h, replan=False, max_turns=1),
    "hybrid": lambda llm, h: build_plan_graph(llm, h, replan=True, max_turns=4),
}


def run_agent(pattern: str, llm, h: Harness, user_prompt: str):
    counter = CountingLLM(llm)
    graph = PATTERNS[pattern](counter, h)
    t0 = time.time()
    out = graph.invoke({"messages": [HumanMessage(user_prompt)]}, {"recursion_limit": 100})
    out["usage"] = counter.usage
    out["llm_events"] = counter.events
    return out, time.time() - t0