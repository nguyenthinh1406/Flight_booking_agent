# Kịch bản `easy` · Pattern `plan_execute`

**Mô tả kịch bản:** Có chuyến hợp lệ. Kỳ vọng: giữ chỗ và thanh toán chuyến rẻ nhất thỏa ràng buộc (QH303).

**Yêu cầu gửi cho agent:** Hãy đặt cho Nguyen Van A một vé bay SGN -> HAN ngày 2026-10-15, chọn chuyến rẻ nhất thỏa các ràng buộc. Giữ chỗ rồi thanh toán.

**Ràng buộc (dữ liệu):** `{"max_price": 5000000, "allowed_airlines": ["Vietnam Airlines", "Vietjet", "Bamboo"], "max_stops": 1, "must_depart_after": "06:00", "require_confirm_above": 3000000, "max_tool_calls": 15, "max_llm_calls": 12, "max_bad_streak": 3, "loop_k": 3}`  
**Các lớp harness bật:** authz, constraints, done, grounding, handoff, loop, validate

## Kết quả tổng quát

- Kết cục: **done**, ✅ ĐẠT kỳ vọng (kỳ vọng: done)
- Số tool call: 3 · Số lần gọi LLM: 5 · Token: 5236 · Thời gian: 7.5s
- Booking đang hiệu lực trong hệ thống: BK001 (chuyến QH303, 1.900.000đ, ĐÃ THANH TOÁN)

## Diễn biến từng bước

| # | Thời điểm | Thành phần | Hành động | Kết quả |
|---|---|---|---|---|
| 1 | +0.0s | LLM (lập kế hoạch) | Đề xuất kế hoạch: ```json [   "Tìm kiếm chuyến bay từ SGN đi HAN ngày 2026-10-15",   "Chọn chuyến bay rẻ nhất thỏa mãn ràng buộc",   "Tiến hành giữ chỗ chuyến bay",   "Thanh toán vé đã giữ chỗ" ] ``` | 415 token, 1.5s |
| 2 | +1.5s | LLM (chọn tool) | Yêu cầu gọi `search_flights(dest=HAN, date=2026-10-15, origin=SGN)` | 776 token, 1.2s |
| 3 | +2.7s | Harness → tool | `search_flights(dest=HAN, date=2026-10-15, origin=SGN)` | Kiểm quyền: ALLOW. Kết quả: 5 chuyến: VN101 Vietnam Airlines 06:30 2.400.000đ 0 dừng; VJ202 Vietjet 05:10 1.300.000đ 0 dừng; QH303 Bamboo 09:00 1.900.000đ 0 dừng; VN404 Vietnam Airlines 18:00 6.200.000đ 0 dừng; XX707 Vietjet 10:00 1.000.000đ 2 dừng |
| 4 | +2.7s | LLM (chọn tool) | Trả lời: Dựa trên kết quả tìm kiếm chuyến bay từ SGN đi HAN ngày 2026-10-15 và các ràng buộc: - **`max_price`**: 5.000.000 VND - **`allowed_airlines`**: ["Vietnam Airlines", "Vietjet", "Bamboo"] - **`max_stops`**: 1 (tối đa 1 điểm dừng) - **`must_depart_after`**: "06:00" (khởi hành sau 06:00)  Lọc các chuyến | 1622 token, 2.9s |
| 5 | +5.6s | LLM (chọn tool) | Yêu cầu gọi `hold_seat(passenger=Nguyen Van A, flight_id=QH303)` | 1149 token, 0.8s |
| 6 | +6.4s | Harness → tool | `hold_seat(passenger=Nguyen Van A, flight_id=QH303)` | Kiểm quyền: ALLOW. Kết quả: booking BK001 [HELD, chưa thanh toán]: chuyến QH303 (Bamboo), 09:00, 1.900.000đ |
| 7 | +6.4s | LLM (chọn tool) | Yêu cầu gọi `pay(booking_id=BK001)` | 1274 token, 1.1s |
| 8 | +7.5s | Harness → tool | `pay(booking_id=BK001)` | Kiểm quyền: ALLOW. Kết quả: booking BK001 [PAID, đã thanh toán]: chuyến QH303 (Bamboo), 09:00, 1.900.000đ |
| 9 | +7.5s | Harness (check_done) | Kiểm tra tiêu chí hoàn thành bằng code | ✅ đạt |

## Chi tiết

**Bước 1 (+0.0s): LLM (lập kế hoạch)**
- Agent nhìn thấy (tin nhắn cuối): `[HumanMessage] Hãy đặt cho Nguyen Van A một vé bay SGN -> HAN ngày 2026-10-15, chọn chuyến rẻ nhất thỏa các ràng buộc. Giữ chỗ rồi thanh toán.`
- Đề xuất kế hoạch: ```json [   "Tìm kiếm chuyến bay từ SGN đi HAN ngày 2026-10-15",   "Chọn chuyến bay rẻ nhất thỏa mãn ràng buộc",   "Tiến hành giữ chỗ chuyến bay",   "Thanh toán vé đã giữ chỗ" ] ```
- 415 token, 1.5s

**Bước 2 (+1.5s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[HumanMessage] Yêu cầu gốc: Hãy đặt cho Nguyen Van A một vé bay SGN -> HAN ngày 2026-10-15, chọn chuyến rẻ nhất thỏa các ràng buộc. Giữ chỗ rồi thanh toán. Kế hoạch: ['Tìm kiếm chuyến bay từ SGN đi HAN ngày 2026-10-15', 'Chọn chuyến bay rẻ nhất thỏa mãn ràng buộc', 'Tiến hành giữ chỗ chuyến bay', 'Thanh toán vé đã giữ chỗ'] Đã làm: (chưa làm gì)  B`
- Yêu cầu gọi `search_flights(dest=HAN, date=2026-10-15, origin=SGN)`
- 776 token, 1.2s

**Bước 3 (+2.7s): Harness → tool**
- `search_flights(dest=HAN, date=2026-10-15, origin=SGN)`
- Kiểm quyền: ALLOW. Kết quả: 5 chuyến: VN101 Vietnam Airlines 06:30 2.400.000đ 0 dừng; VJ202 Vietjet 05:10 1.300.000đ 0 dừng; QH303 Bamboo 09:00 1.900.000đ 0 dừng; VN404 Vietnam Airlines 18:00 6.200.000đ 0 dừng; XX707 Vietjet 10:00 1.000.000đ 2 dừng

**Bước 4 (+2.7s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[HumanMessage] Yêu cầu gốc: Hãy đặt cho Nguyen Van A một vé bay SGN -> HAN ngày 2026-10-15, chọn chuyến rẻ nhất thỏa các ràng buộc. Giữ chỗ rồi thanh toán. Kế hoạch: ['Tìm kiếm chuyến bay từ SGN đi HAN ngày 2026-10-15', 'Chọn chuyến bay rẻ nhất thỏa mãn ràng buộc', 'Tiến hành giữ chỗ chuyến bay', 'Thanh toán vé đã giữ chỗ'] Đã làm: - search_flights`
- Trả lời: Dựa trên kết quả tìm kiếm chuyến bay từ SGN đi HAN ngày 2026-10-15 và các ràng buộc: - **`max_price`**: 5.000.000 VND - **`allowed_airlines`**: ["Vietnam Airlines", "Vietjet", "Bamboo"] - **`max_stops`**: 1 (tối đa 1 điểm dừng) - **`must_depart_after`**: "06:00" (khởi hành sau 06:00)  Lọc các chuyến
- 1622 token, 2.9s

**Bước 5 (+5.6s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[HumanMessage] Yêu cầu gốc: Hãy đặt cho Nguyen Van A một vé bay SGN -> HAN ngày 2026-10-15, chọn chuyến rẻ nhất thỏa các ràng buộc. Giữ chỗ rồi thanh toán. Kế hoạch: ['Tìm kiếm chuyến bay từ SGN đi HAN ngày 2026-10-15', 'Chọn chuyến bay rẻ nhất thỏa mãn ràng buộc', 'Tiến hành giữ chỗ chuyến bay', 'Thanh toán vé đã giữ chỗ'] Đã làm: - search_flights`
- Yêu cầu gọi `hold_seat(passenger=Nguyen Van A, flight_id=QH303)`
- 1149 token, 0.8s

**Bước 6 (+6.4s): Harness → tool**
- `hold_seat(passenger=Nguyen Van A, flight_id=QH303)`
- Kiểm quyền: ALLOW. Kết quả: booking BK001 [HELD, chưa thanh toán]: chuyến QH303 (Bamboo), 09:00, 1.900.000đ

**Bước 7 (+6.4s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[HumanMessage] Yêu cầu gốc: Hãy đặt cho Nguyen Van A một vé bay SGN -> HAN ngày 2026-10-15, chọn chuyến rẻ nhất thỏa các ràng buộc. Giữ chỗ rồi thanh toán. Kế hoạch: ['Tìm kiếm chuyến bay từ SGN đi HAN ngày 2026-10-15', 'Chọn chuyến bay rẻ nhất thỏa mãn ràng buộc', 'Tiến hành giữ chỗ chuyến bay', 'Thanh toán vé đã giữ chỗ'] Đã làm: - search_flights`
- Yêu cầu gọi `pay(booking_id=BK001)`
- 1274 token, 1.1s

**Bước 8 (+7.5s): Harness → tool**
- `pay(booking_id=BK001)`
- Kiểm quyền: ALLOW. Kết quả: booking BK001 [PAID, đã thanh toán]: chuyến QH303 (Bamboo), 09:00, 1.900.000đ

**Bước 9 (+7.5s): Harness (check_done)**
- Kiểm tra tiêu chí hoàn thành bằng code
- ✅ đạt
