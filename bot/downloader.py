"""Video downloader with size checks using yt-dlp."""

import asyncio
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Optional

import yt_dlp

from bot.config import (
    ESTIMATED_BITRATE,
    MAX_FILESIZE_BYTES,
    PRE_CHECK_LIMIT_BYTES,
)

logger = logging.getLogger(__name__)


class VideoTooLargeError(Exception):
    """Video exceeds Telegram bot size limit."""


class VideoDownloadError(Exception):
    """Generic download error."""


async def check_video_size(url: str) -> None:
    """
    Pre-check video size without downloading.
    Raises VideoTooLargeError if video is too large.
    """

    def _extract_info() -> dict:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)

    try:
        info = await asyncio.to_thread(_extract_info)
    except yt_dlp.utils.DownloadError as e:
        error_str = str(e)
        logger.warning(f"Failed to extract video info: {error_str}")

        # User-friendly error messages
        if "404" in error_str or "not found" in error_str.lower():
            raise VideoDownloadError("Видео не найдено или удалено")
        elif "private" in error_str.lower() or "login" in error_str.lower():
            raise VideoDownloadError("Видео приватное — требуется авторизация")
        elif "geo" in error_str.lower() or "not available in your country" in error_str.lower():
            raise VideoDownloadError("Видео недоступно в вашем регионе")
        elif "unsupported url" in error_str.lower():
            raise VideoDownloadError("Неподдерживаемая ссылка")
        else:
            raise VideoDownloadError(f"Не удалось получить информацию о видео")

    except Exception as e:
        logger.error(f"Unexpected error extracting video info: {e}")
        raise VideoDownloadError("Не удалось получить информацию о видео")

    formats = info.get("formats", [])
    if not formats:
        raise VideoDownloadError("Видео не содержит доступных форматов")

    # Find best format with known size <= 45 MB
    suitable_found = False
    for fmt in formats:
        filesize = fmt.get("filesize") or fmt.get("filesize_approx")

        if filesize and filesize <= PRE_CHECK_LIMIT_BYTES:
            suitable_found = True
            break

        # If size unknown, estimate from duration
        if not filesize and fmt.get("duration"):
            estimated_size = int(fmt["duration"] * ESTIMATED_BITRATE)
            if estimated_size <= PRE_CHECK_LIMIT_BYTES:
                suitable_found = True
                break

    if not suitable_found:
        logger.warning(f"No suitable format found for {url}, all exceed {PRE_CHECK_LIMIT_BYTES}")
        raise VideoTooLargeError(
            "Видео больше 50 МБ — Telegram не позволяет отправить его ботом"
        )


async def download_video(url: str) -> Path:
    """
    Download video to temporary directory.
    Returns path to downloaded file.
    Raises VideoTooLargeError if size check fails.
    Raises VideoDownloadError on other errors.
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix="bot_video_"))

    def _download() -> Path:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            # More flexible format selector - fallback chain for better compatibility
            "format": (
                "bv*[ext=mp4][height<=720]+ba[ext=m4a]/b[ext=mp4][height<=720]/"
                "bv*[height<=720]+ba/b[height<=720]/"
                "bv*+ba/b"
            ),
            "outtmpl": str(tmp_dir / "video.%(ext)s"),
            "max_filesize": MAX_FILESIZE_BYTES,
            "merge_output_format": "mp4",
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Find downloaded file
        video_files = list(tmp_dir.glob("video.*"))
        if not video_files:
            raise VideoDownloadError("Файл не был скачан")

        return video_files[0]

    try:
        video_path = await asyncio.to_thread(_download)

        # Final size check on disk
        file_size = video_path.stat().st_size
        if file_size > MAX_FILESIZE_BYTES:
            logger.warning(f"Downloaded file {file_size} bytes exceeds limit {MAX_FILESIZE_BYTES}")
            raise VideoTooLargeError(
                "Видео больше 50 МБ — Telegram не позволяет отправить его ботом"
            )

        logger.info(f"Downloaded video: {video_path} ({file_size / 1024 / 1024:.1f} MB)")
        return video_path

    except yt_dlp.utils.DownloadError as e:
        error_str = str(e)
        logger.warning(f"yt-dlp download error for {url}: {error_str}")

        # Parse error and provide user-friendly message
        if "too large" in error_str.lower() or "max_filesize" in error_str.lower():
            raise VideoTooLargeError(
                "Видео больше 50 МБ — Telegram не позволяет отправить его ботом"
            )
        elif "404" in error_str or "not found" in error_str.lower():
            raise VideoDownloadError("Видео не найдено или удалено")
        elif "private" in error_str.lower() or "login" in error_str.lower():
            raise VideoDownloadError("Видео приватное — требуется авторизация")
        elif "requested format" in error_str.lower() and "not available" in error_str.lower():
            raise VideoDownloadError("Не удалось найти подходящий формат видео")
        elif "geo" in error_str.lower() or "not available in your country" in error_str.lower():
            raise VideoDownloadError("Видео недоступно в вашем регионе")
        else:
            raise VideoDownloadError("Не удалось скачать видео")

    except Exception as e:
        logger.error(f"Unexpected download error for {url}: {e}")
        raise VideoDownloadError(f"Не удалось скачать видео: {e}")

    finally:
        # Cleanup is handled in handler with shutil.rmtree
        pass


def cleanup_temp_dir(tmp_dir: Path) -> None:
    """Remove temporary directory."""
    try:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        logger.debug(f"Cleaned up {tmp_dir}")
    except Exception as e:
        logger.warning(f"Failed to cleanup {tmp_dir}: {e}")
