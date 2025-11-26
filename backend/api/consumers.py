import json
import os
from channels.generic.websocket import AsyncWebsocketConsumer
from .utils import get_files
from asgiref.sync import sync_to_async


class FileFindConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        base_dir = r"L:\TO_Traffic\TMC"
        with open(os.path.join(base_dir, "TMCGIS/search_folders.json"), 'r') as f:
            search_folders = json.load(f)
        sig_id = self.scope['url_route']['kwargs']['sig_id']

        for key, folder_name in search_folders.items():
            path = os.path.join(base_dir, folder_name)
            # Use sync_to_async to run the generator in a thread
            async for file_path in self._stream_files(path, sig_id):
                await self.send(text_data=json.dumps({
                    'type': key,
                    'file': file_path
                }))
        await self.send(text_data=json.dumps({"done": True}))
        await self.close()

    async def _stream_files(self, path, looking_for):
        # This helper wraps the generator so it yields in a thread
        for file_path in await sync_to_async(list, thread_sensitive=False)(get_files(path, looking_for)):
            yield file_path