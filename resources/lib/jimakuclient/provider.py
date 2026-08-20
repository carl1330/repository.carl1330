from requests import (
    Session,
)

from resources.lib.cache import Cache
from resources.lib.exceptions import (
    ConfigurationError,
)

from resources.lib.utilities import __addon__

CONTENT_TYPE = "application/json"


class JimakuProvider:
    def __init__(self, api_key):
        if not api_key:
            raise ConfigurationError("api_key must be specified")

        self.api_key = api_key

        self.request_headers = {
            "Api-Key": self.api_key,
            "User-Agent": (
                f"Opensubtitles.com Kodi plugin v{__addon__.getAddonInfo('version')}"
            ),
            "Content-Type": CONTENT_TYPE,
            "Accept": CONTENT_TYPE,
        }

        self.session = Session()
        self.session.headers = self.request_headers  # type: ignore[reportAttributeAccessIssue]

        self.cache = Cache(key_prefix="jimaku_cc")
