from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class ProcessingRequest(Base):
    __tablename__ = "processing_requests"
    request_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(20), default="PENDING")
    created_at = Column(DateTime, server_default="CURRENT_TIMESTAMP")
    completed_at = Column(DateTime)
    webhook_url = Column(String(255))

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    request_id = Column(UUID(as_uuid=True), ForeignKey("processing_requests.request_id"))
    serial_number = Column(Integer)
    product_name = Column(String(100))
    input_urls = Column(ARRAY(String))
    output_urls = Column(ARRAY(String))