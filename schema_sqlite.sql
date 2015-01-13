;; SQLite3 DB Schema
;; not recommended for production use, but should be fine for development
;; sqlite3 my.db < schema_sqlite.sql

CREATE TABLE users (
  id UUID UNIQUE NOT NULL,
  email_id VARCHAR UNIQUE NOT NULL,
  PRIMARY KEY (id)
);

CREATE TABLE authorized_emails (
  id UUID NOT NULL,
  email VARCHAR NOT NULL,
  PRIMARY KEY (id, email)
);

CREATE TABLE photos (
  id UUID NOT NULL,
  email VARCHAR NOT NULL,
  photo_id UUID NOT NULL,
  PRIMARY KEY (id, photo_id)
);
