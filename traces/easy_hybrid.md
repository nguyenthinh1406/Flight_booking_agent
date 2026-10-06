# Kịch bản `easy` · Pattern `hybrid`

**Mô tả kịch bản:** Có chuyến hợp lệ. Kỳ vọng: giữ chỗ và thanh toán chuyến rẻ nhất thỏa ràng buộc (QH303).

**Yêu cầu gửi cho agent:** Hãy đặt cho Nguyen Van A một vé bay SGN -> HAN ngày 2026-10-15, chọn chuyến rẻ nhất thỏa các ràng buộc. Giữ chỗ rồi thanh toán.

**Ràng buộc (dữ liệu):** `{"max_price": 5000000, "allowed_airlines": ["Vietnam Airlines", "Vietjet", "Bamboo"], "max_stops": 1, "must_depart_after": "06:00", "require_confirm_above": 3000000, "max_tool_calls": 15, "max_llm_calls": 12, "max_bad_streak": 3, "loop_k": 3}`  
**Các lớp harness bật:** authz, constraints, done, grounding, handoff, loop, validate

## Kết quả tổng quát

- Kết cục: **done**, ✅ ĐẠT kỳ vọng (kỳ vọng: done)
- Số tool call: 3 · Số lần gọi LLM: 7 · Token: 7538 · Thời gian: 9.4s
- Booking đang hiệu lực trong hệ thống: BK001 (chuyến QH303, 1.900.000đ, ĐÃ THANH TOÁN)

## Diễn biến từng bước

| # | Thời điểm | Thành phần | Hành động | Kết quả |
|---|---|---|---|---|
| 1 | +0.0s | LLM (lập kế hoạch) | Đề xuất kế hoạch: [   "search_flights",   "hold_seat",   "pay" ] | 369 token, 1.3s |
| 2 | +1.3s | LLM (chọn tool) | Yêu cầu gọi `search_flights(dest=HAN, date=2026-10-15, origin=SGN)` | 719 token, 1.3s |
| 3 | +2.6s | Harness → tool | `search_flights(dest=HAN, date=2026-10-15, origin=SGN)` | Kiểm quyền: ALLOW. Kết quả: 5 chuyến: VN101 Vietnam Airlines 06:30 2.400.000đ 0 dừng; VJ202 Vietjet 05:10 1.300.000đ 0 dừng; QH303 Bamboo 09:00 1.900.000đ 0 dừng; VN404 Vietnam Airlines 18:00 6.200.000đ 0 dừng; XX707 Vietjet 10:00 1.000.000đ 2 dừng |
| 4 | +2.6s | LLM (chọn tool) | Trả lời: Đã thực hiện xong bước 1 (`search_flights`). Kết quả trả về các chuyến bay từ SGN đi HAN ngày 2026-10-15: 1. `VJ202` (Vietjet) - 05:10 - 1.300.000 VNĐ - 0 điểm dừng (Không thỏa mãn ràng buộc khởi hành sau 06:00) 2. `VN101` (Vietnam Airlines) - 06:30 - 2.400.000 VNĐ - 0 điểm dừng (Thỏa mãn mọi ràng b | 1446 token, 2.2s |
| 5 | +4.8s | LLM (chọn tool) | Yêu cầu gọi `hold_seat(passenger=Nguyen Van A, flight_id=QH303)` | 1107 token, 0.9s |
| 6 | +5.7s | Harness → tool | `hold_seat(passenger=Nguyen Van A, flight_id=QH303)` | Kiểm quyền: ALLOW. Kết quả: booking BK001 [HELD, chưa thanh toán]: chuyến QH303 (Bamboo), 09:00, 1.900.000đ |
| 7 | +5.7s | LLM (chọn tool) | Trả lời: Đã giữ chỗ thành công cho hành khách Nguyen Van A trên chuyến bay QH303 (Bamboo, khởi hành lúc 09:00 ngày 2026-10-15, giá 1.900.000 VNĐ) với mã booking: BK001. | 1285 token, 1.3s |
| 8 | +7.0s | LLM (chọn tool) | Yêu cầu gọi `pay(booking_id=BK001)` | 1230 token, 1.2s |
| 9 | +8.1s | Harness → tool | `pay(booking_id=BK001)` | Kiểm quyền: ALLOW. Kết quả: booking BK001 [PAID, đã thanh toán]: chuyến QH303 (Bamboo), 09:00, 1.900.000đ |
| 10 | +8.2s | LLM (chọn tool) | Trả lời: Đã hoàn tất việc thanh toán cho chuyến bay QH303 của hành khách Nguyen Van A với mã đặt chỗ BK001 (giá 1.900.000 VND). | 1382 token, 1.2s |
| 11 | +9.4s | Harness (check_done) | Kiểm tra tiêu chí hoàn thành bằng code | ✅ đạt |

## Chi tiết

**Bước 1 (+0.0s): LLM (lập kế hoạch)**
- Agent nhìn thấy (tin nhắn cuối): `[HumanMessage] Hãy đặt cho Nguyen Van A một vé bay SGN -> HAN ngày 2026-10-15, chọn chuyến rẻ nhất thỏa các ràng buộc. Giữ chỗ rồi thanh toán.`
- Đề xuất kế hoạch: [   "search_flights",   "hold_seat",   "pay" ]
- 369 token, 1.3s

**Bước 2 (+1.3s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[HumanMessage] Yêu cầu gốc: Hãy đặt cho Nguyen Van A một vé bay SGN -> HAN ngày 2026-10-15, chọn chuyến rẻ nhất thỏa các ràng buộc. Giữ chỗ rồi thanh toán. Kế hoạch: ['search_flights', 'hold_seat', 'pay'] Đã làm: (chưa làm gì)  Bây giờ CHỈ thực hiện bước 1: search_flights`
- Yêu cầu gọi `search_flights(dest=HAN, date=2026-10-15, origin=SGN)`
- 719 token, 1.3s

**Bước 3 (+2.6s): Harness → tool**
- `search_flights(dest=HAN, date=2026-10-15, origin=SGN)`
- Kiểm quyền: ALLOW. Kết quả: 5 chuyến: VN101 Vietnam Airlines 06:30 2.400.000đ 0 dừng; VJ202 Vietjet 05:10 1.300.000đ 0 dừng; QH303 Bamboo 09:00 1.900.000đ 0 dừng; VN404 Vietnam Airlines 18:00 6.200.000đ 0 dừng; XX707 Vietjet 10:00 1.000.000đ 2 dừng

**Bước 4 (+2.6s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[ToolMessage] {"status": "ok", "flights": [{"id": "VN101", "airline": "Vietnam Airlines", "origin": "SGN", "dest": "HAN", "date": "2026-10-15", "depart": "06:30", "price": 2400000, "stops": 0}, {"id": "VJ202", "airline": "Vietjet", "origin": "SGN", "dest": "HAN", "date": "2026-10-15", "depart": "05:10", "price": 1300000, "stops": 0}, {"id": "QH303"`
- Trả lời: Đã thực hiện xong bước 1 (`search_flights`). Kết quả trả về các chuyến bay từ SGN đi HAN ngày 2026-10-15: 1. `VJ202` (Vietjet) - 05:10 - 1.300.000 VNĐ - 0 điểm dừng (Không thỏa mãn ràng buộc khởi hành sau 06:00) 2. `VN101` (Vietnam Airlines) - 06:30 - 2.400.000 VNĐ - 0 điểm dừng (Thỏa mãn mọi ràng b
- 1446 token, 2.2s

**Bước 5 (+4.8s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[HumanMessage] Yêu cầu gốc: Hãy đặt cho Nguyen Van A một vé bay SGN -> HAN ngày 2026-10-15, chọn chuyến rẻ nhất thỏa các ràng buộc. Giữ chỗ rồi thanh toán. Kế hoạch: ['search_flights', 'hold_seat', 'pay'] Đã làm: - search_flights({"dest": "HAN", "date": "2026-10-15", "origin": "SGN"}) -> OK: {"status": "ok", "flights": [{"id": "VN101", "airline": "`
- Yêu cầu gọi `hold_seat(passenger=Nguyen Van A, flight_id=QH303)`
- 1107 token, 0.9s

**Bước 6 (+5.7s): Harness → tool**
- `hold_seat(passenger=Nguyen Van A, flight_id=QH303)`
- Kiểm quyền: ALLOW. Kết quả: booking BK001 [HELD, chưa thanh toán]: chuyến QH303 (Bamboo), 09:00, 1.900.000đ

**Bước 7 (+5.7s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[ToolMessage] {"status": "ok", "booking_id": "BK001", "passenger": "Nguyen Van A", "state": "HELD", "paid": false, "id": "QH303", "airline": "Bamboo", "origin": "SGN", "dest": "HAN", "date": "2026-10-15", "depart": "09:00", "price": 1900000, "stops": 0}`
- Trả lời: Đã giữ chỗ thành công cho hành khách Nguyen Van A trên chuyến bay QH303 (Bamboo, khởi hành lúc 09:00 ngày 2026-10-15, giá 1.900.000 VNĐ) với mã booking: BK001.
- 1285 token, 1.3s

**Bước 8 (+7.0s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[HumanMessage] Yêu cầu gốc: Hãy đặt cho Nguyen Van A một vé bay SGN -> HAN ngày 2026-10-15, chọn chuyến rẻ nhất thỏa các ràng buộc. Giữ chỗ rồi thanh toán. Kế hoạch: ['search_flights', 'hold_seat', 'pay'] Đã làm: - search_flights({"dest": "HAN", "date": "2026-10-15", "origin": "SGN"}) -> OK: {"status": "ok", "flights": [{"id": "VN101", "airline": "`
- Yêu cầu gọi `pay(booking_id=BK001)`
- 1230 token, 1.2s

**Bước 9 (+8.1s): Harness → tool**
- `pay(booking_id=BK001)`
- Kiểm quyền: ALLOW. Kết quả: booking BK001 [PAID, đã thanh toán]: chuyến QH303 (Bamboo), 09:00, 1.900.000đ

**Bước 10 (+8.2s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[ToolMessage] {"status": "ok", "booking_id": "BK001", "passenger": "Nguyen Van A", "state": "PAID", "paid": true, "id": "QH303", "airline": "Bamboo", "origin": "SGN", "dest": "HAN", "date": "2026-10-15", "depart": "09:00", "price": 1900000, "stops": 0}`
- Trả lời: Đã hoàn tất việc thanh toán cho chuyến bay QH303 của hành khách Nguyen Van A với mã đặt chỗ BK001 (giá 1.900.000 VND).
- 1382 token, 1.2s

**Bước 11 (+9.4s): Harness (check_done)**
- Kiểm tra tiêu chí hoàn thành bằng code
- ✅ đạt
