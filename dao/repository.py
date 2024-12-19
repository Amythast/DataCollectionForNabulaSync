import asyncio
from datetime import datetime
from typing import List, Dict

from dao.async_db import AsyncMysqlDB
from dao.db import init_db
from dao.model import LiveRecord, LiveTarget
from common.logger import logger
from dao.dao_var import db_var


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
        logger.info(f"query live record by id: {id} success")
        return rows[0]
    logger.warning(f"query live record by id: {id} failed")
    return dict()


async def add_new_content(content_item: Dict) -> int:
    """
    新增一条内容记录（xhs的帖子 ｜ 抖音的视频 ｜ 微博 ｜ 快手视频 ...）
    Args:
        content_item:

    Returns:

    """
    async_db_conn: AsyncMysqlDB = db_var.get()
    last_row_id: int = await async_db_conn.item_to_table("nebula_live_stream_records", content_item)
    logger.info(f"add new content success, last row id: {last_row_id}")
    return last_row_id


async def update_content_by_content_id(content_id: int, content_item: Dict) -> int:
    """
    更新一条记录（xhs的帖子 ｜ 抖音的视频 ｜ 微博 ｜ 快手视频 ...）
    Args:
        content_id:
        content_item:

    Returns:

    """
    async_db_conn: AsyncMysqlDB = db_var.get()
    effect_row: int = await async_db_conn.update_table("nebula_live_stream_records", content_item, "id", content_id)
    logger.info(f"update content by content id: {content_id} success, effect row: {effect_row}")
    return effect_row


async def query_live_record_by_anchor_name(anchor_name: str) -> List[Dict]:
    """
    查询主播记录
    Args:
        anchor_name:

    Returns:

    """
    async_db_conn: AsyncMysqlDB = db_var.get()
    sql: str = f"select * from nebula_live_stream_records where anchor_name = '{anchor_name}'"
    rows: List[Dict] = await async_db_conn.query(sql)
    if len(rows) <= 0:
        logger.warning(f"query creator by anchor name: {anchor_name} failed")
    else:
        logger.info(f"query creator by anchor name: {anchor_name} success")
    return rows


async def update_live_record_by_anchor_name(anchor_name: str, anchor_item: Dict) -> int:
    """
    更新主播信息
    Args:
        anchor_name:
        anchor_item:

    Returns:

    """
    async_db_conn: AsyncMysqlDB = db_var.get()
    effect_row: int = await async_db_conn.update_table(
        table_name="nebula_live_stream_records",
        updates=anchor_item,
        field_where="anchor_name",
        value_where=anchor_name
    )
    logger.info(f"update creator by anchor name: {anchor_name} success, effect row: {effect_row}")
    return effect_row


async def query_target_live_by_platform(platfrom: str) -> List[LiveTarget]:
    """
    按平台查询要录制的直播
    Returns:

    """
    async_db_conn: AsyncMysqlDB = db_var.get()
    sql: str = f"select * from nebula_live_stream_target where live_platform = '{platfrom}' and need_record = 1"
    rows: List[Dict] = await async_db_conn.query(sql)
    if len(rows) <= 0:
        logger.warning(f"query_target_live failed")
    else:
        logger.info(f"query_target_live success, {len(rows)} will be recorded")

    live_targets = [
        LiveTarget(
            id=row.get("id"),
            live_id=row.get("live_id"),
            anchor_name=row.get("anchor_name"),
            category=row.get("category"),
            platform=row.get("platform"),
            url=row.get("url"),
            need_record=row.get("need_record"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )
        for row in rows
    ]
    return live_targets


async def query_live_record_by_anchor_name_and_slice(anchor_name: str, live_slice: str) -> List[Dict]:
    """
    查询直播记录
    Args:
        anchor_name:
        live_slice:

    Returns:

    """
    async_db_conn: AsyncMysqlDB = db_var.get()
    sql: str = f"select * from nebula_live_stream_records where anchor_name = '{anchor_name}' and live_slice = '{live_slice}'"
    rows: List[Dict] = await async_db_conn.query(sql)
    if len(rows) <= 0:
        logger.warning(f"query live record by anchor name and slice failed")
    else:
        logger.info(f"query live record by anchor name and slice success")
    return rows


async def save_live_file(record: LiveRecord) -> int:
    """
    保存录制的直播视频/音频/弹幕文件
    """
    async_db_conn: AsyncMysqlDB = db_var.get()
    existing_record = await async_db_conn.get_first(
        "SELECT id FROM nebula_live_stream_records WHERE anchor_name=%s AND platform=%s AND live_slice=%s",
        record.anchor_name, record.platform, record.live_slice
    )

    item = {
        "anchor_name": record.anchor_name,
        "platform": record.platform,
        "category": record.category,
        "live_date": record.live_date,
        "age": record.age,
        "gender": record.gender,
        "live_url": record.live_url,
        "live_slice": record.live_slice,
        "live_stream_file": record.live_stream_file,
        "live_stream_transform": record.live_stream_transform,
        "live_danmu_file": record.live_danmu_file,
        "live_danmu_transform": record.live_danmu_transform,
    }

    if existing_record:
        # 如果记录存在，执行更新操作
        effect_row_id = await async_db_conn.update_table(
            "nebula_live_stream_records",
            item,
            field_where="id",
            value_where=existing_record["id"]
        )
        logger.info(f"Updated live stream record by id: {existing_record['id']}, affected rows id: {effect_row_id}")
    else:
        effect_row_id = await async_db_conn.item_to_table("nebula_live_stream_records", item)
        logger.info(f"Inserted new live stream record, new id: {effect_row_id}")

    return effect_row_id


# test
async def _test_save_live_file():
    await init_db()

    record = LiveRecord(
        anchor_name="test",
        platform="test",
        category="test",
        live_date=datetime(2024, 11, 17, 18, 30, 45),
        age=18,
        gender="male",
        live_slice="0",
        live_url="test",
        live_stream_file="video_save_path/test"
    )
    effect_row = await save_live_file(record)
    logger.info(f"effect row: {effect_row}")


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(_test_save_live_file())
