from sqlalchemy import Column, Integer, String, Text #type: ignore
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class UserToken(Base):
    __tablename__ = 'user_tokens'

    id = Column(Integer, primary_key=True, autoincrement=True)
    credential_path = Column(String(255))
    email = Column(String(255), unique=True)
    token_data = Column(Text, nullable=False)