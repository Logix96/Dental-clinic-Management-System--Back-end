
-- employee
INSERT INTO `employee_info` (`employee_pin`, `employee_type`, `name`, `gender`, `phone`, `email`, `address`, `salary`) VALUES
('EMP000000001', 'a', 'Nguyễn Minh Quân', 'M', '0912345678', 'quan.admin@dentalclinic.com', 'Cầu Giấy, Hà Nội', 25000000.00),
('EMP000000002', 'd', 'Trần Phương Thảo', 'F', '0923456789', 'thao.dentist@dentalclinic.com', 'Đống Đa, Hà Nội', 45000000.00),
('EMP000000003', 'd', 'Lê Hoàng Long', 'M', '0934567890', 'long.dentist@dentalclinic.com', 'Hai Bà Trưng, Hà Nội', 42000000.00),
('EMP000000004', 'r', 'Phạm Quỳnh Anh', 'F', '0945678901', 'anh.reception1@dentalclinic.com', 'Thanh Xuân, Hà Nội', 12000000.00),
('EMP000000005', 'r', 'Bùi Thị Hà', 'F', '0956789012', 'ha.reception2@dentalclinic.com', 'Tây Hồ, Hà Nội', 11000000.00),
('EMP000000006', 'h', 'Đinh Văn Cường', 'M', '0967890123', 'cuong.hygienist1@dentalclinic.com', 'Hoàng Mai, Hà Nội', 18000000.00),
('EMP000000007', 'h', 'Vũ Thu Trà', 'F', '0978901234', 'tra.hygienist2@dentalclinic.com', 'Ba Đình, Hà Nội', 17500000.00);

-- employee
INSERT INTO `employee` (`employee_id`, `employee_pin`) VALUES
(101, 'EMP000000001'), -- Quản trị viên
(102, 'EMP000000002'), -- Nha sĩ 1
(103, 'EMP000000003'), -- Nha sĩ 2
(104, 'EMP000000004'), -- Lễ tân 1
(105, 'EMP000000005'), -- Lễ tân 2
(106, 'EMP000000006'), -- Hygienist 1
(107, 'EMP000000007'); -- Hygienist 2

-- patient info
INSERT INTO `patient_info` (`patient_pin`, `address`, `name`, `gender`, `email`, `phone`, `date_of_birth`) VALUES
('PAT000000001', 'Hoàng Mai, Hà Nội', 'Nguyễn Văn An', 'M', 'an.nguyen95@gmail.com', '0987654321', '1995-05-20'),
('PAT000000002', 'Ba Đình, Hà Nội', 'Lê Thị Bình', 'F', 'binhle.98@gmail.com', '0976543210', '1998-11-12'),
('PAT000000003', 'Cầu Giấy, Hà Nội', 'Trần Văn Cường', 'M', 'cuong.tran@gmail.com', '0911223344', '1990-02-15'),
('PAT000000004', 'Đống Đa, Hà Nội', 'Phạm Thị Dung', 'F', 'dung.pham@gmail.com', '0922334455', '2001-08-08'),
('PAT000000005', 'Thanh Xuân, Hà Nội', 'Hoàng Văn Em', 'M', 'em.hoang@gmail.com', '0933445566', '1985-12-30'),
('PAT000000006', 'Hai Bà Trưng, Hà Nội', 'Ngô Thị Phương', 'F', 'phuong.ngo@gmail.com', '0944556677', '1993-04-25'),
('PAT000000007', 'Tây Hồ, Hà Nội', 'Trịnh Quốc Hưng', 'M', 'hung.trinh@gmail.com', '0955667788', '1988-09-10'),
('PAT000000008', 'Long Biên, Hà Nội', 'Đào Thu Thủy', 'F', 'thuy.dao@gmail.com', '0966778899', '2005-01-05');

-- patient
INSERT INTO `patient` (`patient_id`, `patient_pin`) VALUES
(1, 'PAT000000001'), (2, 'PAT000000002'), (3, 'PAT000000003'), (4, 'PAT000000004'),
(5, 'PAT000000005'), (6, 'PAT000000006'), (7, 'PAT000000007'), (8, 'PAT000000008');

-- user account
INSERT INTO `user_account` (`username`, `password`, `type_id`, `patient_id`, `employee_id`) VALUES
('admin', 'password123', 0, NULL, 101),
('dentist1', 'password123', 1, NULL, 102),
('dentist2', 'password123', 1, NULL, 103),
('reception1', 'password123', 0, NULL, 104),
('reception2', 'password123', 0, NULL, 105),
('hygienist1', 'password123', 1, NULL, 106),
('hygienist2', 'password123', 1, NULL, 107),
('patient1', 'password123', 2, 1, NULL),
('patient2', 'password123', 2, 2, NULL),
('patient3', 'password123', 2, 3, NULL);

-- procedure
INSERT INTO `procedure` (`procedure_code`, `procedure_name`, `procedure_fee`) VALUES
(1, 'Cạo vôi răng & Đánh bóng', 300000.00),
(2, 'Tẩy trắng răng thẩm mỹ', 1500000.00),
(3, 'Nhổ răng / Tiểu phẫu', 1000000.00),
(4, 'Mặt dán sứ thẩm mỹ', 6000000.00),
(5, 'Trám răng thẩm mỹ Composite', 500000.00),
(6, 'Bọc răng sứ toàn sứ', 3500000.00),
(7, 'Điều trị tủy toàn diện', 2500000.00),
(8, 'Niềng răng chỉnh nha', 30000000.00),
(9, 'Đắp răng thẩm mỹ / Phục hình', 800000.00),
(10, 'Làm hàm giả tháo lắp', 5000000.00);

-- appointment
INSERT INTO `appointment` (`appointment_id`, `patient_id`, `dentist_id`, `date_of_appointment`, `start_time`, `end_time`, `appointment_type`, `appointment_status`, `room`) VALUES
(1, 1, 102, '2026-05-18', '09:00:00', '10:00:00', 'Khám định kỳ', 'Đã đặt lịch', 101),
(2, 2, 103, '2026-05-15', '14:00:00', '15:00:00', 'Điều trị bệnh lý', 'Đã khám', 102),
(3, 3, 102, '2026-05-10', '08:30:00', '09:30:00', 'Tiểu phẫu', 'Đã khám', 101),
(4, 4, 103, '2026-05-12', '10:00:00', '11:00:00', 'Khám tổng quát', 'Vắng mặt', 103),
(5, 5, 102, '2026-05-19', '15:30:00', '16:30:00', 'Tư vấn thẩm mỹ', 'Đã đặt lịch', 101),
(6, 6, 103, '2026-05-20', '09:00:00', '11:00:00', 'Thẩm mỹ', 'Đã đặt lịch', 102),
(7, 7, 102, '2026-05-05', '14:00:00', '15:00:00', 'Khám định kỳ', 'Đã huỷ', 101),
(8, 8, 103, '2026-05-08', '16:00:00', '17:30:00', 'Thẩm mỹ', 'Đã khám', 103),
(9, 1, 102, '2026-06-01', '08:00:00', '09:00:00', 'Tái khám', 'Đã đặt lịch', 101),
(10, 3, 103, '2026-05-25', '13:30:00', '14:30:00', 'Cắt chỉ', 'Đã đặt lịch', 102);

-- invoice
INSERT INTO `invoice` (`invoice_id`, `patient_id`, `date_of_issue`, `patient_charge`) VALUES
(1, 2, '2026-05-15', 300000.00),
(2, 3, '2026-05-10', 1000000.00),
(3, 8, '2026-05-08', 1500000.00);

-- patient billing
INSERT INTO `patient_billing` (`billing_id`, `patient_id`, `billing_date`, `payment_type`, `total_amount`) VALUES
(1, 2, '2026-05-15 15:05:00', 'Chuyển khoản', 300000.00),
(2, 3, '2026-05-10 09:40:00', 'Tiền mặt', 1000000.00),
(3, 8, '2026-05-08 17:45:00', 'Quẹt thẻ', 1500000.00);

-- appointment procedure
INSERT INTO `appointment_procedure` (`procedure_id`, `appointment_id`, `patient_id`, `date_of_procedure`, `procedure_code`, `appointment_description`, `tooth`, `amount_of_procedure`, `patient_charge`, `total_charge`, `invoice_id`) VALUES
(1, 2, 2, '2026-05-15', 1, 'Cạo vôi răng mảng bám cứng', 'Hàm dưới', 1, 300000.00, 300000.00, 1),
(2, 3, 3, '2026-05-10', 3, 'Nhổ răng khôn số 8 mọc lệch', 'Răng 48', 1, 1000000.00, 1000000.00, 2),
(3, 8, 8, '2026-05-08', 2, 'Tẩy trắng răng Laser', 'Toàn hàm', 1, 1500000.00, 1500000.00, 3);

-- appointment treatment
INSERT INTO `appointment_treatment` (`treatment_id`, `treatment_type`, `medication`, `symptoms`, `tooth`, `comments`, `patient_id`, `appointment_id`) VALUES
(1, 'Lấy cao răng siêu âm', 'Nước súc miệng diệt khuẩn', 'Ê buốt nhẹ khi ăn đồ lạnh', 'Toàn hàm', 'Tái khám định kỳ sau 6 tháng', 2, 2),
(2, 'Nhổ răng tiểu phẫu', 'Paracetamol, Kháng sinh', 'Đau nhức vùng góc hàm', 'Răng 48', 'Ăn đồ mềm, quay lại cắt chỉ sau 7 ngày', 3, 3),
(3, 'Tẩy trắng Laser Whitening', 'Gel giảm buốt', 'Răng ố vàng do cafe', 'Toàn hàm', 'Kiêng đồ ăn có màu sậm trong 48h', 8, 8);
