
# mysql config
RELATION_DB_PWD = "xwt961121"
RELATION_DB_USER = "root"
RELATION_DB_HOST = "localhost"
RELATION_DB_PORT = "3306"
RELATION_DB_NAME = "nebula_data_collection"

RELATION_DB_URL = f"mysql://{RELATION_DB_USER}:{RELATION_DB_PWD}@{RELATION_DB_HOST}:{RELATION_DB_PORT}/{RELATION_DB_NAME}"

# redis config
REDIS_DB_HOST = "127.0.0.1"  # your redis host
REDIS_DB_PWD = "123456"  # your redis password
REDIS_DB_PORT = 6379  # your redis port
REDIS_DB_NUM = 0  # your redis db num

# cache type
CACHE_TYPE_REDIS = "redis"
CACHE_TYPE_MEMORY = "memory"
