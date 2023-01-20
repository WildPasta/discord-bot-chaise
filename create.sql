DROP TABLE IF EXISTS USERS;
DROP TABLE IF EXISTS PUNCH;
DROP TABLE IF EXISTS HISTORY;

CREATE TABLE USERS (
    id_discord VARCHAR PRIMARY KEY
                       UNIQUE
                       NOT NULL,
    chaised    INTEGER NOT NULL,
    label      VARCHAR
);

CREATE TABLE PUNCH (
    id    INTEGER PRIMARY KEY AUTOINCREMENT
                  UNIQUE
                  NOT NULL,
    label TEXT    NOT NULL
);


CREATE TABLE HISTORY (
    id_history INTEGER PRIMARY KEY AUTOINCREMENT
                       NOT NULL
                       UNIQUE,
    id_discord VARCHAR,
    date       DATE
);
