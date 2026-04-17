-- ============================================================
-- Script d'initialisation des bases de données PostgreSQL
-- Exécuté automatiquement au premier démarrage du container
-- ============================================================

-- 1. User microservice
SELECT 'CREATE DATABASE "GestionUserPI"'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'GestionUserPI')\gexec

-- 2. Course microservice
SELECT 'CREATE DATABASE "CoursePI"'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'CoursePI')\gexec

-- 3. ClubEvent microservice
SELECT 'CREATE DATABASE "ClubEventPI"'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ClubEventPI')\gexec

-- 4. Package microservice
SELECT 'CREATE DATABASE "GestionPackagePI"'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'GestionPackagePI')\gexec

-- 5. Quiz microservice
SELECT 'CREATE DATABASE "QuizPI"'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'QuizPI')\gexec

-- 6. Appointment microservice
SELECT 'CREATE DATABASE "AppointmentPI"'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'AppointmentPI')\gexec

-- 7. Discussion microservice
SELECT 'CREATE DATABASE "DiscussionPI"'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'DiscussionPI')\gexec
