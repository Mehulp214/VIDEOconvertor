#  This file is part of the VIDEOconvertor distribution.
#  Copyright (c) 2021 vasusen-code ; All rights reserved. 
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, version 3.
#
#  This program is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#  General Public License for more details.
#
#  License can be found in < https://github.com/vasusen-code/VIDEOconvertor/blob/public/LICENSE> .

import asyncio
import time
import os
from datetime import datetime as dt
from telethon import events
from telethon.tl.types import DocumentAttributeVideo
from ethon.telefunc import fast_download, fast_upload
from ethon.pyfunc import video_metadata
from .. import Drone, BOT_UN, LOG_CHANNEL
from main.plugins.actions import LOG_START, LOG_END
from LOCAL.localisation import SUPPORT_LINK, JPG
from LOCAL.utils import ffmpeg_progress

async def encode(event, msg, scale=0):
    ps_name = f"**{scale}p ENCODING:**"
    _ps = f"{scale}p ENCODE"
    Drone = event.client
    edit = await Drone.send_message(event.chat_id, "Trying to process.", reply_to=msg.id)
    new_name = f"out_{dt.now().isoformat('_', 'seconds')}"
    
    if hasattr(msg.media, "document"):
        file = msg.media.document
    else:
        file = msg.media
    
    mime = msg.file.mime_type
    
    if 'mp4' in mime:
        n = f"media_{dt.now().isoformat('_', 'seconds')}.mp4"
        out = f"{new_name}.mp4"
    elif msg.video:
        n = f"media_{dt.now().isoformat('_', 'seconds')}.mp4"
        out = f"{new_name}.mp4"
    elif 'x-matroska' in mime:
        n = f"media_{dt.now().isoformat('_', 'seconds')}.mkv" 
        out = f"{new_name}.mp4"            
    elif 'webm' in mime:
        n = f"media_{dt.now().isoformat('_', 'seconds')}.webm" 
        out = f"{new_name}.mp4"
    else:
        n = msg.file.name
        ext = n.split(".")[1]
        out = f"{new_name}.{ext}"
    
    DT = time.time()
    log = await LOG_START(event, f"**{_ps} PROCESS STARTED**\n\n[Bot is busy now]({SUPPORT_LINK})")
    log_end_text = f"**{_ps} PROCESS FINISHED**\n\n[Bot is free now]({SUPPORT_LINK})"
    
    try:
        await fast_download(n, file, Drone, edit, DT, "**DOWNLOADING:**")
    except Exception as e:
        await log.delete()
        await LOG_END(event, log_end_text)
        print(e)
        return await edit.edit(f"An error occurred while downloading.\n\nContact [SUPPORT]({SUPPORT_LINK})", link_preview=False) 
    
    name = f"__{dt.now().isoformat('_', 'seconds')}.mp4"
    os.rename(n, name)
    await edit.edit("Extracting metadata...")
    vid = video_metadata(name)
    hgt = int(vid['height'])
    wdt = int(vid['width'])
    
    if scale == hgt:
        os.remove(name)
        return await edit.edit(f"The video is already in {scale}p resolution.")
    
    if scale in [240, 360, 480, 720]:
        if scale == 240 and wdt == 426:
            os.remove(name)
            return await edit.edit(f"The video is already in {scale}p resolution.")
        elif scale == 360 and wdt == 640:
            os.remove(name)
            return await edit.edit(f"The video is already in {scale}p resolution.")
        elif scale == 480 and wdt == 854:
            os.remove(name)
            return await edit.edit(f"The video is already in {scale}p resolution.")
        elif scale == 720 and wdt == 1280:
            os.remove(name)
            return await edit.edit(f"The video is already in {scale}p resolution.")
    
    FT = time.time()
    progress = f"progress-{FT}.txt"
    cmd = f'ffmpeg -hide_banner -loglevel quiet -progress {progress} -i "{name}" -vf scale=-2:{scale} -c:a copy "{out}" -y'
    
    try:
        await ffmpeg_progress(cmd, name, progress, FT, edit, ps_name, log=log)
    except Exception as e:
        await log.delete()
        await LOG_END(event, log_end_text)
        print(e)
        return await edit.edit(f"An error occurred while encoding.\n\nContact [SUPPORT]({SUPPORT_LINK})", link_preview=False)  
    
    out2 = f"{dt.now().isoformat('_', 'seconds')}.mp4" 
    
    if msg.file.name:
        out2 = msg.file.name
    else:
        out2 = f"{dt.now().isoformat('_', 'seconds')}.mp4" 
    
    os.rename(out, out2)
    i_size = os.path.getsize(name)
    f_size = os.path.getsize(out2)     
    text = f"**{_ps}D by** : @{BOT_UN}"
    UT = time.time()
    
    await log.edit("Uploading file")
    
    try:
        uploader = await fast_upload(out2, out2, UT, Drone, edit, '**UPLOADING:**')
        await Drone.send_file(event.chat_id, uploader, caption=text, thumb=JPG, force_document=True)
    except Exception as e:
        await log.delete()
        await LOG_END(event, log_end_text)
        print(e)
        return await edit.edit(f"An error occurred while uploading.\n\nContact [SUPPORT]({SUPPORT_LINK})", link_preview=False)
    
    await edit.delete()
    os.remove(name)
    os.remove(out2)
    await log.delete()
    
    log_end_text2 = f'**{_ps} PROCESS FINISHED**\n\nTime Taken: {round((time.time()-DT)/60)} minutes\nInitial size: {i_size/1000000}mb.\nFinal size: {f_size/1000000}mb.\n\n[Bot is free now.]({SUPPORT_LINK})'
    await LOG_END(event, log_end_text2)
