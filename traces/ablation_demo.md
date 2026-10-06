# Demo ablation: 4 kiểu lỗi × harness tắt/bật (LLM giả có kịch bản, tái hiện 100%)

| Lỗi | Lớp chống lỗi | Harness | Kết cục | Tool call | Báo xong nhưng sai | Booking vi phạm | Lý do dừng |
|---|---|---|---|---|---|---|---|
| Vòng lặp vô hạn | `loop` | TẮT | handoff | 12 | không | không | hết ngân sách 12 lần gọi LLM |
| Vòng lặp vô hạn | `loop` | BẬT | handoff | 3 | không | không | lặp: gọi lại search_flights cùng tham số và cùng kết quả 3 lần |
| Ảo giác về dữ liệu tool | `grounding` | TẮT | done | 1 | CÓ ❌ | không | — |
| Ảo giác về dữ liệu tool | `grounding` | BẬT | handoff | 1 | không | không | ảo giác: câu trả lời chứa dữ kiện KHÔNG có trong kết quả tool: ['1200000', 'VN999'] |
| Trôi mục tiêu | `authz` | TẮT | done | 3 | CÓ ❌ | CÓ ❌ | — |
| Trôi mục tiêu | `authz` | BẬT | done | 4 | không | không | — |
| Hỏng trạng thái do kết quả rỗng | `validate` | TẮT | done | 1 | CÓ ❌ | không | — |
| Hỏng trạng thái do kết quả rỗng | `validate` | BẬT | handoff | 3 | không | không | lặp: gọi lại search_flights cùng tham số và cùng kết quả 3 lần |

## Vòng lặp vô hạn (lớp `loop`)

Tool chỉ trả lỗi mơ hồ 'not found' nên model cứ gọi lại y hệt.

**Harness TẮT** — kết cục `handoff`
1. search_flights(origin=SGN, dest=HAN, date=2026-10-15) → OK
2. search_flights(origin=SGN, dest=HAN, date=2026-10-15) → OK
3. search_flights(origin=SGN, dest=HAN, date=2026-10-15) → OK
4. search_flights(origin=SGN, dest=HAN, date=2026-10-15) → OK
5. search_flights(origin=SGN, dest=HAN, date=2026-10-15) → OK
6. search_flights(origin=SGN, dest=HAN, date=2026-10-15) → OK
7. search_flights(origin=SGN, dest=HAN, date=2026-10-15) → OK
8. search_flights(origin=SGN, dest=HAN, date=2026-10-15) → OK
9. search_flights(origin=SGN, dest=HAN, date=2026-10-15) → OK
10. search_flights(origin=SGN, dest=HAN, date=2026-10-15) → OK
11. search_flights(origin=SGN, dest=HAN, date=2026-10-15) → OK
12. search_flights(origin=SGN, dest=HAN, date=2026-10-15) → OK

**Harness BẬT** — kết cục `handoff`
1. search_flights(origin=SGN, dest=HAN, date=2026-10-15) → ERROR: {"status": "error", "error": "not found"}
2. search_flights(origin=SGN, dest=HAN, date=2026-10-15) → ERROR: {"status": "error", "error": "not found"}
3. search_flights(origin=SGN, dest=HAN, date=2026-10-15) → ERROR: {"status": "error", "error": "not found"}

Câu hỏi bàn giao: Tool search_flights liên tục trả '{"status": "error", "error": "not found"}' với tham số {"origin": "SGN", "dest": "HAN", "date": "2026-10-15"}. Tham số có sai định dạng hoặc dịch vụ đang lỗi không?

## Ảo giác về dữ liệu tool (lớp `grounding`)

Model không đặt gì nhưng báo 'đã đặt VN999, 1.200.000đ' (bịa).

**Harness TẮT** — kết cục `done`
1. search_flights(origin=SGN, dest=HAN, date=2026-10-15) → OK

**Harness BẬT** — kết cục `handoff`
1. search_flights(origin=SGN, dest=HAN, date=2026-10-15) → OK

Câu hỏi bàn giao: Câu trả lời của agent chứa dữ kiện KHÔNG có trong kết quả tool. Có cho agent tìm kiếm và đặt lại không?

## Trôi mục tiêu (lớp `authz`)

Model chạy theo 'rẻ nhất' và quên giờ bay >= 06:00: chọn VJ202 (05:10).

**Harness TẮT** — kết cục `done`
1. search_flights(origin=SGN, dest=HAN, date=2026-10-15) → OK
2. hold_seat(flight_id=VJ202, passenger=Nguyen Van A) → OK
3. pay(booking_id=BK001) → OK

**Harness BẬT** — kết cục `done`
1. search_flights(origin=SGN, dest=HAN, date=2026-10-15) → OK
2. hold_seat(flight_id=VJ202, passenger=Nguyen Van A) → DENIED: giờ bay 05:10 sớm hơn 06:00
3. hold_seat(flight_id=QH303, passenger=Nguyen Van A) → OK
4. pay(booking_id=BK001) → OK

## Hỏng trạng thái do kết quả rỗng (lớp `validate`)

search lỗi nhưng im lặng trả {}; model hiểu thành 'không có chuyến bay nào'.

**Harness TẮT** — kết cục `done`
1. search_flights(origin=SGN, dest=HAN, date=2026-10-15) → OK

**Harness BẬT** — kết cục `handoff`
1. search_flights(origin=SGN, dest=HAN, date=2026-10-15) → ERROR: EMPTY RESULT: search_flights trả về rỗng/thiếu 'status'. Đây là LỖI TOOL, KHÔNG phải 'khôn
2. search_flights(origin=SGN, dest=HAN, date=2026-10-15) → ERROR: EMPTY RESULT: search_flights trả về rỗng/thiếu 'status'. Đây là LỖI TOOL, KHÔNG phải 'khôn
3. search_flights(origin=SGN, dest=HAN, date=2026-10-15) → ERROR: EMPTY RESULT: search_flights trả về rỗng/thiếu 'status'. Đây là LỖI TOOL, KHÔNG phải 'khôn

Câu hỏi bàn giao: Dịch vụ search_flights trả kết quả RỖNG (có thể lỗi dịch vụ). Có thử lại sau hoặc kiểm tra dịch vụ không?
