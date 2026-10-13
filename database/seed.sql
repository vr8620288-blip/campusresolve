-- CampusResolve — reference seed data (PostgreSQL)
--
-- This is a plain-SQL mirror of backend/seed.py for reviewers who want to
-- see demo data at a glance. The RECOMMENDED way to seed the database is:
--
--     cd backend
--     python seed.py
--
-- because it correctly bcrypt-hashes the demo passwords. The INSERT below
-- for `users` is illustrative only — replace hashed_password with a real
-- bcrypt hash before using this file directly against a database.

INSERT INTO departments (name, description) VALUES
 ('IT Services', 'Computer labs, network and Wi-Fi'),
 ('Facilities & Maintenance', 'Electricity, plumbing, furniture, civil work'),
 ('Administration', 'General administration and campus operations'),
 ('Library', 'Library services and resources'),
 ('Security', 'Campus security and safety')
ON CONFLICT (name) DO NOTHING;

INSERT INTO categories (name) VALUES
 ('Classroom'), ('Laboratory'), ('Computer / IT'), ('Wi-Fi / Network'),
 ('Electricity'), ('Water / Plumbing'), ('Cleanliness'), ('Furniture'),
 ('Projector / Smart Board'), ('Library'), ('Security'), ('Canteen'),
 ('Washroom'), ('Parking'), ('Other')
ON CONFLICT (name) DO NOTHING;

-- Demo users (DEVELOPMENT ONLY). Passwords below are placeholders —
-- use `python seed.py` to create real, correctly-hashed accounts.
-- admin@smartcampus.edu   / Admin@123
-- staff@smartcampus.edu   / Staff@123
-- student@smartcampus.edu / Student@123
