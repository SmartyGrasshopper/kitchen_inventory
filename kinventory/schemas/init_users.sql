DROP TABLE IF EXISTS users;

CREATE TABLE users(
    username TEXT UNIQUE NOT NULL PRIMARY KEY,
    psword TEXT NOT NULL,
    business_name TEXT
);