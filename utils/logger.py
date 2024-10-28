# -*- coding: utf-8 -*-
import os
from loguru import logger

script_path = "/Volumes/External/sales_bot"
if not os.path.exists(script_path):
    script_path = "/"

logger.add(
    f"{script_path}/logs/{{time:YYYY-MM-DD}}.log",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}",
    serialize=False,
    enqueue=True,
    retention="30 days",
    rotation="00:00",
)
