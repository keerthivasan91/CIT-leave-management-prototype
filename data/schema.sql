DROP DATABASE IF EXISTS faculty_leave;
CREATE DATABASE faculty_leave;
USE faculty_leave;

-- Users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE,
    password VARCHAR(100),
    role ENUM('staff','faculty','hod','admin') DEFAULT 'faculty',
    name VARCHAR(100),
    department VARCHAR(100)
);

-- Leave requests with substitute workflow
CREATE TABLE leave_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50),
    department VARCHAR(100),
    leave_type VARCHAR(50),
    start_date DATE,
    start_session ENUM('Forenoon','Afternoon') DEFAULT 'Forenoon',
    end_date DATE,
    end_session ENUM('Forenoon','Afternoon') DEFAULT 'Afternoon',
    reason TEXT,
    days INT,
    substitute_user_id VARCHAR(50),
    substitute_status ENUM('Pending','Accepted','Rejected') DEFAULT 'Pending',
    hod_status ENUM('Pending','Approved','Rejected') DEFAULT 'Pending',
    principal_status ENUM('Pending','Approved','Rejected') DEFAULT 'Pending',
    final_status VARCHAR(20) DEFAULT 'Pending',
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    substitute_responded_at TIMESTAMP NULL,
    hod_responded_at TIMESTAMP NULL,
    principal_responded_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (substitute_user_id) REFERENCES users(user_id)
);

-- Substitute requests (when someone requests you as substitute)
CREATE TABLE substitute_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    leave_request_id INT,
    requested_user_id VARCHAR(50),
    status ENUM('Pending','Accepted','Rejected') DEFAULT 'Pending',
    responded_at TIMESTAMP NULL,
    FOREIGN KEY (leave_request_id) REFERENCES leave_requests(id),
    FOREIGN KEY (requested_user_id) REFERENCES users(user_id)
);

-- Holidays
CREATE TABLE holidays (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE,
    name VARCHAR(100)
);

-- Sample users
INSERT INTO users (user_id, password, role, name, department) VALUES
('STF001','1234','Staff','Sam','CSE'),
('FAC001','1234','faculty','BOB','CSE'),
('FAC002','abcd','faculty','Ravi Kumar','CSE'),
('FAC003','pass123','faculty','Dr. Alice Johnson','CSE'),
('FAC004','pass456','faculty','Prof. Bob Smith','CSE'),
('FAC005','pass789','faculty','Dr. Carol Davis','ECE'),
('FAC006','pass101','faculty','Prof. David Wilson','ECE'),
('FAC007','pass202','faculty','Dr. Emma Brown','ME'),
('FAC008','pass303','faculty','Prof. Frank Miller','ME'),
('HODCSE','hodpass','hod','Dr. Meena','CSE'),
('HODECE','hodpass2','hod','Dr. Rajesh','ECE'),
('HODME','hodpass3','hod','Dr. Priya','ME'),
('ADM001','admin','admin','Principal Raj','Admin'); 

-- Sample holidays
INSERT INTO holidays (date, name) VALUES
('2025-01-01', 'New Year''s Day'),
('2025-01-14', 'Makar Sankranti'),
('2025-01-15', 'Pongal'),
('2025-01-26', 'Republic Day'),
('2025-03-08', 'International Women''s Day'),
('2025-03-14', 'Maha Shivaratri'),
('2025-03-17', 'Holi'),
('2025-04-02', 'Ram Navami'),
('2025-04-06', 'Mahavir Jayanti'),
('2025-04-13', 'Vaisakhi'),
('2025-04-14', 'Ambedkar Jayanti'),
('2025-04-18', 'Good Friday'),
('2025-04-20', 'Easter Sunday'),
('2025-05-01', 'Labour Day'),
('2025-05-12', 'Eid al-Fitr (Ramzan Eid)'),
('2025-06-07', 'Jamat Ul-Vida'),
('2025-06-17', 'Bakri Eid (Eid al-Adha)'),
('2025-07-04', 'Guru Purnima'),
('2025-07-17', 'Muharram'),
('2025-08-15', 'Independence Day'),
('2025-08-19', 'Raksha Bandhan'),
('2025-08-26', 'Janmashtami'),
('2025-09-02', 'Ganesh Chaturthi'),
('2025-10-02', 'Gandhi Jayanti'),
('2025-10-12', 'Dussehra'),
('2025-10-27', 'Diwali'),
('2025-10-28', 'Govardhan Puja'),
('2025-10-29', 'Bhai Dooj'),
('2025-11-10', 'Chhath Puja'),
('2025-11-15', 'Guru Nanak Jayanti'),
('2025-12-25', 'Christmas Day'),
('2025-12-31', 'New Year''s Eve');
