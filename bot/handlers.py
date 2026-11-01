"""Inline query handlers."""

import asyncio
import logging
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.types import (
    FSInputFile,
    InlineQuery,
    InlineQueryResultArticle,
    InlineQueryResultCachedVideo,
    InputTextMessageContent,
)

from bot.cache import FileCache
from bot.config import ARCHIVE_CHAT_ID, CACHE_TTL, INLINE_TIMEOUT
from bot.downloader import (
    VideoDownloadError,
    VideoTooLargeError,
    check_video_size,
    cleanup_temp_dir,
    download_video,
)
from bot.urls import extract_url, get_platform_name, normalize_url

logger = logging.getLogger(__name__)

router = Router()
file_cache = FileCache(ttl=CACHE_TTL)


def create_error_result(error_message: str) -> list[InlineQueryResultArticle]:
    """Create inline result with error message."""
    return [
        InlineQueryResultArticle(
            id="error",
            title="Ошибка",
            description=error_message,
            input_message_content=InputTextMessageContent(message_text=error_message),
        )
    ]


@router.inline_query(F.query)
async def handle_inline_query(query: InlineQuery, bot: Bot) -> None:
    """Handle inline query with video URL."""
    query_text = query.query.strip()
    logger.info(f"Inline query from {query.from_user.id}: {query_text[:50]}...")

    # Extract URL
    url = extract_url(query_text)
    if not url:
        logger.debug("No supported URL found in query")
        await query.answer(results=[], cache_time=60, is_personal=True)
        return

    normalized_url = normalize_url(url)
    platform_name = get_platform_name(url)
    logger.info(f"Processing {platform_name} URL: {normalized_url}")

    # Check cache
    cached_file_id = file_cache.get(normalized_url)
    if cached_file_id:
        logger.info(f"Cache hit for {normalized_url}")
        results = [
            InlineQueryResultCachedVideo(
                id="cached",
                video_file_id=cached_file_id,
                title=f"Видео с {platform_name}",
                description=f"Из кэша: {url}",
            )
        ]
        await query.answer(results=results, cache_time=300, is_personal=True)
        return

    # Download and upload video
    try:
        results = await asyncio.wait_for(
            _process_video(bot, url, normalized_url, platform_name), timeout=INLINE_TIMEOUT
        )
        await query.answer(results=results, cache_time=300, is_personal=True)

    except asyncio.TimeoutError:
        logger.warning(f"Timeout processing {normalized_url}")
        await query.answer(
            results=create_error_result("Время ожидания истекло, попробуйте ещё раз"),
            cache_time=30,
            is_personal=True,
        )

    except Exception as e:
        logger.error(f"Unexpected error processing {normalized_url}: {e}", exc_info=True)
        await query.answer(
            results=create_error_result("Произошла ошибка при обработке видео"),
            cache_time=30,
            is_personal=True,
        )


async def _process_video(
    bot: Bot, url: str, normalized_url: str, platform_name: str
) -> list[InlineQueryResultCachedVideo | InlineQueryResultArticle]:
    """Download video, upload to archive, cache file_id, return result."""
    tmp_dir: Path | None = None

    try:
        # Pre-check size
        await check_video_size(url)

        # Download
        video_path = await download_video(url)
        tmp_dir = video_path.parent

        # Upload to archive chat
        logger.info(f"Uploading {video_path.name} to archive chat {ARCHIVE_CHAT_ID}")
        video_file = FSInputFile(video_path)
        message = await bot.send_video(
            chat_id=ARCHIVE_CHAT_ID,
            video=video_file,
            caption=f"{platform_name}\n{url}",
        )

        file_id = message.video.file_id
        logger.info(f"Video uploaded, file_id: {file_id}")

        # Cache file_id
        file_cache.set(normalized_url, file_id)

        return [
            InlineQueryResultCachedVideo(
                id="new",
                video_file_id=file_id,
                title=f"Видео с {platform_name}",
                description=url,
            )
        ]

    except VideoTooLargeError as e:
        logger.warning(f"Video too large: {url}")
        return create_error_result(str(e))

    except VideoDownloadError as e:
        logger.warning(f"Download error for {url}: {e}")
        return create_error_result(str(e))

    finally:
        if tmp_dir:
            cleanup_temp_dir(tmp_dir)
