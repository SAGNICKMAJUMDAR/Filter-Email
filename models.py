import uuid
from enum import IntEnum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime,
    UniqueConstraint,
    Index,
)
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.inspection import inspect
from sqlalchemy.dialects.postgresql import UUID


Base = declarative_base()


class RoleEnum(IntEnum):
    SENDER = 1
    RECIPIENT = 2
    CC = 3
    BCC = 4


class IntEnumType(TypeDecorator):
    impl = Integer

    def __init__(self, enumtype, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._enumtype = enumtype

    def process_bind_param(self, value, dialect):
        return int(value) if value is not None else None

    def process_result_value(self, value, dialect):
        return self._enumtype(value) if value is not None else None


class Serializer:
    def to_dict(self):
        return {
            column_obj.key: getattr(self, column_obj.key)
            for column_obj in inspect(self).mapper.column_attrs
        }


class UserToken(Base, Serializer):
    __tablename__ = "user_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    credential_path = Column(String(255))
    email = Column(String(255), unique=True)
    token_data = Column(Text, nullable=False)


class Email(Base, Serializer):
    __tablename__ = "emails"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(String(255), nullable=False)
    gmail_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_tokens.id", ondelete="CASCADE"),
        nullable=False,
    )

    subject = Column(String(255))
    received_date = Column(DateTime)
    internal_date = Column(DateTime)

    user_token = relationship("UserToken", backref="emails")
    participants = relationship(
        "EmailParticipant", back_populates="email", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("message_id", "gmail_account_id", name="uix_message_account"),
        Index("ix_message_id", "message_id"),
        Index("ix_internal_date", "internal_date"),
    )


class EmailAddress(Base, Serializer):
    __tablename__ = "email_addresses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    address = Column(String(255), unique=True, nullable=False)

    participations = relationship("EmailParticipant", back_populates="email_address")


class EmailParticipant(Base, Serializer):
    __tablename__ = "email_participants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email_id = Column(
        UUID(as_uuid=True), ForeignKey("emails.id", ondelete="CASCADE"), nullable=False
    )
    email_address_id = Column(
        UUID(as_uuid=True),
        ForeignKey("email_addresses.id", ondelete="CASCADE"),
        nullable=False,
    )
    role = Column(IntEnumType(RoleEnum), nullable=False)

    email = relationship("Email", back_populates="participants")
    email_address = relationship("EmailAddress", back_populates="participations")

    __table_args__ = (
        Index("ix_email_role", "email_id", "role"),
        UniqueConstraint(
            "email_id", "email_address_id", "role", name="uix_email_participant"
        ),
    )
