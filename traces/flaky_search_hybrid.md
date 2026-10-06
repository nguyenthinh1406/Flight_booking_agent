# Kịch bản `flaky_search` · Pattern `hybrid`

**Mô tả kịch bản:** Lần search đầu tiên bị timeout (lỗi tạm thời). Kỳ vọng: agent thử lại, bộ phát hiện lặp không báo nhầm.

**Yêu cầu gửi cho agent:** Hãy đặt cho Nguyen Van A một vé bay SGN -> HAN ngày 2026-10-15, chọn chuyến rẻ nhất thỏa các ràng buộc. Giữ chỗ rồi thanh toán.

**Ràng buộc (dữ liệu):** `{"max_price": 5000000, "allowed_airlines": ["Vietnam Airlines", "Vietjet", "Bamboo"], "max_stops": 1, "must_depart_after": "06:00", "require_confirm_above": 3000000, "max_tool_calls": 15, "max_llm_calls": 12, "max_bad_streak": 3, "loop_k": 3}`  
**Các lớp harness bật:** authz, constraints, done, grounding, handoff, loop, validate

## Kết quả tổng quát

- Kết cục: **done**, ✅ ĐẠT kỳ vọng (kỳ vọng: done)
- Số tool call: 4 · Số lần gọi LLM: 11 · Token: 13009 · Thời gian: 15.9s
- Booking đang hiệu lực trong hệ thống: BK001 (chuyến QH303, 1.900.000đ, ĐÃ THANH TOÁN)

## Diễn biến từng bước

| # | Thời điểm | Thành phần | Hành động | Kết quả |
|---|---|---|---|---|
| 1 | +0.0s | LLM (lập kế hoạch) | Đề xuất kế hoạch: ```json [   "Tìm chuyến bay từ SGN đến HAN ngày 2026-10-15",   "Chọn chuyến bay rẻ nhất thỏa mãn ràng buộc",   "Giữ chỗ chuyến bay",   "Thanh toán vé" ] ``` | 409 token, 1.7s |
| 2 | +1.7s | LLM (chọn tool) | Yêu cầu gọi `search_flights(origin=SGN, dest=HAN, date=2026-10-15)` | 769 token, 0.9s |
| 3 | +2.6s | Harness → tool | `search_flights(origin=SGN, dest=HAN, date=2026-10-15)` | Kiểm quyền: ALLOW. Kết quả: **ERROR**: TimeoutError: search service timeout |
| 4 | +2.6s | LLM (chọn tool) | Yêu cầu gọi `search_flights(dest=HAN, date=2026-10-15, origin=SGN)` | 828 token, 0.9s |
| 5 | +3.4s | Harness → tool | `search_flights(dest=HAN, date=2026-10-15, origin=SGN)` | Kiểm quyền: ALLOW. Kết quả: 5 chuyến: VN101 Vietnam Airlines 06:30 2.400.000đ 0 dừng; VJ202 Vietjet 05:10 1.300.000đ 0 dừng; QH303 Bamboo 09:00 1.900.000đ 0 dừng; VN404 Vietnam Airlines 18:00 6.200.000đ 0 dừng; XX707 Vietjet 10:00 1.000.000đ 2 dừng |
| 6 | +3.4s | LLM (chọn tool) | Trả lời: Đã tìm kiếm chuyến bay từ SGN đến HAN ngày 2026-10-15 thành công. Các chuyến bay khả dụng: 1. VN101 (Vietnam Airlines): 06:30, 0 điểm dừng, 2,400,000 VND 2. VJ202 (Vietjet): 05:10, 0 điểm dừng, 1,300,000 VND (Khởi hành trước 06:00, vi phạm ràng buộc `must_depart_after: 06:00`) 3. QH303 (Bamboo): 09: | 1524 token, 2.1s |
| 7 | +5.5s | LLM (lập kế hoạch) | Đề xuất kế hoạch: [   "Lọc các chuyến bay thỏa mãn ràng buộc về hãng, giá, số điểm dừng và giờ khởi hành",   "Chọn chuyến bay rẻ nhất từ danh sách đã lọc",   "Giữ chỗ cho chuyến bay đã chọn",   "Thanh toán vé" ] | 880 token, 1.3s |
| 8 | +6.8s | LLM (chọn tool) | Trả lời: Dựa trên các ràng buộc: - **`max_price`**: 5.000.000 VND - **`allowed_airlines`**: ["Vietnam Airlines", "Vietjet", "Bamboo"] (Tất cả hãng trong danh sách đều hợp lệ) - **`max_stops`**: 1 (Số điểm dừng tối đa là 1) - **`must_depart_after`**: "06:00" (Giờ khởi hành phải sau 06:00)  Xét các chuyến bay  | 1732 token, 2.4s |
| 9 | +9.2s | LLM (chọn tool) | Trả lời: Dựa trên danh sách các chuyến bay từ SGN đi HAN ngày 2026-10-15 và các ràng buộc (giá tối đa 5.000.000 VND, hãng thuộc Vietnam Airlines/Vietjet/Bamboo, tối đa 1 điểm dừng, giờ khởi hành từ 06:00):  - **VN101** (Vietnam Airlines): 06:30, 2.400.000 VND, 0 điểm dừng -> Thỏa mãn mọi ràng buộc. - **VJ202 | 1498 token, 2.2s |
| 10 | +11.4s | LLM (chọn tool) | Yêu cầu gọi `hold_seat(passenger=Nguyen Van A, flight_id=QH303)` | 1192 token, 1.0s |
| 11 | +12.3s | Harness → tool | `hold_seat(passenger=Nguyen Van A, flight_id=QH303)` | Kiểm quyền: ALLOW. Kết quả: booking BK001 [HELD, chưa thanh toán]: chuyến QH303 (Bamboo), 09:00, 1.900.000đ |
| 12 | +12.3s | LLM (chọn tool) | Trả lời: Đã thực hiện giữ chỗ thành công cho hành khách Nguyen Van A trên chuyến bay QH303 (Bamboo, SGN -> HAN, ngày 2026-10-15, giờ khởi hành 09:00, giá 1.900.000 VNĐ) với mã đặt chỗ `BK001`. | 1379 token, 1.4s |
| 13 | +13.8s | LLM (chọn tool) | Yêu cầu gọi `pay(booking_id=BK001)` | 1312 token, 0.9s |
| 14 | +14.6s | Harness → tool | `pay(booking_id=BK001)` | Kiểm quyền: ALLOW. Kết quả: booking BK001 [PAID, đã thanh toán]: chuyến QH303 (Bamboo), 09:00, 1.900.000đ |
| 15 | +14.6s | LLM (chọn tool) | Trả lời: Đã thanh toán thành công vé chuyến bay QH303 của hãng Bamboo (SGN -> HAN, ngày 2026-10-15) cho hành khách Nguyen Van A với giá 1.900.000 VNĐ. Mã đặt chỗ: BK001. | 1486 token, 1.2s |
| 16 | +15.9s | Harness (check_done) | Kiểm tra tiêu chí hoàn thành bằng code | ✅ đạt |

## Chi tiết

**Bước 1 (+0.0s): LLM (lập kế hoạch)**
- Agent nhìn thấy (tin nhắn cuối): `[HumanMessage] Hãy đặt cho Nguyen Van A một vé bay SGN -> HAN ngày 2026-10-15, chọn chuyến rẻ nhất thỏa các ràng buộc. Giữ chỗ rồi thanh toán.`
- Đề xuất kế hoạch: ```json [   "Tìm chuyến bay từ SGN đến HAN ngày 2026-10-15",   "Chọn chuyến bay rẻ nhất thỏa mãn ràng buộc",   "Giữ chỗ chuyến bay",   "Thanh toán vé" ] ```
- 409 token, 1.7s

**Bước 2 (+1.7s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[HumanMessage] Yêu cầu gốc: Hãy đặt cho Nguyen Van A một vé bay SGN -> HAN ngày 2026-10-15, chọn chuyến rẻ nhất thỏa các ràng buộc. Giữ chỗ rồi thanh toán. Kế hoạch: ['Tìm chuyến bay từ SGN đến HAN ngày 2026-10-15', 'Chọn chuyến bay rẻ nhất thỏa mãn ràng buộc', 'Giữ chỗ chuyến bay', 'Thanh toán vé'] Đã làm: (chưa làm gì)  Bây giờ CHỈ thực hiện bước`
- Yêu cầu gọi `search_flights(origin=SGN, dest=HAN, date=2026-10-15)`
- 769 token, 0.9s

**Bước 3 (+2.6s): Harness → tool**
- `search_flights(origin=SGN, dest=HAN, date=2026-10-15)`
- Kiểm quyền: ALLOW. Kết quả: **ERROR**: TimeoutError: search service timeout

**Bước 4 (+2.6s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[ToolMessage] ERROR: TimeoutError: search service timeout`
- Yêu cầu gọi `search_flights(dest=HAN, date=2026-10-15, origin=SGN)`
- 828 token, 0.9s

**Bước 5 (+3.4s): Harness → tool**
- `search_flights(dest=HAN, date=2026-10-15, origin=SGN)`
- Kiểm quyền: ALLOW. Kết quả: 5 chuyến: VN101 Vietnam Airlines 06:30 2.400.000đ 0 dừng; VJ202 Vietjet 05:10 1.300.000đ 0 dừng; QH303 Bamboo 09:00 1.900.000đ 0 dừng; VN404 Vietnam Airlines 18:00 6.200.000đ 0 dừng; XX707 Vietjet 10:00 1.000.000đ 2 dừng

**Bước 6 (+3.4s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[ToolMessage] {"status": "ok", "flights": [{"id": "VN101", "airline": "Vietnam Airlines", "origin": "SGN", "dest": "HAN", "date": "2026-10-15", "depart": "06:30", "price": 2400000, "stops": 0}, {"id": "VJ202", "airline": "Vietjet", "origin": "SGN", "dest": "HAN", "date": "2026-10-15", "depart": "05:10", "price": 1300000, "stops": 0}, {"id": "QH303"`
- Trả lời: Đã tìm kiếm chuyến bay từ SGN đến HAN ngày 2026-10-15 thành công. Các chuyến bay khả dụng: 1. VN101 (Vietnam Airlines): 06:30, 0 điểm dừng, 2,400,000 VND 2. VJ202 (Vietjet): 05:10, 0 điểm dừng, 1,300,000 VND (Khởi hành trước 06:00, vi phạm ràng buộc `must_depart_after: 06:00`) 3. QH303 (Bamboo): 09:
- 1524 token, 2.1s

**Bước 7 (+5.5s): LLM (lập kế hoạch)**
- Agent nhìn thấy (tin nhắn cuối): `[HumanMessage] Hãy đặt cho Nguyen Van A một vé bay SGN -> HAN ngày 2026-10-15, chọn chuyến rẻ nhất thỏa các ràng buộc. Giữ chỗ rồi thanh toán.  Kế hoạch trước chưa thành công. Đã thực hiện: - search_flights({"origin": "SGN", "dest": "HAN", "date": "2026-10-15"}) -> ERROR: TimeoutError: search service timeout - search_flights({"dest": "HAN", "date":`
- Đề xuất kế hoạch: [   "Lọc các chuyến bay thỏa mãn ràng buộc về hãng, giá, số điểm dừng và giờ khởi hành",   "Chọn chuyến bay rẻ nhất từ danh sách đã lọc",   "Giữ chỗ cho chuyến bay đã chọn",   "Thanh toán vé" ]
- 880 token, 1.3s

**Bước 8 (+6.8s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[HumanMessage] Yêu cầu gốc: Hãy đặt cho Nguyen Van A một vé bay SGN -> HAN ngày 2026-10-15, chọn chuyến rẻ nhất thỏa các ràng buộc. Giữ chỗ rồi thanh toán. Kế hoạch: ['Lọc các chuyến bay thỏa mãn ràng buộc về hãng, giá, số điểm dừng và giờ khởi hành', 'Chọn chuyến bay rẻ nhất từ danh sách đã lọc', 'Giữ chỗ cho chuyến bay đã chọn', 'Thanh toán vé'] `
- Trả lời: Dựa trên các ràng buộc: - **`max_price`**: 5.000.000 VND - **`allowed_airlines`**: ["Vietnam Airlines", "Vietjet", "Bamboo"] (Tất cả hãng trong danh sách đều hợp lệ) - **`max_stops`**: 1 (Số điểm dừng tối đa là 1) - **`must_depart_after`**: "06:00" (Giờ khởi hành phải sau 06:00)  Xét các chuyến bay 
- 1732 token, 2.4s

**Bước 9 (+9.2s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[HumanMessage] Yêu cầu gốc: Hãy đặt cho Nguyen Van A một vé bay SGN -> HAN ngày 2026-10-15, chọn chuyến rẻ nhất thỏa các ràng buộc. Giữ chỗ rồi thanh toán. Kế hoạch: ['Lọc các chuyến bay thỏa mãn ràng buộc về hãng, giá, số điểm dừng và giờ khởi hành', 'Chọn chuyến bay rẻ nhất từ danh sách đã lọc', 'Giữ chỗ cho chuyến bay đã chọn', 'Thanh toán vé'] `
- Trả lời: Dựa trên danh sách các chuyến bay từ SGN đi HAN ngày 2026-10-15 và các ràng buộc (giá tối đa 5.000.000 VND, hãng thuộc Vietnam Airlines/Vietjet/Bamboo, tối đa 1 điểm dừng, giờ khởi hành từ 06:00):  - **VN101** (Vietnam Airlines): 06:30, 2.400.000 VND, 0 điểm dừng -> Thỏa mãn mọi ràng buộc. - **VJ202
- 1498 token, 2.2s

**Bước 10 (+11.4s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[HumanMessage] Yêu cầu gốc: Hãy đặt cho Nguyen Van A một vé bay SGN -> HAN ngày 2026-10-15, chọn chuyến rẻ nhất thỏa các ràng buộc. Giữ chỗ rồi thanh toán. Kế hoạch: ['Lọc các chuyến bay thỏa mãn ràng buộc về hãng, giá, số điểm dừng và giờ khởi hành', 'Chọn chuyến bay rẻ nhất từ danh sách đã lọc', 'Giữ chỗ cho chuyến bay đã chọn', 'Thanh toán vé'] `
- Yêu cầu gọi `hold_seat(passenger=Nguyen Van A, flight_id=QH303)`
- 1192 token, 1.0s

**Bước 11 (+12.3s): Harness → tool**
- `hold_seat(passenger=Nguyen Van A, flight_id=QH303)`
- Kiểm quyền: ALLOW. Kết quả: booking BK001 [HELD, chưa thanh toán]: chuyến QH303 (Bamboo), 09:00, 1.900.000đ

**Bước 12 (+12.3s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[ToolMessage] {"status": "ok", "booking_id": "BK001", "passenger": "Nguyen Van A", "state": "HELD", "paid": false, "id": "QH303", "airline": "Bamboo", "origin": "SGN", "dest": "HAN", "date": "2026-10-15", "depart": "09:00", "price": 1900000, "stops": 0}`
- Trả lời: Đã thực hiện giữ chỗ thành công cho hành khách Nguyen Van A trên chuyến bay QH303 (Bamboo, SGN -> HAN, ngày 2026-10-15, giờ khởi hành 09:00, giá 1.900.000 VNĐ) với mã đặt chỗ `BK001`.
- 1379 token, 1.4s

**Bước 13 (+13.8s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[HumanMessage] Yêu cầu gốc: Hãy đặt cho Nguyen Van A một vé bay SGN -> HAN ngày 2026-10-15, chọn chuyến rẻ nhất thỏa các ràng buộc. Giữ chỗ rồi thanh toán. Kế hoạch: ['Lọc các chuyến bay thỏa mãn ràng buộc về hãng, giá, số điểm dừng và giờ khởi hành', 'Chọn chuyến bay rẻ nhất từ danh sách đã lọc', 'Giữ chỗ cho chuyến bay đã chọn', 'Thanh toán vé'] `
- Yêu cầu gọi `pay(booking_id=BK001)`
- 1312 token, 0.9s

**Bước 14 (+14.6s): Harness → tool**
- `pay(booking_id=BK001)`
- Kiểm quyền: ALLOW. Kết quả: booking BK001 [PAID, đã thanh toán]: chuyến QH303 (Bamboo), 09:00, 1.900.000đ

**Bước 15 (+14.6s): LLM (chọn tool)**
- Agent nhìn thấy (tin nhắn cuối): `[ToolMessage] {"status": "ok", "booking_id": "BK001", "passenger": "Nguyen Van A", "state": "PAID", "paid": true, "id": "QH303", "airline": "Bamboo", "origin": "SGN", "dest": "HAN", "date": "2026-10-15", "depart": "09:00", "price": 1900000, "stops": 0}`
- Trả lời: Đã thanh toán thành công vé chuyến bay QH303 của hãng Bamboo (SGN -> HAN, ngày 2026-10-15) cho hành khách Nguyen Van A với giá 1.900.000 VNĐ. Mã đặt chỗ: BK001.
- 1486 token, 1.2s

**Bước 16 (+15.9s): Harness (check_done)**
- Kiểm tra tiêu chí hoàn thành bằng code
- ✅ đạt
