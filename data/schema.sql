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
    department VARCHAR(100),
    email VARCHAR(100) NULL,
    phone VARCHAR(15) NULL
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
    arrangement_details TEXT NULL,
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
    arrangement_details TEXT NULL,
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
INSERT INTO users (user_id, password, role, name, department, email, phone) VALUES
-- ===== CSE Department =====
('CSEFAC001','pass','faculty','Dr. Alice Johnson','CSE','alice.johnson@example.com','1234567890'),
('CSEFAC002','pass','faculty','Prof. Bob Smith','CSE','bob.smith@example.com','1234567891'),
('CSEFAC003','pass','faculty','Dr. Carol Davis','CSE','carol.davis@example.com','1234567892'),
('CSEFAC004','pass','faculty','Prof. David Wilson','CSE','david.wilson@example.com','1234567893'),
('CSEFAC005','pass','faculty','Dr. Emma Brown','CSE','emma.brown@example.com','1234567894'),
('CSEFAC006','pass','faculty','Prof. Frank Miller','CSE','frank.miller@example.com','1234567895'),
('CSEFAC007','pass','faculty','Dr. Grace Lee','CSE','grace.lee@example.com','1234567896'),
('CSEFAC008','pass','faculty','Prof. Henry Clark','CSE','henry.clark@example.com','1234567897'),
('CSEFAC009','pass','faculty','Dr. Irene Lewis','CSE','irene.lewis@example.com','1234567898'),
('CSEFAC010','pass','faculty','Prof. John White','CSE','john.white@example.com','1234567899'),

('CSESTF001','pass','staff','Staff Rahul','CSE','rahul@example.com','1234567890'),
('CSESTF002','pass','staff','Staff Kavya','CSE','kavya@example.com','1234567891'),
('CSESTF003','pass','staff','Staff Neha','CSE','neha@example.com','1234567892'),
('CSESTF004','pass','staff','Staff Arjun','CSE','arjun@example.com','1234567893'),
('CSESTF005','pass','staff','Staff Sneha','CSE','sneha@example.com','1234567894'),

('HODCSE','pass','hod','Dr. Meena','CSE','meena@example.com','1234567895'),

-- ===== ECE Department =====
('ECEFAC001','pass','faculty','Dr. Rajesh Kumar','ECE','rajesh.kumar@example.com','1234567890'),
('ECEFAC002','pass','faculty','Prof. Sunita Sharma','ECE','sunita.sharma@example.com','1234567891'),
('ECEFAC003','pass','faculty','Dr. Vikram Rao','ECE','vikram.rao@example.com','1234567892'),
('ECEFAC004','pass','faculty','Prof. Aarti Singh','ECE','aarti.singh@example.com','1234567893'),
('ECEFAC005','pass','faculty','Dr. Kiran Das','ECE','kiran.das@example.com','1234567894'),
('ECEFAC006','pass','faculty','Prof. Ramesh Patil','ECE','ramesh.patil@example.com','1234567895'),
('ECEFAC007','pass','faculty','Dr. Divya Nair','ECE','divya.nair@example.com','1234567896'),
('ECEFAC008','pass','faculty','Prof. Manish Gupta','ECE','manish.gupta@example.com','1234567897'),
('ECEFAC009','pass','faculty','Dr. Rohit Sen','ECE','rohit.sen@example.com','1234567898'),
('ECEFAC010','pass','faculty','Prof. Lata Iyer','ECE','lata.iyer@example.com','1234567899'),

('ECESTF001','pass','staff','Staff Rohan','ECE','rohan@example.com','1234567890'),
('ECESTF002','pass','staff','Staff Nisha','ECE','nisha@example.com','1234567891'),
('ECESTF003','pass','staff','Staff Karthik','ECE','karthik@example.com','1234567892'),
('ECESTF004','pass','staff','Staff Deepa','ECE','deepa@example.com','1234567893'),
('ECESTF005','pass','staff','Staff Manoj','ECE','manoj@example.com','1234567894'),

('HODECE','pass','hod','Dr. Rajesh','ECE','rajesh@example.com','1234567895'),

-- ===== ME Department =====
('MEFAC001','pass','faculty','Dr. Priya Reddy','ME','priya.reddy@example.com','1234567890'),
('MEFAC002','pass','faculty','Prof. Karthik Iyer','ME','karthik.iyer@example.com','1234567891'),
('MEFAC003','pass','faculty','Dr. Nikhil Sharma','ME','nikhil.sharma@example.com','1234567892'),
('MEFAC004','pass','faculty','Prof. Anjali Das','ME','anjali.das@example.com','1234567893'),
('MEFAC005','pass','faculty','Dr. Pooja Menon','ME','pooja.menon@example.com','1234567894'),
('MEFAC006','pass','faculty','Prof. Sanjay Rao','ME','sanjay.rao@example.com','1234567895'),
('MEFAC007','pass','faculty','Dr. Sneha Verma','ME','sneha.verma@example.com','1234567896'),
('MEFAC008','pass','faculty','Prof. Amit Tiwari','ME','amit.tiwari@example.com','1234567897'),
('MEFAC009','pass','faculty','Dr. Veena Kulkarni','ME','veena.kulkarni@example.com','1234567898'),
('MEFAC010','pass','faculty','Prof. Ritesh Jain','ME','ritesh.jain@example.com','1234567899'),

('MESTF001','pass','staff','Staff Suresh','ME','suresh@example.com','1234567890'),
('MESTF002','pass','staff','Staff Divya','ME','divya@example.com','1234567891'),
('MESTF003','pass','staff','Staff Naveen','ME','naveen@example.com','1234567892'),
('MESTF004','pass','staff','Staff Priya','ME','priya@example.com','1234567893'),
('MESTF005','pass','staff','Staff Tarun','ME','tarun@example.com','1234567894'),

('HODME','pass','hod','Dr. Priya','ME','priya.hod@example.com','1234567895'),

-- ===== Principal / Admin =====
('ADM001','pass','admin','Principal Raj','Management','raj@example.com','1234567890'),
('ADM002','pass','admin','Registrar Ram','Management','ram@example.com','1234567891');


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
