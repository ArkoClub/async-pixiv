# Async-Pixiv

[![Python 3.8](https://img.shields.io/badge/Python-3.8_|_3.9_|_3.10-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/release/python-370/)
[![GitHub file size in bytes](https://img.shields.io/github/languages/code-size/ArkoClub/async-pixiv?label=Size&logo=hack-the-box&logoColor=white&style=flat-square)](https://github.com/ArkoClub/async-pixiv)
[![PyPI](https://img.shields.io/pypi/v/async-pixiv?color=%233775A9&label=PyPI&logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/async-pixivr/)
[![License](https://img.shields.io/github/license/ArkoClub/async-pixiv?label=License&style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB0PSIxNjUxMjEyODQ2ODY0IiBjbGFzcz0iaWNvbiIgdmlld0JveD0iMCAwIDEwMjQgMTAyNCIgdmVyc2lvbj0iMS4xIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHAtaWQ9IjE1MDAiIHdpZHRoPSIzMDAiIGhlaWdodD0iMzAwIj48cGF0aCBkPSJNOTQ3LjIgOTIxLjZsLTg3MC40IDBjLTQyLjM0MjQgMC03Ni44LTM0LjQ1NzYtNzYuOC03Ni44bDAtNjY1LjZjMC00Mi4zNDI0IDM0LjQ1NzYtNzYuOCA3Ni44LTc2LjhsODcwLjQgMGM0Mi4zNDI0IDAgNzYuOCAzNC40NTc2IDc2LjggNzYuOGwwIDY2NS42YzAgNDIuMzQyNC0zNC40NTc2IDc2LjgtNzYuOCA3Ni44ek03Ni44IDE1My42Yy0xNC4xMzEyIDAtMjUuNiAxMS40Njg4LTI1LjYgMjUuNmwwIDY2NS42YzAgMTQuMTMxMiAxMS40Njg4IDI1LjYgMjUuNiAyNS42bDg3MC40IDBjMTQuMTMxMiAwIDI1LjYtMTEuNDY4OCAyNS42LTI1LjZsMC02NjUuNmMwLTE0LjEzMTItMTEuNDY4OC0yNS42LTI1LjYtMjUuNmwtODcwLjQgMHoiIHAtaWQ9IjE1MDEiIGZpbGw9IiNmZmZmZmYiPjwvcGF0aD48cGF0aCBkPSJNNDg2LjQgMzA3LjJsLTMwNy4yIDBjLTE0LjEzMTIgMC0yNS42LTExLjQ2ODgtMjUuNi0yNS42czExLjQ2ODgtMjUuNiAyNS42LTI1LjZsMzA3LjIgMGMxNC4xMzEyIDAgMjUuNiAxMS40Njg4IDI1LjYgMjUuNnMtMTEuNDY4OCAyNS42LTI1LjYgMjUuNnoiIHAtaWQ9IjE1MDIiIGZpbGw9IiNmZmZmZmYiPjwvcGF0aD48cGF0aCBkPSJNNDg2LjQgNDYwLjhsLTMwNy4yIDBjLTE0LjEzMTIgMC0yNS42LTExLjQ2ODgtMjUuNi0yNS42czExLjQ2ODgtMjUuNiAyNS42LTI1LjZsMzA3LjIgMGMxNC4xMzEyIDAgMjUuNiAxMS40Njg4IDI1LjYgMjUuNnMtMTEuNDY4OCAyNS42LTI1LjYgMjUuNnoiIHAtaWQ9IjE1MDMiIGZpbGw9IiNmZmZmZmYiPjwvcGF0aD48cGF0aCBkPSJNNDg2LjQgNTYzLjJsLTMwNy4yIDBjLTE0LjEzMTIgMC0yNS42LTExLjQ2ODgtMjUuNi0yNS42czExLjQ2ODgtMjUuNiAyNS42LTI1LjZsMzA3LjIgMGMxNC4xMzEyIDAgMjUuNiAxMS40Njg4IDI1LjYgMjUuNnMtMTEuNDY4OCAyNS42LTI1LjYgMjUuNnoiIHAtaWQ9IjE1MDQiIGZpbGw9IiNmZmZmZmYiPjwvcGF0aD48cGF0aCBkPSJNNDg2LjQgNjY1LjZsLTMwNy4yIDBjLTE0LjEzMTIgMC0yNS42LTExLjQ2ODgtMjUuNi0yNS42czExLjQ2ODgtMjUuNiAyNS42LTI1LjZsMzA3LjIgMGMxNC4xMzEyIDAgMjUuNiAxMS40Njg4IDI1LjYgMjUuNnMtMTEuNDY4OCAyNS42LTI1LjYgMjUuNnoiIHAtaWQ9IjE1MDUiIGZpbGw9IiNmZmZmZmYiPjwvcGF0aD48cGF0aCBkPSJNNDM1LjIgNzY4bC0yNTYgMGMtMTQuMTMxMiAwLTI1LjYtMTEuNDY4OC0yNS42LTI1LjZzMTEuNDY4OC0yNS42IDI1LjYtMjUuNmwyNTYgMGMxNC4xMzEyIDAgMjUuNiAxMS40Njg4IDI1LjYgMjUuNnMtMTEuNDY4OCAyNS42LTI1LjYgMjUuNnoiIHAtaWQ9IjE1MDYiIGZpbGw9IiNmZmZmZmYiPjwvcGF0aD48cGF0aCBkPSJNOTE4LjY4MTYgMzM1LjA1MjhsLTQxLjYyNTYtMzAuMjU5Mi0xNS45MjMyLTQ4Ljk0NzItNTEuNDU2IDAtNDEuNjI1Ni0zMC4yNTkyLTQxLjYyNTYgMzAuMjU5Mi01MS40NTYgMC0xNS45MjMyIDQ4Ljk0NzItNDEuNjI1NiAzMC4yNTkyIDE1LjkyMzIgNDguOTQ3Mi0xNS45MjMyIDQ4Ljk0NzIgNDEuNjI1NiAzMC4yNTkyIDYuNzU4NCAyMC43ODcyYy0wLjEwMjQgMC44MTkyLTAuMTAyNCAxLjU4NzItMC4xMDI0IDIuNDA2NGwwIDI1NmMwIDEwLjM0MjQgNi4yNDY0IDE5LjcxMiAxNS44MjA4IDIzLjY1NDRzMjAuNTgyNCAxLjc5MiAyNy45MDQtNS41Mjk2bDU4LjY3NTItNTguNjc1MiA1OC42NzUyIDU4LjY3NTJjNC45MTUyIDQuOTE1MiAxMS40MTc2IDcuNTI2NCAxOC4xMjQ4IDcuNDc1MiAzLjI3NjggMCA2LjYwNDgtMC42MTQ0IDkuNzc5Mi0xLjk0NTYgOS41NzQ0LTMuOTQyNCAxNS44MjA4LTEzLjMxMiAxNS44MjA4LTIzLjY1NDRsMC0yNTZjMC0wLjgxOTItMC4wNTEyLTEuNjM4NC0wLjEwMjQtMi40MDY0bDYuNzU4NC0yMC43ODcyIDQxLjYyNTYtMzAuMjU5Mi0xNS45MjMyLTQ4Ljk0NzIgMTUuOTIzMi00OC45NDcyek02NzcuNTI5NiAzNTQuNjExMmwyNC45ODU2LTE4LjE3NiA5LjU3NDQtMjkuMzg4OCAzMC45MjQ4IDAgMjQuOTg1Ni0xOC4xNzYgMjQuOTg1NiAxOC4xNzYgMzAuOTI0OCAwIDkuNTc0NCAyOS4zODg4IDI0Ljk4NTYgMTguMTc2LTkuNTc0NCAyOS4zODg4IDkuNTc0NCAyOS4zODg4LTI0Ljk4NTYgMTguMTc2LTkuNTc0NCAyOS4zODg4LTMwLjkyNDggMC0yNC45ODU2IDE4LjE3Ni0yNC45ODU2LTE4LjE3Ni0zMC45MjQ4IDAtOS41NzQ0LTI5LjM4ODgtMjQuOTg1Ni0xOC4xNzYgOS41NzQ0LTI5LjM4ODgtOS41NzQ0LTI5LjM4ODh6TTc4Ni4xMjQ4IDY0Ny40NzUyYy05Ljk4NC05Ljk4NC0yNi4yMTQ0LTkuOTg0LTM2LjE5ODQgMGwtMzMuMDc1MiAzMy4wNzUyIDAtMTY4LjQ0OCA5LjU3NDQgMCA0MS42MjU2IDMwLjI1OTIgNDEuNjI1Ni0zMC4yNTkyIDkuNTc0NCAwIDAgMTY4LjQ0OC0zMy4wNzUyLTMzLjA3NTJ6IiBwLWlkPSIxNTA3IiBmaWxsPSIjZmZmZmZmIj48L3BhdGg+PC9zdmc+)](./LICENSE)

[![PyPI - Downloads](https://img.shields.io/pypi/dm/async-pixiv?color=91A4ED&label=Downloads&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB0PSIxNjUyMjYwMDAwMjU3IiBjbGFzcz0iaWNvbiIgdmlld0JveD0iMCAwIDEwMjQgMTAyNCIgdmVyc2lvbj0iMS4xIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHAtaWQ9IjUxNjIiIHdpZHRoPSI1MDAiIGhlaWdodD0iNTAwIj48cGF0aCBkPSJNOTU3LjU0MzkzNyA5NjEuMTMxMTM3IDYyLjg2NTI4MSA5NjEuMTMxMTM3IDYyLjg2NTI4MSA2NTUuNTA5NDg1IDE4OC4yOTgwNjIgNjU1LjUwOTQ4NSAxODguMjk4MDYyIDg1OS4yNDI1ODYgODMyLjE2MDI3NSA4NTkuMjQyNTg2IDgzMi4xNjAyNzUgNjU1LjUwOTQ4NSA5NTcuNTQzOTM3IDY1NS41MDk0ODVaIiBwLWlkPSI1MTYzIiBmaWxsPSIjZmZmZmZmIj48L3BhdGg%2BPHBhdGggZD0iTTc1My4yNzg3MTcgMzYzLjI3ODgxNyA1MTAuMTgwMDUgNzkwLjc0MTQ0NSAyNjcuMDMzMjg3IDM2My4yNzg4MTdaIiBwLWlkPSI1MTY0IiBmaWxsPSIjZmZmZmZmIj48L3BhdGg%2BPHBhdGggZD0iTTQzNC44OTEzMiA2NC4zNTY3NWwxNTAuNTI4MzQyIDAgMCAzMDAuMjU5NTI4LTE1MC41MjgzNDIgMCAwLTMwMC4yNTk1MjhaIiBwLWlkPSI1MTY1IiBmaWxsPSIjZmZmZmZmIj48L3BhdGg%2BPC9zdmc%2B&style=flat-square)](https://pypi.org/project/async-pixiv/)
[![View](https://hits.sh/github.com/ArkoClub/async-pixiv.svg?color=7AA3CC&style=flat-square&label=View&logo=data:image/svg+xml;base64,PHN2ZyB0PSIxNjUyMjU5MTQ0MjAzIiBjbGFzcz0iaWNvbiIgdmlld0JveD0iMCAwIDEwMjQgMTAyNCIgdmVyc2lvbj0iMS4xIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHAtaWQ9IjM0NjkiIHdpZHRoPSIzMDAiIGhlaWdodD0iMzAwIj48cGF0aCBkPSJNNTEyIDQxNmE5NiA5NiAwIDEgMCAwIDE5MiA5NiA5NiAwIDAgMCAwLTE5MnogbTUxMS45NTIgMTAyLjA2NGMtMC4wMTYtMC40NDgtMC4wNjQtMC44NjQtMC4wOTYtMS4yOTZhOC4xNiA4LjE2IDAgMCAwLTAuMDgtMC42NTZjMC0wLjMyLTAuMDY0LTAuNjI0LTAuMTI4LTAuOTI4LTAuMDMyLTAuMzY4LTAuMDY0LTAuNzM2LTAuMTI4LTEuMDg4LTAuMDMyLTAuMDQ4LTAuMDMyLTAuMDk2LTAuMDMyLTAuMTQ0YTM5LjQ4OCAzOS40ODggMCAwIDAtMTAuNzA0LTIxLjUzNmMtMzIuNjcyLTM5LjYxNi03MS41MzYtNzQuODgtMTExLjA0LTEwNy4wNzItODUuMDg4LTY5LjM5Mi0xODIuNDMyLTEyNy40MjQtMjg5Ljg1Ni0xNTAuOC02Mi4xMTItMTMuNTA0LTEyNC41NzYtMTQuMDY0LTE4Ny4wMDgtMi42NC01Ni43ODQgMTAuMzg0LTExMS41MDQgMzItMTYyLjcyIDU4Ljc4NC04MC4xNzYgNDEuOTItMTUzLjM5MiA5OS42OTYtMjE3LjE4NCAxNjQuNDgtMTEuODA4IDExLjk4NC0yMy41NTIgMjQuMjI0LTM0LjI4OCAzNy4yNDgtMTQuMjg4IDE3LjMyOC0xNC4yODggMzcuODcyIDAgNTUuMjE2IDMyLjY3MiAzOS42MTYgNzEuNTIgNzQuODQ4IDExMS4wNCAxMDcuMDU2IDg1LjEyIDY5LjM5MiAxODIuNDQ4IDEyNy40MDggMjg5Ljg4OCAxNTAuNzg0IDYyLjA5NiAxMy41MDQgMTI0LjYwOCAxNC4wOTYgMTg3LjAwOCAyLjY1NiA1Ni43NjgtMTAuNCAxMTEuNDg4LTMyIDE2Mi43MzYtNTguNzY4IDgwLjE3Ni00MS45MzYgMTUzLjM3Ni05OS42OTYgMjE3LjE4NC0xNjQuNDggMTEuNzkyLTEyIDIzLjUzNi0yNC4yMjQgMzQuMjg4LTM3LjI0OCA1LjcxMi01Ljg3MiA5LjQ1Ni0xMy40NCAxMC43MDQtMjEuNTY4bDAuMDMyLTAuMTI4YTEyLjU5MiAxMi41OTIgMCAwIDAgMC4xMjgtMS4wODhjMC4wNjQtMC4zMDQgMC4wOTYtMC42MjQgMC4xMjgtMC45MjhsMC4wOC0wLjY1NiAwLjA5Ni0xLjI4YzAuMDMyLTAuNjU2IDAuMDQ4LTEuMjk2IDAuMDQ4LTEuOTUybC0wLjA5Ni0xLjk2OHpNNTEyIDcwNGMtMTA2LjAzMiAwLTE5Mi04NS45NTItMTkyLTE5MnM4NS45NTItMTkyIDE5Mi0xOTIgMTkyIDg1Ljk2OCAxOTIgMTkyYzAgMTA2LjA0OC04NS45NjggMTkyLTE5MiAxOTJ6IiBwLWlkPSIzNDcwIiBmaWxsPSIjZmZmZmZmIj48L3BhdGg+PC9zdmc+)](https://hits.sh/github.com/ArkoClub/async-pixiv)

异步调用 Pixiv API

# Building...
此项目的开发者很忙，所以没啥时间修 bug ，写文档什么的

### 特点
1. 支持 API 请求速率限制（[RateLimiter](https://aiolimiter.readthedocs.io/en/latest/)）
2. 可使用账号和密码直接登录 Pixiv（注：可能会因为遇到 Cloudflare 验证而登录失败）
3. 自动将请求后的数据转为 Model ，再也不用以字典形式调用获取数据了（pydantic typed）
4. 支持多种代理模式（http/https/socks5）
5. 支持下载 gif 帧序列文件，并将其转为 gif 或 mp4 （需要 [ffmpeg](https://ffmpeg.org)） 
6. 。。。（想到再写）

## 安装

使用 `pip` (任选一行指令进行安装)

```bash
pip install --upgrade async-pixiv

# 安装额外依赖（用于提升数据解析速度）
pip install --upgrade async-pixiv[extra]

# 安装 playwright，使之可以使用账号密码登录 
pip install --upgrade async-pixiv[playwright]

# 安装全部额外依赖
pip install --upgrade async-pixiv[full]
```

使用 `poetry`

```bash
poetry add async-pixiv

# 安装额外依赖（用于提升数据解析速度）
poetry add async-pixiv[extra]

# 安装 playwright，使之可以使用账号密码登录 
poetry add async-pixiv[playwright]

# 安装全部额外依赖
poetry add async-pixiv[full]
```

## 使用

```python
from async_pixiv import PixivClient  # 导入

# 初始化 Client
client = PixivClient(
    max_rate=100,  # API 请求速率限制。默认 100 次
    rate_time_period=60,  # API 请求速率限制时间区间。默认 60 秒
    timeout=10,  # 默认超时秒数
    proxies=None,  # 代理配置
    trust_env=False,  # 是否从环境变量中获取代理配置
    retry=5,  # 默认请求重试次数
    retry_sleep=1,  # 默认重复请求间隔秒数
)


async def main():
    user = await client.login_with_token('TOKEN')  # 使用 token 登录 pixiv
    print(user.name)

    # 获取作品详情
    detail_result = await client.ILLUST.detail(91725675)
    illust = detail_result.illust
    print(
        f"链接：{illust.link}", 
        f"标题：{illust.title}", 
        f"作者：{illust.user.name}", 
        f"标签：#{' #'.join(map(str, illust.tags))}", 
        f"是否为 AI 作品：{'是' if illust.ai_type else '否'}",
        f"是否为 R18 作品：{'是' if await illust.is_r18() else '否'}",
        sep='\n'
    )
    file_data = illust.download() # 下载
    breakpoint()

    # 下载动图
    bytes_data = await client.ILLUST.download_ugoira(105369892, type='mp4')  # bytes
    gif_data = await client.ILLUST.download_ugoira(105369892, type='gif')
    breakpoint()

    # 小说
    novel_result = await client.NOVEL.detail(15739859)
    novel = novel_result.novel
    print(f"标题：{novel.title}", f"字数：{novel.text_length}", sep='\n')
    breakpoint()
    
    # 漫画
    # 下次再写

def __main__():
    import asyncio

    asyncio.run(main())


if __name__ == '__main__':
    __main__()

```
