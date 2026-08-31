import os
import re
import shutil
import sys
import time
import uuid

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

from resources.lib.exceptions import ProviderError
from resources.lib.jimakuclient.provider import JimakuProvider
from resources.lib.utilities import __language__, get_params, log

__addon__ = xbmcaddon.Addon("service.subtitles.jimaku-cc")
__addonname__ = __addon__.getAddonInfo("name")
__scriptid__ = __addon__.getAddonInfo("id")

__profile__ = xbmcvfs.translatePath(__addon__.getAddonInfo("profile"))
__temp__ = xbmcvfs.translatePath(os.path.join(__profile__, "temp", ""))

TEMP_MAX_AGE_SECONDS = 60 * 60 * 6


def clean_temp_directory():
    """Removes STALE temp entries and ensures the add-on temp directory exists.

    Only entries older than TEMP_MAX_AGE_SECONDS are deleted - a concurrent
    invocation's fresh subtitle stays on disk.
    """
    try:
        if os.path.exists(__temp__):
            now = time.time()
            for entry in os.listdir(__temp__):
                entry_path = os.path.join(__temp__, entry)
                try:
                    if now - os.path.getmtime(entry_path) < TEMP_MAX_AGE_SECONDS:
                        continue
                    if os.path.isfile(entry_path) or os.path.islink(entry_path):
                        os.unlink(entry_path)
                    elif os.path.isdir(entry_path):
                        shutil.rmtree(entry_path, ignore_errors=True)
                except Exception as err:
                    log(
                        __name__,
                        f"Failed to clean temp file {entry_path}: {type(err).__name__}",
                    )
        else:
            os.makedirs(__temp__, exist_ok=True)
    except Exception as e:
        log(__name__, f"Temp directory initialization error: {type(e).__name__}")


# Run initial cleanup on load
clean_temp_directory()


def unique_subtitle_path(display_name, language, sub_extension):
    return os.path.join(
        __temp__,
        f"{display_name}.{language}.{uuid.uuid4().hex[:8]}.{sub_extension}",
    )


class SubtitleDownloader:

    def __init__(self):
        self.params = get_params()
        self.handle = int(sys.argv[1])
        self.jimaku_client = JimakuProvider(__addon__.getSetting("api_key"))

    def handle_action(self):
        action = self.params.get("action")
        log(__name__, f"action '{action}' called")
        if not action:
            log(__name__, "no action specified, nothing to do")
            return

        version = __addon__.getAddonInfo("version")
        addon_name = __addon__.getAddonInfo("name")
        icon_path = xbmcvfs.translatePath(
            os.path.join(
                __addon__.getAddonInfo("path"),
                "resources",
                "media",
                "os_logo_512x512.png",
            )
        )

        if action == "manualsearch":
            self.manual_search(self.params.get("searchstring", ""))
        elif action == "search":
            self.search()
        elif action == "download":
            xbmcgui.Dialog().notification(
                f"{addon_name} v{version}",
                "Downloading subtitle...",
                icon_path,
                2000,
                False,
            )
            self.download()

    def manual_search(self, query: str):
        xbmcgui.Dialog().ok(__addonname__, __language__(32100).format(query))

    def _search_entries(self):
        tag = xbmc.Player().getVideoInfoTag()
        tmdb_id = tag.getUniqueID("tmdb")
        anilist_id = tag.getUniqueID("anilist_id") or tag.getUniqueID("anilist")

        media_type = "tv" if (tag.getSeason() or tag.getEpisode()) else "movie"

        if anilist_id:
            log(__name__, f"searching by anilist id {anilist_id}")
            response = self.jimaku_client.search_subtitle_anilist_id(
                anilist_id=anilist_id, anime=True
            )
            if response:
                return response

        if tmdb_id:
            log(__name__, f"searching by tmdb id {tmdb_id}")
            response = self.jimaku_client.search_subtitle_tmdb_id(
                tmdb_id=tmdb_id, media_type=media_type, anime=True
            )
            if response:
                return response

        file_title = os.path.splitext(os.path.basename(xbmc.Player().getPlayingFile()))[
            0
        ]
        title = tag.getTVShowTitle() or tag.getTitle() or file_title
        log(__name__, f"searching by title {title}")
        return self.jimaku_client.search_subtitle_query(
            query=title, anime=True, episode=tag.getEpisode()
        )

    def search(self):
        episode = xbmc.Player().getVideoInfoTag().getEpisode()
        episodes = self._search_entries()

        if not episodes:
            log(__name__, "No subtitle found")
            xbmcplugin.endOfDirectory(self.handle)
            return

        for entry in episodes:
            try:
                files = self.jimaku_client.get_entry_files(entry.id, episode=episode)
            except ProviderError as e:
                log(
                    __name__,
                    f"Error fetching files for entry {entry.id}: {type(e).__name__}",
                )
                continue
            for sub_file in files:
                try:
                    self.list_subtitle(entry, sub_file)
                except Exception as e:
                    log(
                        __name__,
                        f"Skipping unusable subtitle entry "
                        f"{getattr(sub_file, 'name', '?')}: {type(e).__name__}",
                    )
                    continue

        xbmcplugin.endOfDirectory(self.handle)

    def list_subtitle(self, entry, sub_file):
        display_name = entry.english_name or entry.name or str(entry.id)
        list_item = xbmcgui.ListItem(label=display_name, label2=sub_file.name)
        list_item.setProperty(
            "unverified",
            "true" if getattr(entry.flags, "unverified", False) else "false",
        )
        list_item.setProperty(
            "adult", "true" if getattr(entry.flags, "adult", False) else "false"
        )
        list_item.setArt({"thumb": "jp"})

        from urllib.parse import quote

        url = (
            f"plugin://{__scriptid__}/?action=download"
            f"&id={entry.id}&file_url={quote(sub_file.url, safe='')}&name={quote(sub_file.name, safe='')}"
        )
        xbmcplugin.addDirectoryItem(
            handle=self.handle, url=url, listitem=list_item, isFolder=False
        )

    def download(self):
        from urllib.parse import unquote

        sub_file_url = self.params.get("file_url")
        sub_name = self.params.get("name")

        if not sub_file_url:
            log(__name__, "download missing file_url, nothing to do")
            return

        file_url = unquote(sub_file_url)
        name = unquote(sub_name) if sub_name else "subtitle.srt"

        ext = os.path.splitext(name)[1] or ".srt"
        if not ext.startswith("."):
            ext = "." + ext

        display_name = os.path.splitext(os.path.basename(name))[0]
        display_name = (
            re.sub(r"[^\w\- .]+", "", display_name, flags=re.UNICODE).strip()
            or "subtitle"
        )

        try:
            content = self.jimaku_client.download_file(file_url)
        except ProviderError as e:
            log(__name__, f"Download failed: {type(e).__name__}")
            xbmcgui.Dialog().notification(
                __addonname__,
                "Download failed",
                xbmcgui.NOTIFICATION_ERROR,
                3000,
                False,
            )
            return

        clean_temp_directory()
        subtitle_path = unique_subtitle_path(display_name, "ja", ext)
        tmp_path = subtitle_path + ".tmp"
        log(__name__, f"download subtitle_path: {subtitle_path}")

        try:
            with open(tmp_path, "wb") as tmp_file:
                tmp_file.write(content)

            if os.path.exists(subtitle_path):
                try:
                    os.unlink(subtitle_path)
                except Exception:
                    pass

            os.rename(tmp_path, subtitle_path)
        except Exception as e:
            log(__name__, f"Failed to save subtitle file: {type(e).__name__}")
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
            return

        list_item = xbmcgui.ListItem(label=display_name)
        xbmcplugin.addDirectoryItem(
            handle=self.handle, url=subtitle_path, listitem=list_item, isFolder=False
        )


def get_file_path():
    return xbmc.Player().getPlayingFile()
