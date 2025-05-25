from datetime import datetime
import pytz
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settings

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(pytz.timezone(settings.TIMEZONE)), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(pytz.timezone(settings.TIMEZONE)), onupdate=lambda: datetime.now(pytz.timezone(settings.TIMEZONE)), nullable=False)
    
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns} 