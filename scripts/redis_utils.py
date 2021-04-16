import redis
from backend.user_manager import UserManager

redis_pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
r = redis.Redis(connection_pool=redis_pool)
#r.delete("1000013")

user_manager = UserManager(redis_pool)
user_manager.create_user("Sam2", "even-more-stronky-bonky-paswordy")

for k in r.scan_iter():
    print(k)

