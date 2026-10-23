-- Schema from the 2022 submission; no account or transaction records.

CREATE TABLE shares_owned (person_id INTEGER NOT NULL,
symbol TEXT NOT NULL,
shares INTEGER NOT NULL,
FOREIGN KEY(person_id) REFERENCES users(id));

CREATE TABLE transactions (id INTEGER PRIMARY KEY AUTOINCREMENT,
company TEXT NOT NULL,
symbol TEXT NOT NULL,
quote INT NOT NULL,
shares INT NOT NULL,
total INT NOT NULL,
person_id INT NOT NULL,
date_time NUMERIC,
trans_type TEXT DEFAULT 'BUY',
FOREIGN KEY (person_id) REFERENCES users(id));

CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
username TEXT NOT NULL,
hash TEXT NOT NULL,
cash NUMERIC NOT NULL DEFAULT 10000.00);

CREATE UNIQUE INDEX username ON users (username);
