from requests import (
    Session,
)

from resources.lib.cache import Cache
from resources.lib.exceptions import (
    ConfigurationError,
    ProviderError,
)
from resources.lib.jimakuclient.model.request.files import JimakuFilesRequest
from resources.lib.jimakuclient.model.request.search import JimakuSearchRequest
from resources.lib.jimakuclient.model.response.files import JimakuFileEntry
from resources.lib.jimakuclient.model.response.search import JimakuSearchResponse
from resources.lib.utilities import __addon__, log

CONTENT_TYPE = "application/json"
API_URL = "https://jimaku.cc/api"
SEARCH = "/entries/search"


class JimakuProvider:
    def __init__(self, api_key):
        if not api_key:
            raise ConfigurationError("api_key must be specified")

        self.api_key = api_key
        log(__name__, "API KEY" + api_key)

        self.request_headers = {
            "Authorization": f"{self.api_key}",
            "User-Agent": f"jimaku.cc Kodi plugin v{__addon__.getAddonInfo('version')}",
            "Content-Type": CONTENT_TYPE,
            "Accept": CONTENT_TYPE,
        }

        self.session = Session()
        self.session.headers = self.request_headers  # type: ignore[reportAttributeAccessIssue]

        self.cache = Cache(key_prefix="jimaku_cc")

    def search_subtitle_tmdb_id(self, tmdb_id: str, media_type: str, anime: bool):
        encoded_tmdb_id = f"{media_type}:{tmdb_id}"
        search_request = JimakuSearchRequest(anime=anime, tmdb_id=encoded_tmdb_id)
        log(__name__, f"tmdb_id {encoded_tmdb_id}")
        search_response = self.session.get(
            API_URL + SEARCH, params=search_request.params
        )

        if not search_response.ok:
            raise ProviderError(
                f"HTTP error {search_response.status_code} during search subtitle tmdb request"
            )

        search_response_json = search_response.json()
        log(__name__, search_response_json)
        if isinstance(search_response_json, list):
            return [JimakuSearchResponse(**item) for item in search_response_json]

        return [JimakuSearchResponse(**search_response_json)]

    def search_subtitle_anilist_id(self, anilist_id, anime: bool):
        search_request = JimakuSearchRequest(anime=anime, anilist_id=anilist_id)
        log(__name__, f"anilist_id {anilist_id}")
        search_response = self.session.get(
            API_URL + SEARCH, params=search_request.params
        )

        if not search_response.ok:
            raise ProviderError(
                f"HTTP error {search_response.status_code} during search subtitle anilist request"
            )

        search_response_json = search_response.json()
        log(__name__, search_response_json)
        if isinstance(search_response_json, list):
            return [JimakuSearchResponse(**item) for item in search_response_json]

        return [JimakuSearchResponse(**search_response_json)]

    def search_subtitle_query(self, query: str, anime: bool, episode=None):
        search_request = JimakuSearchRequest(anime=anime, query=query)
        log(__name__, f"query {query}")
        if episode is not None:
            log(__name__, f"episode {episode}")
        search_response = self.session.get(
            API_URL + SEARCH, params=search_request.params
        )

        if not search_response.ok:
            raise ProviderError(
                f"HTTP error {search_response.status_code} during search subtitle query request"
            )

        search_response_json = search_response.json()
        log(__name__, search_response_json)
        if isinstance(search_response_json, list):
            return [JimakuSearchResponse(**item) for item in search_response_json]

        return [JimakuSearchResponse(**search_response_json)]

    def get_entry_files(self, entry_id: int, episode=None):
        request = JimakuFilesRequest(id=entry_id, episode=episode)
        log(__name__, f"entry_id {entry_id} episode {episode}")
        response = self.session.get(
            API_URL + f"/entries/{entry_id}/files", params=request.params
        )

        if not response.ok:
            raise ProviderError(
                f"HTTP error {response.status_code} during get entry files request"
            )

        response_json = response.json()
        log(__name__, response_json)
        if not isinstance(response_json, list):
            return []
        return [JimakuFileEntry(**item) for item in response_json]

    def download_file(self, file_url: str):
        log(__name__, f"downloading file {file_url}")
        response = self.session.get(file_url)

        if not response.ok:
            raise ProviderError(
                f"HTTP error {response.status_code} during download file request"
            )

        return response.content
