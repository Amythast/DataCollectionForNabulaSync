from typing import List, Dict

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dao.async_db import AsyncMysqlDB
from dao.model import LiveStreamRecord, FinetuneData
from var import db_var


async def query_live_record_by_id(id: int) -> Dict:
    """
    查询一条直播内容记录
    Args:
        id:

    Returns:

    """
    async_db_conn: AsyncMysqlDB = db_var.get()
    sql: str = f"select * from nebula_live_stream_records where id = '{id}'"
    rows: List[Dict] = await async_db_conn.query(sql)
    if len(rows) > 0:
        return rows[0]
    return dict()


async def add_new_content(content_item: Dict) -> int:
    """
    新增一条内容记录（xhs的帖子 ｜ 抖音的视频 ｜ 微博 ｜ 快手视频 ...）
    Args:
        content_item:

    Returns:

    """
    async_db_conn: AsyncMysqlDB = media_crawler_db_var.get()
    last_row_id: int = await async_db_conn.item_to_table("douyin_aweme", content_item)
    return last_row_id


async def update_content_by_content_id(content_id: str, content_item: Dict) -> int:
    """
    更新一条记录（xhs的帖子 ｜ 抖音的视频 ｜ 微博 ｜ 快手视频 ...）
    Args:
        content_id:
        content_item:

    Returns:

    """
    async_db_conn: AsyncMysqlDB = media_crawler_db_var.get()
    effect_row: int = await async_db_conn.update_table("douyin_aweme", content_item, "aweme_id", content_id)
    return effect_row



async def query_comment_by_comment_id(comment_id: str) -> Dict:
    """
    查询一条评论内容
    Args:
        comment_id:

    Returns:

    """
    async_db_conn: AsyncMysqlDB = media_crawler_db_var.get()
    sql: str = f"select * from douyin_aweme_comment where comment_id = '{comment_id}'"
    rows: List[Dict] = await async_db_conn.query(sql)
    if len(rows) > 0:
        return rows[0]
    return dict()


async def add_new_comment(comment_item: Dict) -> int:
    """
    新增一条评论记录
    Args:
        comment_item:

    Returns:

    """
    async_db_conn: AsyncMysqlDB = media_crawler_db_var.get()
    last_row_id: int = await async_db_conn.item_to_table("douyin_aweme_comment", comment_item)
    return last_row_id


async def update_comment_by_comment_id(comment_id: str, comment_item: Dict) -> int:
    """
    更新增一条评论记录
    Args:
        comment_id:
        comment_item:

    Returns:

    """
    async_db_conn: AsyncMysqlDB = media_crawler_db_var.get()
    effect_row: int = await async_db_conn.update_table("douyin_aweme_comment", comment_item, "comment_id", comment_id)
    return effect_row


async def query_creator_by_user_id(user_id: str) -> Dict:
    """
    查询一条创作者记录
    Args:
        user_id:

    Returns:

    """
    async_db_conn: AsyncMysqlDB = media_crawler_db_var.get()
    sql: str = f"select * from dy_creator where user_id = '{user_id}'"
    rows: List[Dict] = await async_db_conn.query(sql)
    if len(rows) > 0:
        return rows[0]
    return dict()


async def add_new_creator(creator_item: Dict) -> int:
    """
    新增一条创作者信息
    Args:
        creator_item:

    Returns:

    """
    async_db_conn: AsyncMysqlDB = media_crawler_db_var.get()
    last_row_id: int = await async_db_conn.item_to_table("dy_creator", creator_item)
    return last_row_id


async def update_creator_by_user_id(user_id: str, creator_item: Dict) -> int:
    """
    更新一条创作者信息
    Args:
        user_id:
        creator_item:

    Returns:

    """
    async_db_conn: AsyncMysqlDB = media_crawler_db_var.get()
    effect_row: int = await async_db_conn.update_table("dy_creator", creator_item, "user_id", user_id)
    return effect_row


def add_live_stream_record(
        anchor_name,
        platform,
        category,
        age,
        gender,
        live_date,
        live_address,
        live_stream_file,
        live_stream_transform,
        live_danmu_file,
        live_danmu_transform
):
    Session = sessionmaker(bind=engine)
    session = Session()
    new_record = LiveStreamRecord(
        anchor_name=anchor_name,
        platform=platform,
        category=category,
        age=age,
        gender=gender,
        live_date=live_date,
        live_address=live_address,
        live_stream_file=live_stream_file,
        live_stream_transform=live_stream_transform,
        live_danmu_file=live_danmu_file,
        live_danmu_transform=live_danmu_transform
    )
    session.add(new_record)
    session.commit()
    session.close()


def query_live_stream_record():
    Session = sessionmaker(bind=engine)
    session = Session()
    records = session.query(LiveStreamRecord).all()
    session.close()
    return records


def add_finetune_data(
        anchor_name,
        platform,
        category,
        live_date,
        target_platform,
        data
):
    Session = sessionmaker(bind=engine)
    session = Session()
    new_record = FinetuneData(
        anchor_name=anchor_name,
        platform=platform,
        category=category,
        live_date=live_date,
        target_platform=target_platform,
        data=data
    )
    session.add(new_record)
    session.commit()
    session.close()


def query_finetune_data():
    Session = sessionmaker(bind=engine)
    session = Session()
    records = session.query(FinetuneData).all()
    session.close()
    return records


# test
if __name__ == '__main__':
    add_live_stream_record(
        anchor_name='Kslala666',
        platform='Kuaishou',
        category='Beauty',
        live_date='2021-12-12 12:12:12',
        live_address='https://www.kuaishou.com',
        live_stream_file=b'',
        live_stream_transform={},
        live_danmu_file=b'',
        live_danmu_transform={}
    )
