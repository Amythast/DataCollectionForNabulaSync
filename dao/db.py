import asyncio
from typing import Dict
from urllib.parse import urlparse

import aiofiles
import aiomysql

from async_db import AsyncMysqlDB
from dao import db_config
from common.logger import logger
from dao.dao_var import db_conn_pool_var, db_var


def parse_mysql_url(mysql_url) -> Dict:
    """
    从配置文件中解析db链接url，给到aiomysql用，因为aiomysql不支持直接以URL的方式传递链接信息。
    Args:
        mysql_url: mysql://root:{RELATION_DB_PWD}@localhost:3306/media_crawler

    Returns:

    """
    parsed_url = urlparse(mysql_url)
    db_params = {
        'host': parsed_url.hostname,
        'port': parsed_url.port or 3306,
        'user': parsed_url.username,
        'password': parsed_url.password,
        'db': parsed_url.path.lstrip('/')
    }
    return db_params


async def init_db_inner():
    """
    初始化数据库链接池对象，并将该对象塞给db_var上下文变量
    Returns:

    """
    db_conn_params = parse_mysql_url(db_config.RELATION_DB_URL)
    pool = await aiomysql.create_pool(
        autocommit=True,
        **db_conn_params
    )
    async_db_obj = AsyncMysqlDB(pool)

    # 将连接池对象和封装的CRUD sql接口对象放到上下文变量中
    db_conn_pool_var.set(pool)
    db_var.set(async_db_obj)


async def init_db():
    """
    初始化db连接池
    Returns:

    """
    logger.info("[init_db] start init mediacrawler db connect object")
    await init_db_inner()
    logger.info("[init_db] end init mediacrawler db connect object")


async def close():
    """
    关闭连接池
    Returns:

    """
    logger.info("[close] close mediacrawler db pool")
    db_pool: aiomysql.Pool = db_conn_pool_var.get()
    if db_pool is not None:
        db_pool.close()


async def init_table_schema():
    """
    用来初始化数据库表结构，请在第一次需要创建表结构的时候使用，多次执行该函数会将已有的表以及数据全部删除
    Returns:

    """
    logger.info("[init_table_schema] begin init mysql table schema ...")
    await init_db_inner()
    async_db_obj: AsyncMysqlDB = db_var.get()
    async with aiofiles.open("dao/database-init.sql", mode="r", encoding="utf-8") as f:
        schema_sql = await f.read()
        await async_db_obj.execute(schema_sql)
        logger.info("[init_table_schema] table init successful")
        await close()


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(init_db())
