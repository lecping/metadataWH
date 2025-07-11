CREATE DATABASE analytics;

-- Set up permissions
GRANT ALL PRIVILEGES ON DATABASE datawarehouse TO ingest;
GRANT ALL PRIVILEGES ON DATABASE analytics TO ingest;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";