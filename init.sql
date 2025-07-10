-- Initialize employee_search database
-- This script runs when the PostgreSQL container starts for the first time

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE employee_search'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'employee_search')\gexec

-- Connect to the employee_search database
\c employee_search;

-- Grant all privileges to postgres user
GRANT ALL PRIVILEGES ON DATABASE employee_search TO postgres;

-- Create organizations table
CREATE TABLE IF NOT EXISTS organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    employee_fields JSON NOT NULL DEFAULT '[]'
);

-- Create employees table
CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES organizations(id),
    name VARCHAR(255) NOT NULL,
    department VARCHAR(100),
    location VARCHAR(100),
    position VARCHAR(100),
    contact_info VARCHAR(255),
    status VARCHAR(50),
    company VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    org_id INTEGER NOT NULL REFERENCES organizations(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for search optimization
CREATE INDEX IF NOT EXISTS idx_employees_org_id ON employees(org_id);
CREATE INDEX IF NOT EXISTS idx_employees_status ON employees(status);
CREATE INDEX IF NOT EXISTS idx_employees_location ON employees(location);
CREATE INDEX IF NOT EXISTS idx_employees_company ON employees(company);
CREATE INDEX IF NOT EXISTS idx_employees_department ON employees(department);
CREATE INDEX IF NOT EXISTS idx_employees_position ON employees(position);
CREATE INDEX IF NOT EXISTS idx_users_org_id ON users(org_id);

-- Insert sample organizations data
INSERT INTO organizations (name, employee_fields) VALUES
    ('TechCorp Inc.', '["name", "department", "position", "location", "contact_info", "status", "company", "org_id"]'),
    ('Global Solutions Ltd.', '["name", "department", "position", "location", "contact_info", "status", "company"]'),
    ('Innovation Systems', '["name", "department", "position", "location", "contact_info", "status", "company"]'),
    ('Digital Dynamics', '["name", "department", "position", "location", "contact_info", "status", "company"]'),
    ('Future Technologies', '["name", "department", "position", "location", "contact_info", "status", "company"]'),
    ('Smart Solutions Co.', '["name", "department", "position", "location", "contact_info", "status", "company"]'),
    ('NextGen Enterprises', '["name", "department", "position", "location", "contact_info", "status", "company"]'),
    ('Elite Innovations', '["name", "department", "position", "location", "contact_info", "status", "company"]'),
    ('Peak Performance Inc.', '["name", "department", "position", "location", "contact_info", "status", "company"]'),
    ('Visionary Ventures', '["name", "department", "position", "location", "contact_info", "status", "company"]')
ON CONFLICT (name) DO NOTHING;

-- Insert sample employees data
INSERT INTO employees (org_id, name, department, location, position, contact_info, status, company) VALUES
    (1, 'John Smith', 'Engineering', 'San Francisco', 'Senior Software Engineer', 'john.smith@techcorp.com', 'active', 'TechCorp Inc.'),
    (1, 'Sarah Johnson', 'Marketing', 'New York', 'Marketing Manager', 'sarah.johnson@techcorp.com', 'active', 'TechCorp Inc.'),
    (1, 'Mike Davis', 'Sales', 'Chicago', 'Sales Director', 'mike.davis@techcorp.com', 'active', 'TechCorp Inc.'),
    (1, 'Emily Wilson', 'HR', 'Los Angeles', 'HR Specialist', 'emily.wilson@techcorp.com', 'active', 'TechCorp Inc.'),
    (1, 'David Brown', 'Engineering', 'Austin', 'Frontend Developer', 'david.brown@techcorp.com', 'active', 'TechCorp Inc.'),
    (1, 'Lisa Garcia', 'Finance', 'Seattle', 'Financial Analyst', 'lisa.garcia@techcorp.com', 'active', 'TechCorp Inc.'),
    (1, 'Robert Martinez', 'Operations', 'Denver', 'Operations Manager', 'robert.martinez@techcorp.com', 'active', 'TechCorp Inc.'),
    (1, 'Jennifer Lee', 'Engineering', 'Boston', 'Backend Developer', 'jennifer.lee@techcorp.com', 'active', 'TechCorp Inc.'),
    (1, 'Thomas Anderson', 'Sales', 'Miami', 'Sales Representative', 'thomas.anderson@techcorp.com', 'active', 'TechCorp Inc.'),
    (1, 'Amanda Taylor', 'Marketing', 'Portland', 'Content Strategist', 'amanda.taylor@techcorp.com', 'active', 'TechCorp Inc.')
ON CONFLICT DO NOTHING;

-- Insert additional employees for other organizations
INSERT INTO employees (org_id, name, department, location, position, contact_info, status, company) VALUES
    (2, 'Alex Rodriguez', 'Engineering', 'Toronto', 'Full Stack Developer', 'alex.rodriguez@globalsolutions.com', 'active', 'Global Solutions Ltd.'),
    (2, 'Maria Gonzalez', 'Product Management', 'Vancouver', 'Product Manager', 'maria.gonzalez@globalsolutions.com', 'active', 'Global Solutions Ltd.'),
    (2, 'Carlos Silva', 'Sales', 'Montreal', 'Sales Executive', 'carlos.silva@globalsolutions.com', 'active', 'Global Solutions Ltd.'),
    (3, 'Sophie Chen', 'Research & Development', 'Berlin', 'Research Scientist', 'sophie.chen@innovationsystems.com', 'active', 'Innovation Systems'),
    (3, 'Hans Mueller', 'Engineering', 'Munich', 'Systems Architect', 'hans.mueller@innovationsystems.com', 'active', 'Innovation Systems'),
    (3, 'Elena Petrova', 'Marketing', 'Moscow', 'Marketing Director', 'elena.petrova@innovationsystems.com', 'active', 'Innovation Systems'),
    (4, 'James Wilson', 'Data Science', 'London', 'Data Scientist', 'james.wilson@digitaldynamics.com', 'active', 'Digital Dynamics'),
    (4, 'Emma Thompson', 'Design', 'Manchester', 'UX Designer', 'emma.thompson@digitaldynamics.com', 'active', 'Digital Dynamics'),
    (4, 'Oliver Brown', 'Engineering', 'Edinburgh', 'DevOps Engineer', 'oliver.brown@digitaldynamics.com', 'active', 'Digital Dynamics'),
    (5, 'Yuki Tanaka', 'AI Research', 'Tokyo', 'AI Engineer', 'yuki.tanaka@futuretech.com', 'active', 'Future Technologies'),
    (5, 'Kenji Yamamoto', 'Product Development', 'Osaka', 'Product Lead', 'kenji.yamamoto@futuretech.com', 'active', 'Future Technologies'),
    (5, 'Aiko Sato', 'Business Development', 'Yokohama', 'Business Analyst', 'aiko.sato@futuretech.com', 'active', 'Future Technologies'),
    (6, 'Raj Patel', 'Software Engineering', 'Bangalore', 'Senior Developer', 'raj.patel@smartsolutions.com', 'active', 'Smart Solutions Co.'),
    (6, 'Priya Sharma', 'Quality Assurance', 'Mumbai', 'QA Lead', 'priya.sharma@smartsolutions.com', 'active', 'Smart Solutions Co.'),
    (6, 'Arun Kumar', 'Operations', 'Delhi', 'Operations Director', 'arun.kumar@smartsolutions.com', 'active', 'Smart Solutions Co.'),
    (7, 'Lucas Santos', 'Innovation', 'São Paulo', 'Innovation Manager', 'lucas.santos@nextgen.com', 'active', 'NextGen Enterprises'),
    (7, 'Ana Costa', 'Engineering', 'Rio de Janeiro', 'Backend Engineer', 'ana.costa@nextgen.com', 'active', 'NextGen Enterprises'),
    (7, 'Pedro Oliveira', 'Sales', 'Brasília', 'Sales Manager', 'pedro.oliveira@nextgen.com', 'active', 'NextGen Enterprises'),
    (8, 'Nina Ivanova', 'Research', 'St. Petersburg', 'Research Lead', 'nina.ivanova@eliteinnovations.com', 'active', 'Elite Innovations'),
    (8, 'Dmitry Volkov', 'Engineering', 'Novosibirsk', 'Software Engineer', 'dmitry.volkov@eliteinnovations.com', 'active', 'Elite Innovations'),
    (8, 'Svetlana Popova', 'Marketing', 'Kazan', 'Marketing Specialist', 'svetlana.popova@eliteinnovations.com', 'active', 'Elite Innovations'),
    (9, 'Marcus Johnson', 'Performance Analytics', 'Sydney', 'Analytics Manager', 'marcus.johnson@peakperformance.com', 'active', 'Peak Performance Inc.'),
    (9, 'Zoe Williams', 'Engineering', 'Melbourne', 'Frontend Developer', 'zoe.williams@peakperformance.com', 'active', 'Peak Performance Inc.'),
    (9, 'Ethan Davis', 'Sales', 'Brisbane', 'Sales Representative', 'ethan.davis@peakperformance.com', 'active', 'Peak Performance Inc.'),
    (10, 'Isabella Martinez', 'Strategic Planning', 'Mexico City', 'Strategy Director', 'isabella.martinez@visionaryventures.com', 'active', 'Visionary Ventures'),
    (10, 'Diego Fernandez', 'Engineering', 'Guadalajara', 'Mobile Developer', 'diego.fernandez@visionaryventures.com', 'active', 'Visionary Ventures'),
    (10, 'Carmen Ruiz', 'Business Development', 'Monterrey', 'Business Development Manager', 'carmen.ruiz@visionaryventures.com', 'active', 'Visionary Ventures')
ON CONFLICT DO NOTHING;

-- Insert sample users data
-- Raw passwords are: "testpass"
INSERT INTO users (username, hashed_password, org_id) VALUES
    ('admin_techcorp', '$2b$12$DJ35496SLjvb2vdjgRDdD.oJtvY/VJ1iVkMH3du3mNV3ffWkUV.k6', 1),
    ('hr_manager', '$2b$12$DJ35496SLjvb2vdjgRDdD.oJtvY/VJ1iVkMH3du3mNV3ffWkUV.k6', 1),
    ('sales_lead', '$2b$12$DJ35496SLjvb2vdjgRDdD.oJtvY/VJ1iVkMH3du3mNV3ffWkUV.k6', 2),
    ('dev_team_lead', '$2b$12$DJ35496SLjvb2vdjgRDdD.oJtvY/VJ1iVkMH3du3mNV3ffWkUV.k6', 3),
    ('marketing_coord', '$2b$12$DJ35496SLjvb2vdjgRDdD.oJtvY/VJ1iVkMH3du3mNV3ffWkUV.k6', 5),
    ('finance_admin', '$2b$12$DJ35496SLjvb2vdjgRDdD.oJtvY/VJ1iVkMH3du3mNV3ffWkUV.k6', 7),
    ('ops_supervisor', '$2b$12$DJ35496SLjvb2vdjgRDdD.oJtvY/VJ1iVkMH3du3mNV3ffWkUV.k6', 4),
    ('qa_engineer', '$2b$12$DJ35496SLjvb2vdjgRDdD.oJtvY/VJ1iVkMH3du3mNV3ffWkUV.k6', 10),
    ('product_manager', '$2b$12$DJ35496SLjvb2vdjgRDdD.oJtvY/VJ1iVkMH3du3mNV3ffWkUV.k6', 10),
    ('support_specialist', '$2b$12$DJ35496SLjvb2vdjgRDdD.oJtvY/VJ1iVkMH3du3mNV3ffWkUV.k6', 10)
ON CONFLICT (username) DO NOTHING; 