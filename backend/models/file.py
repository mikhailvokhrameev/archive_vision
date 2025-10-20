# /models/file.py
import uuid
from sqlalchemy import Column, String, TIMESTAMP, ForeignKey, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base

class File(Base):
    __tablename__ = "files"
    file_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_extension = Column(String(10), nullable=False)
    load_date = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    transcripts = relationship("FileTranscript", back_populates="file")
    corrections = relationship("FileCorrection", back_populates="file")

class FileTranscript(Base):
    __tablename__ = "file_transcripts"
    transcript_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.file_id", ondelete="CASCADE"), nullable=False)
    transcript_path = Column(String, nullable=False) # Путь до JSON/TXT с результатом
    wer = Column(JSON, nullable=True) # Здесь может быть общая статистика, например, {'wer': 0.15}
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Back-reference to File
    file = relationship("File", back_populates="transcripts")

class FileCorrection(Base):
    __tablename__ = "file_corrections"
    correction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.file_id", ondelete="CASCADE"), nullable=False)
    corrected_text = Column(String, nullable=False)
    fragment_id = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Back-reference to File
    file = relationship("File", back_populates="corrections")
