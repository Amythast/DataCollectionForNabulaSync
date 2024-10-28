from contextvars import ContextVar
import aiomysql

from dao.async_db import AsyncMysqlDB


db_var: ContextVar[AsyncMysqlDB] = ContextVar("db_var")
db_conn_pool_var: ContextVar[aiomysql.Pool] = ContextVar("db_conn_pool_var")
