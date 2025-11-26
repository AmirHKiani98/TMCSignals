import json
import os
from channels.generic.websocket import AsyncWebsocketConsumer
from .utils import get_files


class FileFindConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.sig_id = self.scope['url_route']['kwargs']['sig_id'].lower()
        self.base_dir = r"L:\TO_Traffic\TMC"

        await self.accept()

        # search each folder type
        search_folders = {
            "front_page_sheets": r"001 - Front Page Sheets",
            "signal_timing": r"002 - Signal Timing",
            "fya": r"006 - FYA",
        }

        for key, folder_name in search_folders.items():
            path = os.path.join(self.base_dir, folder_name)
            for file_path in get_files(path, self.sig_id):
                await self.send(text_data=json.dumps({
                    'type': key,
                    'file': file_path
                }))

        await self.send(text_data=json.dumps({"done": True}))
        await self.close()