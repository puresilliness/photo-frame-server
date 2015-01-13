import os
import sqlalchemy
import sqlalchemy.dialects.postgresql
import sqlalchemy.ext.declarative
import sqlalchemy.orm
import sqlalchemy.types
import uuid

DATABASE_PATH = os.getenv(
    'DATABASE_PATH',
    'sqlite:////home/application/local/databases/photoframe.sqlite')

ENGINE = sqlalchemy.create_engine(DATABASE_PATH, echo=True)
SESSION = sqlalchemy.orm.sessionmaker(bind=ENGINE)
Base = sqlalchemy.ext.declarative.declarative_base()


# via http://docs.sqlalchemy.org/en/rel_0_9/core/custom_types.html
# #backend-agnostic-guid-type
class GUID(sqlalchemy.types.TypeDecorator):
    """Platform-independent GUID type.

    Uses Postgresql's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.

    """
    impl = sqlalchemy.types.CHAR

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(
                sqlalchemy.dialects.postgresql.UUID())
        else:
            return dialect.type_descriptor(sqlalchemy.types.CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value)
            else:
                # hexstring
                return "%.32x" % value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return uuid.UUID(value)


class User(Base):
    """An SQL mapping to the users table."""
    __tablename__ = 'users'

    id = sqlalchemy.Column(GUID, primary_key=True)
    email_id = sqlalchemy.Column(sqlalchemy.String)


class AuthorizedEmail(Base):
    """An SQL mapping to the authorized email addresses that can send pictures
    to users."""
    __tablename__ = 'authorized_emails'

    id = sqlalchemy.Column(GUID, primary_key=True)
    email = sqlalchemy.Column(sqlalchemy.String, primary_key=True)


class Photo(Base):
    """A list of photos that have not been downloaded yet by the user's photo
    frame client."""
    __tablename__ = 'photos'

    id = sqlalchemy.Column(GUID, primary_key=True)
    email = sqlalchemy.Column(sqlalchemy.String)
    photo_id = sqlalchemy.Column(GUID, primary_key=True)
