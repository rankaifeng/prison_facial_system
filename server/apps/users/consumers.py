import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer

# 存储 Daphne 事件循环引用，供后台线程调度广播
_event_loop = None


def get_event_loop():
    return _event_loop


class DoorEventConsumer(AsyncWebsocketConsumer):
    group_name = 'door_events'

    async def connect(self):
        global _event_loop
        _event_loop = asyncio.get_running_loop()
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def door_event(self, event):
        await self.send(text_data=json.dumps(event['data'], ensure_ascii=False))
