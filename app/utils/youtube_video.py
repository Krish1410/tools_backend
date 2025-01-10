import os
import uuid
import yt_dlp
from fastapi import HTTPException
from moviepy.editor import VideoFileClip, AudioFileClip

cookies_path = "/home/sgma/tools_backend/cookies.txt"  # Path to the cookies file


def list_video_formats_with_size(url: str):
    ydl_opts = {
        "listformats": True,  # This option lists all available formats
    }
    res = {"formats": {"audio": [], "video": []}}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        formats = info_dict.get("formats", [])

        res["title"] = info_dict.get("title")
        res["thumbnail"] = info_dict.get("thumbnail")
        audio_id = []
        audio_file_size = []
        for f in formats:
            # Retrieve file size if available
            file_size = f.get("filesize") or f.get("filesize_approx")
            # print(f)
            if file_size:
                format_id = f["format_id"]
                if f.get("resolution") == "audio only":
                    audio_id.append(format_id)
                    audio_file_size.append(file_size)
                    print("audio_id", audio_id)
                    res["formats"]["audio"].append(
                        {
                            "format_id": format_id,
                            "ext": f["ext"],
                            "audio_ext": f["audio_ext"],
                            "resolution": f.get("resolution"),
                            "size": (file_size / (1024 * 1024)),  # Convert bytes to MB
                            "note": f.get("format_note"),
                        }
                    )
                    continue
                if f.get("audio_ext", "none") == "none":
                    format_id = str(format_id) + "+" + str(audio_id[0])
                    file_size = audio_file_size[0] + file_size
                    if len(audio_id) > 1:
                        audio_id.pop(0)
                        audio_file_size.pop(0)

                res["formats"]["video"].append(
                    {
                        "format_id": format_id,
                        "ext": f["ext"],
                        "audio_ext": f["audio_ext"],
                        "resolution": f.get("resolution"),
                        "size": (file_size / (1024 * 1024)),  # Convert bytes to MB
                        "note": f.get("format_note"),
                    }
                )

        return res


def combine_audio_and_video(video_path, audio_path, output_path):

    video_clip = VideoFileClip(video_path)

    audio_clip = AudioFileClip(audio_path)

    video_clip = video_clip.set_audio(audio_clip)

    video_clip.write_videofile(f"{output_path}", codec="libx264", audio_codec="aac")


def download_video_audio_separately(url, video_format, audio_format, output_name):
    video_path = f"videos/{output_name}/video_%(title)s.%(ext)s"
    audio_path = f"videos/{output_name}/audio_%(title)s.%(ext)s"

    # Download video
    ydl_opts_video = {
        "format": video_format,
        "outtmpl": video_path,
    }
    with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
        try:
            dw = ydl.download([url])
            print("Download", dw)
        except yt_dlp.utils.DownloadError as e:
            raise HTTPException(400, f"Download error (video): {str(e)}")

    # Download audio
    ydl_opts_audio = {
        "format": audio_format,
        "outtmpl": audio_path,
    }
    with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
        try:
            ydl.download([url])
        except yt_dlp.utils.DownloadError as e:
            raise HTTPException(400, f"Download error (audio): {str(e)}")

    files = os.listdir(f"videos/{output_name}")
    # Merge video and audio using ffmpeg
    ext = ""
    video_file = ""
    audio_file = ""
    for file in files:
        if "video_" in file:
            ext = file.split(".")[-1]
            video_file = file
        if "audio_" in file:
            audio_file = file
    combine_audio_and_video(
        f"videos/{output_name}/{video_file}",
        f"videos/{output_name}/{audio_file}",
        f"videos/{output_name}.{ext}",
    ),
    # ffmpeg_command = [
    #     "ffmpeg",
    #     "-i",
    #     f"videos/{output_name}/{files[0]}",
    #     "-i",
    #     f"videos/{output_name}/{files[1]}",
    #     "-c:v",
    #     "copy",
    #     "-c:a",
    #     "copy",
    #     f"videos/{output_name}/{output_name}.{ext}",
    # ]
    # try:
    #     subprocess.run(ffmpeg_command, check=True)
    # except subprocess.CalledProcessError as e:
    #     raise HTTPException(400, f"FFmpeg merge error: {str(e)}")

    return


def download_video(url, format_id, video_id):
    ydl_opts = {
        "format": format_id,
        "outtmpl": "videos/" + video_id + "_%(title)s.%(ext)s",
        "cookies": cookies_path,  # Specify the path to the cookies file
        # Output file template
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
        except yt_dlp.utils.DownloadError:
            raise HTTPException(400, "Invalid URL")


if __name__ == "__main__":

    video_url = "https://youtu.be/9QpmsrYO4cc?si=HIPy7KRdGNobyAtC"
    # list_video_formats_with_size(video_url)394+140
    download_video_audio_separately(video_url, "394", "140", uuid.uuid4().hex)
    download_video(video_url, "140", uuid.uuid4().hex)
