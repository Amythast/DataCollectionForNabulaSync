from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, JSON, LargeBinary
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class LiveRecord(Base):
    __tablename__ = 'nebula_live_stream_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    anchor_name = Column(String(255), nullable=False, comment="主播名")
    platform = Column(String(255), nullable=False, comment="直播平台")
    category = Column(String(255), nullable=False, comment="直播分类")
    live_date = Column(DateTime, default=datetime.utcnow, comment="直播日期")
    age = Column(Integer, nullable=True, comment="主播年龄")
    gender = Column(String(255), nullable=True, comment="主播性别")
    live_url = Column(String(255), nullable=False, comment="直播间链接")
    live_slice = Column(String(255), nullable=False, comment="直播间片段名")
    live_stream_file = Column(LargeBinary, nullable=True, comment="直播间视频/音频原文件")
    live_stream_transform = Column(JSON, nullable=True, comment="直播间信息转json")
    live_danmu_file = Column(LargeBinary, nullable=True, comment="直播间弹幕文件")
    live_danmu_transform = Column(JSON, nullable=True, comment="直播间弹幕信息转json")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")


class FinetuneData(Base):
    __tablename__ = 'nebula_finetune_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    anchor_name = Column(String(255), nullable=False, comment="主播名")
    platform = Column(String(255), nullable=False, comment="直播平台")
    category = Column(String(255), nullable=False, comment="直播分类")
    live_date = Column(DateTime, default=datetime.utcnow, comment="直播日期")
    target_platform = Column(String(255), nullable=False, comment="数据目标平台")
    data = Column(JSON, nullable=True, comment="finetune dao")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")


class LiveTarget(Base):
    __tablename__ = 'nebula_live_target'

    id = Column(Integer, primary_key=True, autoincrement=True)
    live_id = Column(String(255), nullable=False, comment="直播间ID")
    anchor_name = Column(String(255), nullable=False, comment="主播名")
    category = Column(String(255), nullable=False, comment="直播类型")
    platform = Column(String(255), nullable=False, comment="直播平台")
    url = Column(String(255), nullable=False, comment="直播间URL")
    need_record = Column(Integer, default=True, comment="是否需要录制，1 需要, 0 不需要")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")