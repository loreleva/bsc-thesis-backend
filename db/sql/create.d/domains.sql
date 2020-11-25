CREATE SCHEMA IF NOT EXISTS users;

CREATE SCHEMA IF NOT EXISTS errors;

CREATE TYPE var_type_fa AS ENUM('action','feature');
CREATE TYPE var_type_sc AS ENUM('simple','composite');
CREATE TYPE dom_type AS ENUM('boolean', 'integer', 'real');
CREATE DOMAIN public.smallString AS varchar(50);
CREATE DOMAIN public.longString AS varchar(254);
CREATE DOMAIN public.intGZ AS INTEGER CHECK (value > 0);
CREATE DOMAIN public.intGEZ AS INTEGER CHECK (value >= 0);
CREATE DOMAIN public.realGZ AS NUMERIC(1000,15) CHECK (value > 0);
CREATE DOMAIN public.real AS NUMERIC(1000,15);

CREATE DOMAIN users.smallString AS varchar(50);
CREATE DOMAIN users.longString AS varchar(254);
CREATE DOMAIN users.intGZ AS INTEGER CHECK (value > 0);
CREATE DOMAIN users.intGEZ AS INTEGER CHECK (value >= 0);
CREATE DOMAIN users.realGZ AS NUMERIC(1000,15) CHECK (value > 0);
CREATE DOMAIN users.real AS NUMERIC(1000,15);

CREATE DOMAIN errors.smallString AS varchar(50);
CREATE DOMAIN errors.longString AS varchar(254);