"""GitHubAPI class for making request and logging the request-response cycle."""

from typing import Mapping, Tuple

from gidgethub.abc import UTF_8_CHARSET
from gidgethub.aiohttp import GitHubAPI as BaseGitHubAPI

from .log import STATUS_OK, inject_status_color, logger

TOKEN_ENDPOINT = "access_tokens"


class GitHubAPI(BaseGitHubAPI):

    LOG_FORMAT = 'api "%(method)s %(path)s %(data)s %(version)s" => %(status)s'

    async def _request(
        self, method: str, url: str, headers: Mapping[str, str], body: bytes = b""
    ) -> Tuple[int, Mapping[str, str], bytes]:  # pragma: no cover
        """This is the same method as in the base class with the addition of logging.

        No need to test/cover this method as functionally it is the same with the
        addition of logging the request-response cycle.
        """
        async with self._session.request(
            method, url, headers=headers, data=body
        ) as response:
            # We don't want to reveal the `installation_id` from the URL.
            if response.url.name != TOKEN_ENDPOINT:
                inject_status_color(response.status)
                data = "NONE" if body == b"" else body.decode(UTF_8_CHARSET)
                loggerlevel = (
                    logger.debug if response.status in STATUS_OK else logger.error
                )
                loggerlevel(
                    self.LOG_FORMAT,
                    {
                        # host is always going to be 'api.github.com'.
                        "method": method,
                        "path": response.url.raw_path_qs,
                        "version": f"{response.url.scheme.upper()}/"
                        f"{response.version.major}.{response.version.minor}",
                        "data": data,
                        "status": f"{response.status}:{response.reason}",
                    },
                )
            return response.status, response.headers, await response.read()