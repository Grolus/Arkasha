
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, text, BIGINT

from config.constants import (
    MAX_SUBJECT_NAME_LENGTH, 
    MAX_HOMEWORK_LENGTH, 
    MAX_CLASS_NAME_LENGTH,
    MAX_ATTACHMENT_URL_LENGTH
)
from enums import GroupNumberEnum

from .database import Base





class SubjectBase(Base):
    __tablename__ = 'subject'
    
    name: Mapped[str] = mapped_column(String(MAX_SUBJECT_NAME_LENGTH))
    class_id: Mapped[int] = mapped_column(ForeignKey('classtable.id', ondelete='CASCADE'))
    
    class_: Mapped['ClassBase'] = relationship(
        'ClassBase',
        back_populates='subjects'
    )
    
class ClassBase(Base):
    __tablename__ = 'classtable'
    
    name: Mapped[str] = mapped_column(String(MAX_CLASS_NAME_LENGTH), unique=True)
    creator_username: Mapped[str] = mapped_column(String(32))
    # timetable: Mapped[dict] = mapped_column(JSON)
    # """Расписание в формате {weekday: [null, subject, {group_number: subject, group_number: subject}, ...], ...}"""
    
    subjects: Mapped[list['SubjectBase']] = relationship(
        'SubjectBase',
        back_populates='class_',
        cascade='all, delete-orphan'
    )
    lessons: Mapped[list['LessonBase']] = relationship(
        'LessonBase', 
        back_populates='class_', 
        lazy='joined',
        cascade='all, delete-orphan'
    )
    chats: Mapped[list['ClassChatBase']] = relationship(
        'ClassChatBase',
        back_populates='class_',
        cascade='all, delete-orphan'
    )
    
class ClassChatBase(Base):
    __tablename__ = 'classchat'
    
    chat_id: Mapped[int] = mapped_column(BIGINT, unique=True)
    class_id: Mapped[int] = mapped_column(ForeignKey('classtable.id', ondelete='CASCADE'))
    
    class_: Mapped[ClassBase] = relationship(
        'ClassBase',
        back_populates='chats'
    )
    
    
class LessonBase(Base):
    __tablename__ = 'lesson'
    
    weekday_number: Mapped[int]
    position: Mapped[int]
    group_number: Mapped[GroupNumberEnum] = mapped_column(default=GroupNumberEnum.NOT_GROUPED, server_default=text("'not_grouped'"))
    class_id: Mapped[int] = mapped_column(ForeignKey('classtable.id', ondelete='cascade'))
    subject_id: Mapped[int] = mapped_column(ForeignKey('subject.id', ondelete='cascade'))
    
    class_: Mapped['ClassBase'] = relationship(
        'ClassBase',
        back_populates='lessons',
    )
    subject: Mapped['SubjectBase'] = relationship(
        'SubjectBase',
        lazy='immediate'
    )


# class LessonSubjectBase(Base):
#     lesson_id: Mapped[int] = mapped_column(ForeignKey('lesson.id'))
#     subject_id: Mapped[int] = mapped_column(ForeignKey('subject.id'))
    

class HomeworkBase(Base):
    __tablename__ = 'homework'
    
    text: Mapped[str] = mapped_column(String(MAX_HOMEWORK_LENGTH))
    class_id: Mapped[int] = mapped_column(ForeignKey('classtable.id', ondelete='cascade'))
    lesson_id: Mapped[int] = mapped_column(ForeignKey('lesson.id', ondelete='cascade'))
    week: Mapped[int]
    year: Mapped[int]
    attachment_url: Mapped[str] = mapped_column(String(MAX_ATTACHMENT_URL_LENGTH), nullable=True)
    
    class_: Mapped['ClassBase'] = relationship(
        'ClassBase',
        lazy='immediate'
    )
    
    lesson: Mapped['LessonBase'] = relationship(
        'LessonBase',
        lazy='joined'
    )
    
    
