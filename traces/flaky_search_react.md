# Kịch bản `flaky_search` · Pattern `react`

**Mô tả kịch bản:** Lần search đầu tiên bị timeout (lỗi tạm thời). Kỳ vọng: agent thử lại, bộ phát hiện lặp không báo nhầm.

**Yêu cầu gửi cho agent:** Hãy đặt cho Nguyen Van A một vé bay SGN -> HAN ngày 2026-10-15, chọn chuyến rẻ nhất thỏa các ràng buộc. Giữ chỗ rồi thanh toán.

**Ràng buộc (dữ liệu):** `{"max_price": 5000000, "allowed_airlines": ["Vietnam Airlines", "Vietjet", "Bamboo"], "max_stops": 1, "must_depart_after": "06:00", "require_confirm_above": 3000000, "max_tool_calls": 15, "max_llm_calls": 12, "max_bad_streak": 3, "loop_k": 3}`  
**Các lớp harness bật:** authz, constraints, done, grounding, handoff, loop, validate

## Kết quả tổng quát

- Kết cục: **done**, ✅ ĐẠT kỳ vọng (kỳ vọng: done)
- Số tool call: 5 · Số lần gọi LLM: 7 · Token: 8550 · Thời gian: 8.0s
- Booking đang hiệu lực trong hệ thống: BK001 (chuyến QH303, 1.900.000đ, ĐÃ THANH TOÁN)

## Diễn biến từng bước

| # | Thời điểm | Thành phần | Hành động | Kết quả |
|---|---|---|---|---|
| 1 | +0.0s | LLM (chọn tool) | Yêu cầu gọi `search_flights(date=2026-10-15, origin=SGN, dest=HAN)` | 669 token, 1.2s |
| 2 | +1.3s | Harness → tool | `search_flights(date=2026-10-15, origin=SGN, dest=HAN)` | Kiểm quyền: ALLOW. Kết quả: **ERROR**: TimeoutError: search service timeout |
| 3 | +1.3s | LLM (chọn tool) | Yêu cầu gọi `search_flights(dest=HAN, origin=SGN, date=2026-10-15)` | 728 token, 1.0s |
| 4 | +2.2s | Harness → tool | `search_flights(dest=HAN, origin=SGN, date=2026-10-15)` | Kiểm quyền: ALLOW. Kết quả: 5 chuyến: VN101 Vietnam Airlines 06:30 2.400.000đ 0 dừng; VJ202 Vietjet 05:10 1.300.000đ 0 dừng; QH303 Bamboo 09:00 1.900.000đ 0 dừng; VN404 Vietnam Airlines 18:00 6.200.000đ 0 dừng; XX707 Vietjet 10:00 1.000.000đ 2 dừng |
| 5 | +2.2s | LLM (chọn tool) | Yêu cầu gọi `hold_seat(passenger=Nguyen Van A, flight_id=QH303)` | 1113 token, 1.1s |
| 6 | +3.4s | Harness → tool | `hold_seat(passenger=Nguyen Van A, flight_id=QH303)` | Kiểm quyền: ALLOW. Kết quả: booking BK001 [HELD, chưa thanh toán]: chuyến QH303 (Bamboo), 09:00, 1.900.000đ |
| 7 | +3.4s | LLM (chọn tool) | Yêu cầu gọi `pay(booking_id=BK001)` | 1243 token, 0.8s |
| 8 | +4.2s | Harness → tool | `pay(booking_id=BK001)` | Kiểm quyền: ALLOW. Kết quả: booking BK001 [PAID, đã thanh toán]: chuyến QH303 (Bamboo), 09:00, 1.900.000đ |
| 9 | +4.2s | LLM (chọn tool) | Trả lời: Đã đặt vé thành công cho hành khách **Nguyen Van A** tuyến **SGN -> HAN** ngày **2026-10-15**.  - **Chuyến bay:** QH303 (Bamboo Airways) - **Giờ khởi hành:** 09:00 (thỏa mãn điều kiện bay sau 06:00, tối đa 1 điểm dừng, hãng cho phép và giá vé dưới 5.000.000 VNĐ) - **Giá vé:** 1.900.000 VNĐ - **Mã gi | 1508 token, 1.7s |
| 10 | +5.9s | Harness (check_done) | Kiểm tra tiêu chí hoàn thành bằng code | ✅ đạt |
| 11 | +5.9s | LLM (chọn tool) | Yêu cầu gọi `get_flight_details(flight_id=QH303)` | 1569 token, 1.1s |
| 12 | +7.1s | Harness → tool | `get_flight_details(flight_id=QH303)` | Kiểm quyền: ALLOW. Kết quả: {"status": "ok", "id": "QH303", "airline": "Bamboo", "origin": "SGN", "dest": "HAN", "date": "2026-10-15", "depart": "09:00", "price": 1900000, "stops": 0, "baggage_kg": 20} |
| 13 | +7.1s | LLM (chọn tool) | Trả lời: Đã đặt vé máy bay cho Nguyen Van A từ SGN đi HAN ngày 2026-10-15. Mã chuyến bay: QH303. Giá: 1900000. Booking ID: BK001. | 1720 token, 0.9s |
| 14 | +8.0s | Harness (check_done) | Kiểm tra tiêu chí hoàn thành bằng code | ✅ đạt |

## Chi tiết

**Bước 1 (+0.0s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[HumanMessage] Hãy đặt cho Nguyen Van A một vé bay SGN -> HAN ngày 2026-10-15, chọn chuyến rẻ nhất thỏa các ràng buộc. Giữ chỗ rồi thanh toán.`
- Yêu cầu gọi `search_flights(date=2026-10-15, origin=SGN, dest=HAN)`
- 669 token, 1.2s

**Bước 2 (+1.3s): Harness → tool**
- `search_flights(date=2026-10-15, origin=SGN, dest=HAN)`
- Kiểm quyền: ALLOW. Kết quả: **ERROR**: TimeoutError: search service timeout

**Bước 3 (+1.3s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[ToolMessage] ERROR: TimeoutError: search service timeout`
- Yêu cầu gọi `search_flights(dest=HAN, origin=SGN, date=2026-10-15)`
- 728 token, 1.0s

**Bước 4 (+2.2s): Harness → tool**
- `search_flights(dest=HAN, origin=SGN, date=2026-10-15)`
- Kiểm quyền: ALLOW. Kết quả: 5 chuyến: VN101 Vietnam Airlines 06:30 2.400.000đ 0 dừng; VJ202 Vietjet 05:10 1.300.000đ 0 dừng; QH303 Bamboo 09:00 1.900.000đ 0 dừng; VN404 Vietnam Airlines 18:00 6.200.000đ 0 dừng; XX707 Vietjet 10:00 1.000.000đ 2 dừng

**Bước 5 (+2.2s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[ToolMessage] {"status": "ok", "flights": [{"id": "VN101", "airline": "Vietnam Airlines", "origin": "SGN", "dest": "HAN", "date": "2026-10-15", "depart": "06:30", "price": 2400000, "stops": 0}, {"id": "VJ202", "airline": "Vietjet", "origin": "SGN", "dest": "HAN", "date": "2026-10-15", "depart": "05:10", "price": 1300000, "stops": 0}, {"id": "QH303"`
- Yêu cầu gọi `hold_seat(passenger=Nguyen Van A, flight_id=QH303)`
- 1113 token, 1.1s

**Bước 6 (+3.4s): Harness → tool**
- `hold_seat(passenger=Nguyen Van A, flight_id=QH303)`
- Kiểm quyền: ALLOW. Kết quả: booking BK001 [HELD, chưa thanh toán]: chuyến QH303 (Bamboo), 09:00, 1.900.000đ

**Bước 7 (+3.4s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[ToolMessage] {"status": "ok", "booking_id": "BK001", "passenger": "Nguyen Van A", "state": "HELD", "paid": false, "id": "QH303", "airline": "Bamboo", "origin": "SGN", "dest": "HAN", "date": "2026-10-15", "depart": "09:00", "price": 1900000, "stops": 0}`
- Yêu cầu gọi `pay(booking_id=BK001)`
- 1243 token, 0.8s

**Bước 8 (+4.2s): Harness → tool**
- `pay(booking_id=BK001)`
- Kiểm quyền: ALLOW. Kết quả: booking BK001 [PAID, đã thanh toán]: chuyến QH303 (Bamboo), 09:00, 1.900.000đ

**Bước 9 (+4.2s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[ToolMessage] {"status": "ok", "booking_id": "BK001", "passenger": "Nguyen Van A", "state": "PAID", "paid": true, "id": "QH303", "airline": "Bamboo", "origin": "SGN", "dest": "HAN", "date": "2026-10-15", "depart": "09:00", "price": 1900000, "stops": 0}`
- Trả lời: Đã đặt vé thành công cho hành khách **Nguyen Van A** tuyến **SGN -> HAN** ngày **2026-10-15**.  - **Chuyến bay:** QH303 (Bamboo Airways) - **Giờ khởi hành:** 09:00 (thỏa mãn điều kiện bay sau 06:00, tối đa 1 điểm dừng, hãng cho phép và giá vé dưới 5.000.000 VNĐ) - **Giá vé:** 1.900.000 VNĐ - **Mã gi
- 1508 token, 1.7s

**Bước 10 (+5.9s): Harness (check_done)**
- Kiểm tra tiêu chí hoàn thành bằng code
- ✅ đạt

**Bước 11 (+5.9s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[HumanMessage] CHƯA hoàn thành (hệ thống kiểm bằng code): câu trả lời chứa dữ kiện KHÔNG có trong kết quả tool: ['5000000']`
- Yêu cầu gọi `get_flight_details(flight_id=QH303)`
- 1569 token, 1.1s

**Bước 12 (+7.1s): Harness → tool**
- `get_flight_details(flight_id=QH303)`
- Kiểm quyền: ALLOW. Kết quả: {"status": "ok", "id": "QH303", "airline": "Bamboo", "origin": "SGN", "dest": "HAN", "date": "2026-10-15", "depart": "09:00", "price": 1900000, "stops": 0, "baggage_kg": 20}

**Bước 13 (+7.1s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[ToolMessage] {"status": "ok", "id": "QH303", "airline": "Bamboo", "origin": "SGN", "dest": "HAN", "date": "2026-10-15", "depart": "09:00", "price": 1900000, "stops": 0, "baggage_kg": 20}`
- Trả lời: Đã đặt vé máy bay cho Nguyen Van A từ SGN đi HAN ngày 2026-10-15. Mã chuyến bay: QH303. Giá: 1900000. Booking ID: BK001.
- 1720 token, 0.9s

**Bước 14 (+8.0s): Harness (check_done)**
- Kiểm tra tiêu chí hoàn thành bằng code
- ✅ đạt
