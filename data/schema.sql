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
    substitute_user_id VARCHAR(50) NULL,
    substitute_status ENUM('Pending','Accepted','Rejected','Not Applicable') DEFAULT 'Pending',
    hod_status ENUM('Pending','Approved','Rejected') DEFAULT 'Pending',
    principal_status ENUM('Pending','Approved','Rejected') DEFAULT 'Pending',
    final_status VARCHAR(20) DEFAULT 'Pending',
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    substitute_responded_at TIMESTAMP NULL,
    hod_responded_at TIMESTAMP NULL,
    principal_responded_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (substitute_user_id) REFERENCES users(user_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
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

-- Sample Users
INSERT INTO users (user_id, password, role, name, department) VALUES
-- ===== CSE Department =====
('CSEFAC001','pass','faculty','Dr. Alice Johnson','CSE'),
('CSEFAC002','pass','faculty','Prof. Bob Smith','CSE'),
('CSEFAC003','pass','faculty','Dr. Carol Davis','CSE'),
('CSEFAC004','pass','faculty','Prof. David Wilson','CSE'),
('CSEFAC005','pass','faculty','Dr. Emma Brown','CSE'),
('CSEFAC006','pass','faculty','Prof. Frank Miller','CSE'),
('CSEFAC007','pass','faculty','Dr. Grace Lee','CSE'),
('CSEFAC008','pass','faculty','Prof. Henry Clark','CSE'),
('CSEFAC009','pass','faculty','Dr. Irene Lewis','CSE'),
('CSEFAC010','pass','faculty','Prof. John White','CSE'),

('CSESTF001','pass','staff','Staff Rahul','CSE'),
('CSESTF002','pass','staff','Staff Kavya','CSE'),
('CSESTF003','pass','staff','Staff Neha','CSE'),
('CSESTF004','pass','staff','Staff Arjun','CSE'),
('CSESTF005','pass','staff','Staff Sneha','CSE'),

('HODCSE','pass','hod','Dr. Meena','CSE'),

-- ===== ECE Department =====
('ECEFAC001','pass','faculty','Dr. Rajesh Kumar','ECE'),
('ECEFAC002','pass','faculty','Prof. Sunita Sharma','ECE'),
('ECEFAC003','pass','faculty','Dr. Vikram Rao','ECE'),
('ECEFAC004','pass','faculty','Prof. Aarti Singh','ECE'),
('ECEFAC005','pass','faculty','Dr. Kiran Das','ECE'),
('ECEFAC006','pass','faculty','Prof. Ramesh Patil','ECE'),
('ECEFAC007','pass','faculty','Dr. Divya Nair','ECE'),
('ECEFAC008','pass','faculty','Prof. Manish Gupta','ECE'),
('ECEFAC009','pass','faculty','Dr. Rohit Sen','ECE'),
('ECEFAC010','pass','faculty','Prof. Lata Iyer','ECE'),

('ECESTF001','pass','staff','Staff Rohan','ECE'),
('ECESTF002','pass','staff','Staff Nisha','ECE'),
('ECESTF003','pass','staff','Staff Karthik','ECE'),
('ECESTF004','pass','staff','Staff Deepa','ECE'),
('ECESTF005','pass','staff','Staff Manoj','ECE'),

('HODECE','pass','hod','Dr. Rajesh','ECE'),

-- ===== ME Department =====
('MEFAC001','pass','faculty','Dr. Priya Reddy','ME'),
('MEFAC002','pass','faculty','Prof. Karthik Iyer','ME'),
('MEFAC003','pass','faculty','Dr. Nikhil Sharma','ME'),
('MEFAC004','pass','faculty','Prof. Anjali Das','ME'),
('MEFAC005','pass','faculty','Dr. Pooja Menon','ME'),
('MEFAC006','pass','faculty','Prof. Sanjay Rao','ME'),
('MEFAC007','pass','faculty','Dr. Sneha Verma','ME'),
('MEFAC008','pass','faculty','Prof. Amit Tiwari','ME'),
('MEFAC009','pass','faculty','Dr. Veena Kulkarni','ME'),
('MEFAC010','pass','faculty','Prof. Ritesh Jain','ME'),

('MESTF001','pass','staff','Staff Suresh','ME'),
('MESTF002','pass','staff','Staff Divya','ME'),
('MESTF003','pass','staff','Staff Naveen','ME'),
('MESTF004','pass','staff','Staff Priya','ME'),
('MESTF005','pass','staff','Staff Tarun','ME'),

('HODME','pass','hod','Dr. Priya','ME'),

-- ===== Principal / Admin =====
('ADM001','pass','admin','Principal Raj','Admin');


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
