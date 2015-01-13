;; PostgreSQL DB Schema
;; su postgres
;; createuser -P photo_frame_user
;; createdb photo_frame -O photo_frame_user
;; psql photo_frame
;; # GRANT ALL PRIVILEGES ON DATABASE photo_frame to photo_frame_user;
;; psql -h localhost -U photo_frame_user photo_frame

CREATE TABLE users (
  id UUID UNIQUE NOT NULL,
  email_id VARCHAR UNIQUE NOT NULL,
  PRIMARY KEY (id)
);
CREATE UNIQUE INDEX users_email_id_index ON users (email_id);

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
CREATE INDEX photos_id_index ON photos (id);
