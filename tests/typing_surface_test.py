import inspect
from pathlib import Path
from typing import get_type_hints

import pytest
from yarl import URL

from async_pixiv.client._client import PixivClient
from async_pixiv.client.api import APIBase, IllustAPI, NovelAPI, UserAPI
from async_pixiv.client.api._illust import IllustDetail, IllustPageResult
from async_pixiv.client.api._novel import NovelDetail, NovelPageResult
from async_pixiv.client.api._user import UserDetail, UserPageResult
from async_pixiv.model.novel import NovelText
from async_pixiv.model.user import Account

ROOT = Path(__file__).resolve().parents[1]


def test_runtime_type_hints_cover_public_client_surface():
    hints = get_type_hints(PixivClient)
    assert hints["USER"] is UserAPI
    assert hints["ILLUST"] is IllustAPI
    assert hints["NOVEL"] is NovelAPI
    assert get_type_hints(PixivClient.login_with_token)["return"] is Account
    assert get_type_hints(IllustAPI.search)["return"] is IllustPageResult
    assert get_type_hints(NovelAPI.text)["return"] is NovelText


def test_runtime_type_hints_cover_inherited_public_api_methods():
    assert get_type_hints(IllustAPI.__call__)["return"] is IllustDetail
    assert get_type_hints(IllustAPI.detail)["return"] is IllustDetail
    assert get_type_hints(IllustAPI.recommended)["return"] is IllustPageResult

    assert get_type_hints(NovelAPI.__call__)["return"] is NovelDetail
    assert get_type_hints(NovelAPI.detail)["return"] is NovelDetail
    assert get_type_hints(NovelAPI.recommended)["return"] is NovelPageResult

    assert get_type_hints(UserAPI.__call__)["return"] is UserDetail
    assert get_type_hints(UserAPI.detail)["return"] is UserDetail
    assert get_type_hints(UserAPI.search)["return"] is UserPageResult
    assert get_type_hints(UserAPI.recommended)["return"] is UserPageResult


def test_apibase_runtime_signature_requires_client():
    parameter = inspect.signature(APIBase.__init__).parameters["client"]
    assert parameter.default is inspect.Signature.empty


async def test_illust_search_invalid_end_date_raises_expected_type_error():
    api = IllustAPI(object())

    with pytest.raises(TypeError, match=r"end_date must be a datetime\.date or None"):
        await api.search("miku", end_date="2024-01-01")


def test_api_stub_files_are_removed_and_client_stub_is_thin():
    api_stub_paths = [
        ROOT / "src/async_pixiv/client/api/_abc.pyi",
        ROOT / "src/async_pixiv/client/api/_illust.pyi",
        ROOT / "src/async_pixiv/client/api/_novel.pyi",
        ROOT / "src/async_pixiv/client/api/_user.pyi",
    ]
    assert not any(path.exists() for path in api_stub_paths)

    assert (ROOT / "src/async_pixiv/py.typed").exists()

    client_stub = ROOT / "src/async_pixiv/client/_client.pyi"
    text = client_stub.read_text(encoding="utf-8")
    assert "_client_token" not in text
    assert "_timezone_token" not in text
    assert "access_token: str | None" in text
    assert "refresh_token: str | None" in text
    assert "def is_closed(self) -> bool" in text
    assert "url: URLTypes | URL" in text
    assert "params: QueryParamTypes | None = None" in text
    assert "headers: HeaderTypes | None = None" in text
    assert ") -> Response: ..." in text
    assert "method: typing.Literal[" in text
    assert '"GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"' in text
    assert "output: StrPath | BytesIO | str | None = None" in text
    assert "progress_handler: ProgressHandler | None = None" in text
    assert "limiter: RateLimiter | None = None" in text
    assert "proxy: ProxyTypes | None = None" in text
    assert "timeout: TimeoutTypes = None" in text
    assert "*args: Any" not in text


def test_urltype_is_plain_url_type_without_magic_patch_dependency():
    typedefs = ROOT / "src/async_pixiv/typedefs.py"
    text = typedefs.read_text(encoding="utf-8")

    assert "from async_pixiv.utils.magic import curses" not in text
    assert "@curses(_URL)" not in text
    assert "if TYPE_CHECKING:" in text
    assert "UrlType = _URL" in text
    assert "class UrlType:" in text
    assert not hasattr(URL("https://example.com"), "download")
