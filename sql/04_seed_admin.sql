-- 04_seed_admin.sql
-- Creates the default admin account.
-- Password: Admin@1234  (bcrypt hash — change immediately after first login)
-- Generate a fresh hash with: python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('YourPassword'))"

INSERT INTO users (user_name, user_email, user_password, user_role)
VALUES (
    'Admin',
    'admin@securedoc.local',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',  -- Admin@1234
    'admin'
)
ON CONFLICT (user_email) DO NOTHING;