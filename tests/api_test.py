import asyncio
import logging
import os
from datetime import datetime, timedelta

import pytest

from async_pixiv import PixivClient
from async_pixiv.utils.enums import SearchDuration, SearchShort

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
    return PixivClient(max_rate=50)


@pytest.mark.asyncio
class TestLogin:
    async def test_login_with_password(self, client: PixivClient):
        account = await client.login_with_pwd(
            PIXIV_USERNAME,
            PIXIV_PASSWORD,
            PIXIV_SECRET,
            proxy=os.environ.get("HTTP_PROXY"),
        )
        assert account.name == "Karako"
        logger.info(f"password login with {account.name}")

    async def test_login_with_token(self, client: PixivClient):
        account = await client.login_with_token(PIXIV_TOKEN)
        assert account.name
        logger.info(f"token login with {account.name}")


@pytest.mark.asyncio
class TestIllustAPI:
    @staticmethod
    async def login(client: PixivClient):
        await client.login_with_token(PIXIV_TOKEN)

    async def test_search(self, client: PixivClient):
        await self.login(client)

        section = client.ILLUST

        search_result = await section.search(
            "原神", sort=SearchShort.DateIncrements, duration=SearchDuration.week
        )
        assert len(search_result.illusts) == 30
        assert (
            search_result.illusts[0].create_date.astimezone() + timedelta(days=8)
            >= datetime.now().astimezone()
        )

        async for illust in search_result.iter_all_pages():
            for _ in range(50):
                assert illust
                logger.info(illust.id, illust.title)

        breakpoint()
