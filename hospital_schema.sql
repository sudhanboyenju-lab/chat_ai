-- Matches entity_table / entity_id_field / detail_fields / child_table in hospital_config.py

CREATE TABLE doctors (
    doctor_id      VARCHAR(50)  PRIMARY KEY,
    doctor_name    VARCHAR(255) NOT NULL,
    specialization VARCHAR(150),
    department     VARCHAR(150),
    fee            DECIMAL(10,2),
    availability   VARCHAR(255)   -- e.g. "Sun-Fri, 10am-2pm"
);

CREATE TABLE doctor_qualifications (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    doctor_id     VARCHAR(50) NOT NULL,
    qualification VARCHAR(255) NOT NULL,
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE CASCADE
);

-- Example rows
INSERT INTO doctors (doctor_id, doctor_name, specialization, department, fee, availability) VALUES
    ('d001', 'Dr. Rita Sharma', 'Cardiologist', 'Cardiology', 800.00, 'Sun-Fri, 10am-2pm'),
    ('d002', 'Dr. Bikash Thapa', 'Pediatrician', 'Pediatrics', 600.00, 'Sun-Thu, 9am-1pm');

INSERT INTO doctor_qualifications (doctor_id, qualification) VALUES
    ('d001', 'MBBS'),
    ('d001', 'MD Cardiology'),
    ('d002', 'MBBS'),
    ('d002', 'DCH (Pediatrics)');
