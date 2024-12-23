import asyncio
import logging
import os
from datetime import datetime, timedelta

import pytest

from async_pixiv import PixivClient
from async_pixiv.model import SearchDuration, SearchShort

PIXIV_USERNAME = os.environ.get("PIXIV_USERNAME")
PIXIV_PASSWORD = os.environ.get("PIXIV_PASSWORD")
PIXIV_SECRET = os.environ.get("PIXIV_SECRET")
PIXIV_TOKEN = os.environ.get("PIXIV_TOKEN")

logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)
logger.setLevel(logging.NOTSET)


@pytest.fixture(scope="session")
def event_loop():
    try:
        # noinspection PyUnresolvedReferences
        import uvloop

        loop = uvloop.new_event_loop()
    except ImportError:
        loop = asyncio.get_event_loop()

    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def client():
    return PixivClient()


@pytest.mark.asyncio
class TestLogin:
    async def test_login_with_token(self, client: PixivClient):
        account = await client.login_with_token(PIXIV_TOKEN)
        assert account.name
        logger.info(f"token login with {account.name}")


@pytest.mark.asyncio
class TestIllustAPI:
    @staticmethod
    async def login(client: PixivClient):
        await client.login_with_token(PIXIV_TOKEN)

    async def test_search_illust(self, client: PixivClient):
        await self.login(client)

        result = await client.ILLUST.search(
            "初音ミク", sort=SearchShort.DateIncrements, duration=SearchDuration.week
        )
        assert len(result.previews) == 30
        assert (
            result.previews[0].create_date.astimezone() + timedelta(days=8)
            >= datetime.now().astimezone()
        )

        num = 0
        async for illust in result.iter_all_pages():
            if num < 50:
                logger.info(illust.id, illust.title)
            else:
                break
