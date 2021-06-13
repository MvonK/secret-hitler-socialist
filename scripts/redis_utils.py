import aioredis
import asyncio
from backend.user_manager import UserManager


async def create_dummy_users():
    redis_pool = aioredis.ConnectionsPool("redis://localhost:6379", maxsize=10, minsize=0)
    #r.delete("1000013")

    user_manager = UserManager(redis_pool)
    #user_manager.create_user("Sam", "even-more-stronky-bonky-paswordy")
    #await user_manager.create_user("Red2", "newnamegoadadbrr")
    #user_manager.create_user("a", "b")
    await user_manager.create_user("a", "b")
    await user_manager.create_user("b", "c")
    await user_manager.create_user("c", "d")
    await user_manager.create_user("d", "e")
    await user_manager.create_user("e", "f")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(create_dummy_users())
