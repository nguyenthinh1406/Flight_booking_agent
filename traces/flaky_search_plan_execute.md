# Kịch bản `flaky_search` · Pattern `plan_execute`

**Mô tả kịch bản:** Lần search đầu tiên bị timeout (lỗi tạm thời). Kỳ vọng: agent thử lại, bộ phát hiện lặp không báo nhầm.

**Yêu cầu gửi cho agent:** Hãy đặt cho Nguyen Van A một vé bay SGN -> HAN ngày 2026-10-15, chọn chuyến rẻ nhất thỏa các ràng buộc. Giữ chỗ rồi thanh toán.

**Ràng buộc (dữ liệu):** `{"max_price": 5000000, "allowed_airlines": ["Vietnam Airlines", "Vietjet", "Bamboo"], "max_stops": 1, "must_depart_after": "06:00", "require_confirm_above": 3000000, "max_tool_calls": 15, "max_llm_calls": 12, "max_bad_streak": 3, "loop_k": 3}`  
**Các lớp harness bật:** authz, constraints, done, grounding, handoff, loop, validate

## Kết quả tổng quát

- Kết cục: **done**, ✅ ĐẠT kỳ vọng (kỳ vọng: done)
- Số tool call: 4 · Số lần gọi LLM: 5 · Token: 4552 · Thời gian: 5.3s
- Booking đang hiệu lực trong hệ thống: BK001 (chuyến QH303, 1.900.000đ, ĐÃ THANH TOÁN)

## Diễn biến từng bước

| # | Thời điểm | Thành phần | Hành động | Kết quả |
|---|---|---|---|---|
| 1 | +0.0s | LLM (lập kế hoạch) | Đề xuất kế hoạch: ```json [   "Tìm chuyến bay từ SGN đi HAN ngày 2026-10-15",   "Chọn chuyến bay rẻ nhất thỏa mãn ràng buộc giá, hãng, số điểm dừng và giờ khởi hành",   "Giữ chỗ cho hành khách Nguyen Van A",   "Thanh toán vé" ] ``` | 424 token, 1.0s |
| 2 | +1.0s | LLM (chọn tool) | Yêu cầu gọi `search_flights(dest=HAN, date=2026-10-15, origin=SGN)` | 784 token, 1.1s |
| 3 | +2.1s | Harness → tool | `search_flights(dest=HAN, date=2026-10-15, origin=SGN)` | Kiểm quyền: ALLOW. Kết quả: **ERROR**: TimeoutError: search service timeout |
| 4 | +2.1s | LLM (chọn tool) | Yêu cầu gọi `search_flights(date=2026-10-15, dest=HAN, origin=SGN)` | 819 token, 1.1s |
| 5 | +3.2s | Harness → tool | `search_flights(date=2026-10-15, dest=HAN, origin=SGN)` | Kiểm quyền: ALLOW. Kết quả: 5 chuyến: VN101 Vietnam Airlines 06:30 2.400.000đ 0 dừng; VJ202 Vietjet 05:10 1.300.000đ 0 dừng; QH303 Bamboo 09:00 1.900.000đ 0 dừng; VN404 Vietnam Airlines 18:00 6.200.000đ 0 dừng; XX707 Vietjet 10:00 1.000.000đ 2 dừng |
| 6 | +3.2s | LLM (chọn tool) | Yêu cầu gọi `hold_seat(passenger=Nguyen Van A, flight_id=QH303)` | 1203 token, 0.9s |
| 7 | +4.1s | Harness → tool | `hold_seat(passenger=Nguyen Van A, flight_id=QH303)` | Kiểm quyền: ALLOW. Kết quả: booking BK001 [HELD, chưa thanh toán]: chuyến QH303 (Bamboo), 09:00, 1.900.000đ |
| 8 | +4.1s | LLM (chọn tool) | Yêu cầu gọi `pay(booking_id=BK001)` | 1322 token, 1.2s |
| 9 | +5.3s | Harness → tool | `pay(booking_id=BK001)` | Kiểm quyền: ALLOW. Kết quả: booking BK001 [PAID, đã thanh toán]: chuyến QH303 (Bamboo), 09:00, 1.900.000đ |
| 10 | +5.3s | Harness (check_done) | Kiểm tra tiêu chí hoàn thành bằng code | ✅ đạt |

## Chi tiết

**Bước 1 (+0.0s): LLM (lập kế hoạch)**
- Agent nhìn thấy (tin nhắn cuối): `[HumanMessage] Hãy đặt cho Nguyen Van A một vé bay SGN -> HAN ngày 2026-10-15, chọn chuyến rẻ nhất thỏa các ràng buộc. Giữ chỗ rồi thanh toán.`
- Đề xuất kế hoạch: ```json [   "Tìm chuyến bay từ SGN đi HAN ngày 2026-10-15",   "Chọn chuyến bay rẻ nhất thỏa mãn ràng buộc giá, hãng, số điểm dừng và giờ khởi hành",   "Giữ chỗ cho hành khách Nguyen Van A",   "Thanh toán vé" ] ```
- 424 token, 1.0s

**Bước 2 (+1.0s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[HumanMessage] Yêu cầu gốc: Hãy đặt cho Nguyen Van A một vé bay SGN -> HAN ngày 2026-10-15, chọn chuyến rẻ nhất thỏa các ràng buộc. Giữ chỗ rồi thanh toán. Kế hoạch: ['Tìm chuyến bay từ SGN đi HAN ngày 2026-10-15', 'Chọn chuyến bay rẻ nhất thỏa mãn ràng buộc giá, hãng, số điểm dừng và giờ khởi hành', 'Giữ chỗ cho hành khách Nguyen Van A', 'Thanh to`
- Yêu cầu gọi `search_flights(dest=HAN, date=2026-10-15, origin=SGN)`
- 784 token, 1.1s

**Bước 3 (+2.1s): Harness → tool**
- `search_flights(dest=HAN, date=2026-10-15, origin=SGN)`
- Kiểm quyền: ALLOW. Kết quả: **ERROR**: TimeoutError: search service timeout

**Bước 4 (+2.1s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[HumanMessage] Yêu cầu gốc: Hãy đặt cho Nguyen Van A một vé bay SGN -> HAN ngày 2026-10-15, chọn chuyến rẻ nhất thỏa các ràng buộc. Giữ chỗ rồi thanh toán. Kế hoạch: ['Tìm chuyến bay từ SGN đi HAN ngày 2026-10-15', 'Chọn chuyến bay rẻ nhất thỏa mãn ràng buộc giá, hãng, số điểm dừng và giờ khởi hành', 'Giữ chỗ cho hành khách Nguyen Van A', 'Thanh to`
- Yêu cầu gọi `search_flights(date=2026-10-15, dest=HAN, origin=SGN)`
- 819 token, 1.1s

**Bước 5 (+3.2s): Harness → tool**
- `search_flights(date=2026-10-15, dest=HAN, origin=SGN)`
- Kiểm quyền: ALLOW. Kết quả: 5 chuyến: VN101 Vietnam Airlines 06:30 2.400.000đ 0 dừng; VJ202 Vietjet 05:10 1.300.000đ 0 dừng; QH303 Bamboo 09:00 1.900.000đ 0 dừng; VN404 Vietnam Airlines 18:00 6.200.000đ 0 dừng; XX707 Vietjet 10:00 1.000.000đ 2 dừng

**Bước 6 (+3.2s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[HumanMessage] Yêu cầu gốc: Hãy đặt cho Nguyen Van A một vé bay SGN -> HAN ngày 2026-10-15, chọn chuyến rẻ nhất thỏa các ràng buộc. Giữ chỗ rồi thanh toán. Kế hoạch: ['Tìm chuyến bay từ SGN đi HAN ngày 2026-10-15', 'Chọn chuyến bay rẻ nhất thỏa mãn ràng buộc giá, hãng, số điểm dừng và giờ khởi hành', 'Giữ chỗ cho hành khách Nguyen Van A', 'Thanh to`
- Yêu cầu gọi `hold_seat(passenger=Nguyen Van A, flight_id=QH303)`
- 1203 token, 0.9s

**Bước 7 (+4.1s): Harness → tool**
- `hold_seat(passenger=Nguyen Van A, flight_id=QH303)`
- Kiểm quyền: ALLOW. Kết quả: booking BK001 [HELD, chưa thanh toán]: chuyến QH303 (Bamboo), 09:00, 1.900.000đ

**Bước 8 (+4.1s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[HumanMessage] Yêu cầu gốc: Hãy đặt cho Nguyen Van A một vé bay SGN -> HAN ngày 2026-10-15, chọn chuyến rẻ nhất thỏa các ràng buộc. Giữ chỗ rồi thanh toán. Kế hoạch: ['Tìm chuyến bay từ SGN đi HAN ngày 2026-10-15', 'Chọn chuyến bay rẻ nhất thỏa mãn ràng buộc giá, hãng, số điểm dừng và giờ khởi hành', 'Giữ chỗ cho hành khách Nguyen Van A', 'Thanh to`
- Yêu cầu gọi `pay(booking_id=BK001)`
- 1322 token, 1.2s

**Bước 9 (+5.3s): Harness → tool**
- `pay(booking_id=BK001)`
- Kiểm quyền: ALLOW. Kết quả: booking BK001 [PAID, đã thanh toán]: chuyến QH303 (Bamboo), 09:00, 1.900.000đ

**Bước 10 (+5.3s): Harness (check_done)**
- Kiểm tra tiêu chí hoàn thành bằng code
- ✅ đạt
