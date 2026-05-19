-- user account
CREATE TABLE `user_account` (
  `username` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `type_id` tinyint NOT NULL,
  `client_id` int DEFAULT NULL,
  `employee_id` int DEFAULT NULL,
  PRIMARY KEY (`username`),
  KEY `FK_user_client_id_idx` (`client_id`) /*!80000 INVISIBLE */,
  KEY `FK_user_employee_id_idx` (`employee_id`),
  CONSTRAINT `FK_user_client_id` FOREIGN KEY (`client_id`) REFERENCES `client_info` (`client_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `FK_user_employee_id` FOREIGN KEY (`employee_id`) REFERENCES `employee_info` (`employee_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `user_account_chk_1` CHECK ((`type_id` between 0 and 2))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- client info
CREATE TABLE `client_info` (
  `client_id` int NOT NULL AUTO_INCREMENT,
  `pin` varchar(12) DEFAULT NULL,
  `name` varchar(255) NOT NULL,
  `gender` enum('M','F') NOT NULL,
  `date_of_birth` date NOT NULL,
  `address` varchar(255) NOT NULL,
  `phone` varchar(20) NOT NULL,
  `email` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`client_id`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- employee info
CREATE TABLE `employee_info` (
  `employee_id` int NOT NULL AUTO_INCREMENT,
  `employee_pin` varchar(12) NOT NULL,
  `employee_type` enum('r','d','a') NOT NULL,
  `name` varchar(255) NOT NULL,
  `gender` enum('M','F') NOT NULL,
  `date_of_birth` date NOT NULL,
  `address` varchar(255) NOT NULL,
  `phone` varchar(20) NOT NULL,
  `email` varchar(255) NOT NULL,
  `salary` decimal(10,2) NOT NULL,
  PRIMARY KEY (`employee_id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- appointment
CREATE TABLE `appointment` (
  `appointment_id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `dentist_id` int NOT NULL,
  `date_of_appointment` date NOT NULL,
  `time` time NOT NULL,
  `reason` varchar(255) DEFAULT NULL,
  `appointment_status` enum('Vắng mặt','Đã huỷ','Đã khám','Đã đặt lịch') NOT NULL,
  PRIMARY KEY (`appointment_id`),
  KEY `FK_appt_client_id_idx` (`client_id`),
  KEY `FK_appt_dentist_id_idx` (`dentist_id`),
  CONSTRAINT `FK_appt_client_id` FOREIGN KEY (`client_id`) REFERENCES `client_info` (`client_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `FK_appt_dentist_id` FOREIGN KEY (`dentist_id`) REFERENCES `employee_info` (`employee_id`)
) ENGINE=InnoDB AUTO_INCREMENT=59 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- treatment history
CREATE TABLE `treatment_history` (
  `treatment_id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `description` text NOT NULL,
  `client_id` int NOT NULL,
  `appointment_id` int NOT NULL,
  PRIMARY KEY (`treatment_id`),
  KEY `FK_treatment_client_id_idx` (`client_id`),
  KEY `FK_treatment_appointment_id` (`appointment_id`),
  CONSTRAINT `FK_treatment_appointment_id` FOREIGN KEY (`appointment_id`) REFERENCES `appointment` (`appointment_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `FK_treatment_cleint_id` FOREIGN KEY (`client_id`) REFERENCES `client_info` (`client_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- procedure info
CREATE TABLE `procedure_info` (
  `procedure_id` int NOT NULL AUTO_INCREMENT,
  `procedure_name` varchar(255) NOT NULL,
  `procedure_price` decimal(10,2) NOT NULL,
  PRIMARY KEY (`procedure_id`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- procedure history
CREATE TABLE `procedure_history` (
  `history_id` int NOT NULL AUTO_INCREMENT,
  `treatment_id` int NOT NULL,
  `procedure_id` int NOT NULL,
  `procedure_date` date NOT NULL,
  `tooth` varchar(255) NOT NULL,
  `amount` int NOT NULL DEFAULT '1',
  `charge` decimal(10,2) NOT NULL,
  `comment` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`history_id`),
  KEY `fk_pro_his_treatment_id_idx` (`treatment_id`),
  KEY `fk_pro_his_procedure_id_idx` (`procedure_id`),
  CONSTRAINT `fk_pro_his_procedure_id` FOREIGN KEY (`procedure_id`) REFERENCES `procedure_info` (`procedure_id`),
  CONSTRAINT `fk_pro_his_treatment_id` FOREIGN KEY (`treatment_id`) REFERENCES `treatment_history` (`treatment_id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- invoice
CREATE TABLE `invoice` (
  `invoice_id` int NOT NULL AUTO_INCREMENT,
  `treatment_id` int NOT NULL,
  `total_charge` decimal(10,2) NOT NULL,
  `discount` decimal(10,2) NOT NULL DEFAULT '0.00',
  `final_charge` decimal(10,2) GENERATED ALWAYS AS ((`total_charge` - `discount`)) STORED,
  `payment_status` enum('Chưa thanh toán','Đã thanh toán') NOT NULL DEFAULT 'Chưa thanh toán',
  `invoice_date` date DEFAULT NULL,
  PRIMARY KEY (`invoice_id`),
  KEY `fk_invoice_treatment_id_idx` (`treatment_id`),
  CONSTRAINT `fk_invoice_treatment_id` FOREIGN KEY (`treatment_id`) REFERENCES `treatment_history` (`treatment_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
