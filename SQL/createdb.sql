CREATE DATABASE IF NOT EXISTS `dental_clinic_db`;
USE `dental_clinic_db`;

-- thông tin nhân viên

CREATE TABLE `employee_info` (
  `employee_pin` varchar(12) NOT NULL,
  `employee_type` enum('r','d','h','a') NOT NULL, -- r: receptionist, d: dentist, h: hygienist, a: admin
  `name` varchar(255) NOT NULL,
  `gender` enum('M','F') NOT NULL,
  `phone` varchar(20) NOT NULL,
  `email` varchar(255) NOT NULL,
  `address` varchar(255) NOT NULL,
  `salary` decimal(10,2) NOT NULL,
  PRIMARY KEY (`employee_pin`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `employee` (
  `employee_id` int NOT NULL AUTO_INCREMENT,
  `employee_pin` varchar(12) NOT NULL,
  PRIMARY KEY (`employee_id`),
  KEY `FK_employee_pin` (`employee_pin`),
  CONSTRAINT `FK_employee_pin` FOREIGN KEY (`employee_pin`) REFERENCES `employee_info` (`employee_pin`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--  thông tin khách hàng

CREATE TABLE `patient_info` (
  `patient_pin` varchar(12) NOT NULL,
  `address` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `gender` enum('M','F') NOT NULL,
  `email` varchar(255) NOT NULL,
  `phone` varchar(20) NOT NULL,
  `date_of_birth` date NOT NULL,
  PRIMARY KEY (`patient_pin`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `patient` (
  `patient_id` int NOT NULL AUTO_INCREMENT,
  `patient_pin` varchar(12) NOT NULL,
  PRIMARY KEY (`patient_id`),
  KEY `FK_patient_pin` (`patient_pin`),
  CONSTRAINT `FK_patient_pin` FOREIGN KEY (`patient_pin`) REFERENCES `patient_info` (`patient_pin`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- user account

CREATE TABLE `user_account` (
  `username` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `type_id` enum('0','1') NOT NULL,
  `patient_id` int DEFAULT NULL,
  `employee_id` int DEFAULT NULL,
  PRIMARY KEY (`username`),
  KEY `FK_user_patient_id` (`patient_id`),
  KEY `FK_user_employee_id` (`employee_id`),
  CONSTRAINT `FK_user_employee_id` FOREIGN KEY (`employee_id`) REFERENCES `employee` (`employee_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `FK_user_patient_id` FOREIGN KEY (`patient_id`) REFERENCES `patient` (`patient_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `user_account_chk_1` CHECK (`type_id` BETWEEN 0 AND 2)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- danh sách dịch vụ

CREATE TABLE `procedure` (
  `procedure_code` int NOT NULL,
  `procedure_name` varchar(255) NOT NULL,
  `procedure_fee` decimal(10,2) NOT NULL,
  PRIMARY KEY (`procedure_code`),
  CONSTRAINT `procedure_code_check` CHECK (`procedure_code` >= 1 AND `procedure_code` <= 10)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- lịch hẹn

CREATE TABLE `appointment` (
  `appointment_id` int NOT NULL AUTO_INCREMENT,
  `patient_id` int NOT NULL,
  `dentist_id` int NOT NULL,
  `date_of_appointment` date NOT NULL,
  `start_time` time NOT NULL,
  `end_time` time NOT NULL,
  `appointment_type` varchar(255) NOT NULL,
  `appointment_status` enum('Vắng mặt','Đã huỷ','Đã khám','Đã đặt lịch') NOT NULL,
  `room` int NOT NULL,
  PRIMARY KEY (`appointment_id`),
  KEY `FK_appt_patient_id` (`patient_id`),
  KEY `FK_appt_dentist_id` (`dentist_id`),
  CONSTRAINT `FK_appt_dentist_id` FOREIGN KEY (`dentist_id`) REFERENCES `employee` (`employee_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `FK_appt_patient_id` FOREIGN KEY (`patient_id`) REFERENCES `patient` (`patient_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- hoá đơn và thanh toán

CREATE TABLE `invoice` (
  `invoice_id` int NOT NULL AUTO_INCREMENT,
  `patient_id` int NOT NULL,
  `date_of_issue` date NOT NULL,
  `patient_charge` decimal(10,2) NOT NULL,
  PRIMARY KEY (`invoice_id`),
  KEY `FK_invoice_patient` (`patient_id`),
  CONSTRAINT `FK_invoice_patient` FOREIGN KEY (`patient_id`) REFERENCES `patient` (`patient_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `patient_billing` (
  `billing_id` int NOT NULL AUTO_INCREMENT,
  `patient_id` int NOT NULL,
  `billing_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `payment_type` varchar(50) NOT NULL,
  `total_amount` decimal(10,2) NOT NULL,
  PRIMARY KEY (`billing_id`),
  KEY `FK_billing_patient` (`patient_id`),
  CONSTRAINT `FK_billing_patient` FOREIGN KEY (`patient_id`) REFERENCES `patient` (`patient_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- chi tiết quá trình điều trị

CREATE TABLE `appointment_procedure` (
  `procedure_id` int NOT NULL AUTO_INCREMENT,
  `appointment_id` int NOT NULL,
  `patient_id` int NOT NULL,
  `date_of_procedure` date NOT NULL,
  `procedure_code` int NOT NULL,
  `appointment_description` varchar(255) NOT NULL,
  `tooth` varchar(255) NOT NULL,
  `amount_of_procedure` int NOT NULL DEFAULT '1',
  `patient_charge` decimal(10,2) DEFAULT NULL,
  `total_charge` decimal(10,2) NOT NULL,
  `invoice_id` int DEFAULT NULL,
  PRIMARY KEY (`procedure_id`),
  KEY `FK_proc_appointment_id` (`appointment_id`),
  KEY `FK_proc_patient_id` (`patient_id`),
  KEY `FK_proc_procedure_code` (`procedure_code`),
  KEY `FK_proc_invoice` (`invoice_id`),
  CONSTRAINT `FK_proc_appointment_id` FOREIGN KEY (`appointment_id`) REFERENCES `appointment` (`appointment_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `FK_proc_invoice` FOREIGN KEY (`invoice_id`) REFERENCES `invoice` (`invoice_id`) ON DELETE SET NULL,
  CONSTRAINT `FK_proc_patient_id` FOREIGN KEY (`patient_id`) REFERENCES `patient` (`patient_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `FK_proc_procedure_code` FOREIGN KEY (`procedure_code`) REFERENCES `procedure` (`procedure_code`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `appointment_treatment` (
  `treatment_id` int NOT NULL AUTO_INCREMENT,
  `treatment_type` varchar(255) NOT NULL,
  `medication` varchar(255) NOT NULL,
  `symptoms` varchar(255) NOT NULL,
  `tooth` varchar(255) NOT NULL,
  `comments` varchar(255) DEFAULT NULL,
  `patient_id` int NOT NULL,
  `appointment_id` int NOT NULL,
  PRIMARY KEY (`treatment_id`),
  KEY `FK_treatment_patient_id` (`patient_id`),
  KEY `FK_treatment_appointment_id` (`appointment_id`),
  CONSTRAINT `FK_treatment_appointment_id` FOREIGN KEY (`appointment_id`) REFERENCES `appointment` (`appointment_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `FK_treatment_patient_id` FOREIGN KEY (`patient_id`) REFERENCES `patient` (`patient_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
