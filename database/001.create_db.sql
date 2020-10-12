-- UTF-8 without BOM
-- скрипт выполняется с правами суперпользователя postgres
-- скрипт создаёт табличные пространства, базу данных, пользователя для работы с новой БД и выдаёт права

DROP DATABASE qi_db;
DROP USER qi_user;

CREATE DATABASE qi_db
    WITH 
    --по умолчанию:OWNER = postgres
    ENCODING = 'UTF8'
    --порядок сортировки:LC_COLLATE = 'Russian_Russia.1251'
    --порядок сортировки:LC_CTYPE = 'Russian_Russia.1251'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

--по умолчанию:GRANT ALL ON DATABASE qi_db TO postgres;
--по умолчанию:GRANT TEMPORARY, CONNECT ON DATABASE qi_db TO PUBLIC;

CREATE USER qi_user
    WITH
    LOGIN PASSWORD 'qi_LAZ7dBLmSJb9' -- this is the value you probably need to edit
    NOSUPERUSER
    INHERIT
    NOCREATEDB
    NOCREATEROLE
    NOREPLICATION;

GRANT ALL ON DATABASE qi_db TO qi_user;
