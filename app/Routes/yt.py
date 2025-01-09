from fastapi import APIRouter, HTTPException
from app.utils.youtube_video import (
    download_video,
    list_video_formats_with_size,
)
from uuid import uuid4
import os
from fastapi.responses import FileResponse
from pydantic import HttpUrl, BaseModel


class InitiateDownload(BaseModel):

    url: str
    format_id: str


router = APIRouter(prefix="/yt", tags=["yt"])


@router.get("/")
def get_url_info(url: HttpUrl):
    try:
        info = list_video_formats_with_size(str(url))
    except Exception as e:
        raise HTTPException(400, str(e))
    return {"url": url, "info": info}


@router.post("/initiate_download")
def download_yt_video(reqData: InitiateDownload):
    video_id = uuid4().hex
    print(reqData.format_id)
    download_video(reqData.url, reqData.format_id, video_id)
    return {"video_id": video_id}


@router.get("/download/{video_id}")
def download_file_with_video_id(video_id: str):
    files = os.listdir("videos")
    for file in files:
        if file.startswith(video_id):
            return FileResponse(f"videos/{file}")
    return {"error": "File not found"}
