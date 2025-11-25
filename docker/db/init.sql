-- Bootstrap roles and databases for individual services
CREATE USER auth WITH PASSWORD 'pass';
CREATE USER users WITH PASSWORD 'pass';
CREATE USER articles WITH PASSWORD 'pass';
CREATE USER reviews WITH PASSWORD 'pass';
CREATE USER editorial WITH PASSWORD 'pass';
CREATE USER notifications WITH PASSWORD 'pass';
CREATE USER fileprocessing WITH PASSWORD 'pass';

CREATE DATABASE auth OWNER auth;
CREATE DATABASE users OWNER users;
CREATE DATABASE articles OWNER articles;
CREATE DATABASE reviews OWNER reviews;
CREATE DATABASE editorial OWNER editorial;
CREATE DATABASE notifications OWNER notifications;
CREATE DATABASE fileprocessing OWNER fileprocessing;

GRANT ALL PRIVILEGES ON DATABASE auth TO auth;
GRANT ALL PRIVILEGES ON DATABASE users TO users;
GRANT ALL PRIVILEGES ON DATABASE articles TO articles;
GRANT ALL PRIVILEGES ON DATABASE reviews TO reviews;
GRANT ALL PRIVILEGES ON DATABASE editorial TO editorial;
GRANT ALL PRIVILEGES ON DATABASE notifications TO notifications;
GRANT ALL PRIVILEGES ON DATABASE fileprocessing TO fileprocessing;
