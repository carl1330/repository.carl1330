import xbmc
import xbmcaddon
import xbmcgui

__addon__ = xbmcaddon.Addon("service.subtitles.jimaku-cc")
__addon_name__ = __addon__.getAddonInfo("name")
__language__ = __addon__.getLocalizedString


def log(module, msg):
    xbmc.log(f"### [{__addon_name__}:{module}] - {msg}", level=xbmc.LOGDEBUG)
