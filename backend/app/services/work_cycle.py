import asyncio

import redis


class PauseManager:
    """Устанавливает глобальную паузу для обработки всех задач"""

    def __init__(self):
        self._redis_client = redis.StrictRedis(host="localhost", port=6379, db=0)
        self._redis_client.set("pause", "false")

    async def wait_if_paused(self):
        while self.is_paused():
            await asyncio.sleep(5)

    def set_pause(self):
        self._redis_client.set("pause", "true")

    def unset_pause(self):
        self._redis_client.set("pause", "false")

    def is_paused(self):
        return self._redis_client.get("pause") == b"true"


pause_manager = PauseManager()
