import asyncio
import os
import sys
import traceback

import aiohttp
import cachetools
from aiohttp import web
from gidgethub import aiohttp as gh_aiohttp
from gidgethub import routing, sansio

from . import check_runs, installations

router = routing.Router(installations.router, check_runs.router)

lru_cache = cachetools.LRUCache(maxsize=500)  # type: cachetools.LRUCache
# Timed cache for installation access token (1 hour)
ttl_cache = cachetools.TTLCache(maxsize=500, ttl=3600)  # type: cachetools.TTLCache


async def main(request: web.Request):
    try:
        body = await request.read()
        secret = os.environ.get("GITHUB_SECRET")
        event = sansio.Event.from_http(request.headers, body, secret=secret)
        if event.event == "ping":
            return web.Response(status=200)
        async with aiohttp.ClientSession() as session:
            gh = gh_aiohttp.GitHubAPI(session, "TheAlgorithms/Python", cache=lru_cache)
            # Give GitHub some time to reach internal consistency.
            await asyncio.sleep(1)
            await router.dispatch(event, gh, ttl_cache)
        try:
            print(
                f"GH requests remaining: {gh.rate_limit.remaining}\n"
                f"Reset time: {gh.rate_limit.reset_datetime:%b-%d-%Y %H:%M:%S %Z}\n"
                f"GH delivery ID: {event.delivery_id}\n"
            )
        except AttributeError:
            pass
        return web.Response(status=200)
    except Exception:
        traceback.print_exc(file=sys.stderr)
        return web.Response(status=500)


if __name__ == "__main__":  # pragma: no cover
    app = web.Application()
    app.router.add_post("/", main)
    port = os.environ.get("PORT")
    if port is not None:
        port = int(port)  # type: ignore
    web.run_app(app, port=port)
