import sys
import os

import xbmc
import xbmcaddon

from urllib.parse import parse_qsl

__addon__ = xbmcaddon.Addon("service.subtitles.jimaku-cc")
__addon_name__ = __addon__.getAddonInfo("name")
__language__ = __addon__.getLocalizedString


def log(module, msg):
    xbmc.log(f"### [{__addon_name__}:{module}] - {msg}", level=xbmc.LOGDEBUG)


def get_params(string=""):
    if string == "":
        param_string = sys.argv[2][1:]
    else:
        param_string = string

    return dict(parse_qsl(param_string))


def redact_path(path):
    """A playback path safe for the debug log.

    Streaming and plugin URLs routinely carry access tokens in the query
    string or credentials in the userinfo part - and debug logs are exactly
    what users paste on public forums. Local paths pass through untouched;
    anything with a scheme loses query, fragment and userinfo.
    """
    try:
        s = str(path)
        if "://" not in s:
            return s
        from urllib.parse import urlsplit

        parts = urlsplit(s)
        # userinfo can hide behind percent-encoding ('user%3Apass%40host') -
        # decode the authority to fixpoint BEFORE splitting the credentials off
        netloc = _fully_unquote(parts.netloc)
        if netloc is None:
            return f"{parts.scheme}://[host redacted]"
        had_userinfo = "@" in netloc
        host = netloc.rsplit("@", 1)[-1]  # drop user:pass@
        # a percent-encoded '?token=' ('%3Ftoken%3D...', or nested
        # '%253F...') hides INSIDE the path component - decode to fixpoint
        # so every encoding layer surfaces, then strip
        clean_path = _fully_unquote(parts.path)
        if clean_path is None:
            # never emit residue we could not fully decode
            return f"{parts.scheme}://{host}/[path redacted]"
        encoded_smuggle = "?" in clean_path or "#" in clean_path
        clean_path = clean_path.split("?", 1)[0].split("#", 1)[0]
        redacted = f"{parts.scheme}://{host}{clean_path}"
        if parts.query or parts.fragment or encoded_smuggle or had_userinfo:
            redacted += "  [query/credentials redacted]"
        return redacted
    except Exception:
        return "[unloggable path]"


def safe_media_filename(path):
    """Filename derived from a playback path with NO credential residue.

    Order matters: strip the query at the URL layer, decode percent-encoding
    TO FIXPOINT, then strip again - '/video%3Ftoken%3DX' (or nested
    '%253F...') decodes into a fresh '?token=X' that fewer decode passes
    would leave inside the basename.
    """
    try:
        s = str(path)
        if "://" in s:
            from urllib.parse import urlsplit

            s = _fully_unquote(urlsplit(s).path)
            if s is None:
                # never let undecodable residue reach a search query
                return ""
            s = s.split("?", 1)[0].split("#", 1)[0]
        return os.path.basename(s)
    except Exception:
        return ""


def _fully_unquote(s):
    """Percent-decode until nothing changes, or None to FAIL CLOSED.

    One unquote pass leaves an n-times-encoded delimiter ('%253F' ->
    '%3F') still hidden; decoding to fixpoint surfaces every layer so the
    strip that follows sees a literal '?'/'#'. A value still changing
    after 20 layers is adversarial by construction - return None so the
    caller drops the value entirely instead of passing residue through.
    """
    from urllib.parse import unquote

    for _ in range(20):
        decoded = unquote(s)
        if decoded == s:
            return s
        s = decoded
    return None


# Keys whose values are the user's viewing history (titles, filenames,
# queries) - they must never appear verbatim in a shared debug log.
_HISTORY_KEYS = {
    "query",
    "tv_show_title",
    "original_title",
    "basename",
    "filename",
    "file_path",
    "file_original_path",
    "video_filename",
    "release",
}


def loggable_media(mapping):
    """Mapping safe for the debug log, applied RECURSIVELY.

    URL values lose their query/credentials via redact_path; viewing-history
    values (titles, filenames, search queries) are reduced to a set/empty
    marker - presence is what debugging needs, the content is private.
    Recursion matters: fallback-attempt lists nest the same private keys."""

    def _clean(value):
        if isinstance(value, dict):
            # lstrip("_"): request objects expose the same keys as _query etc.
            return {
                k: (
                    ("<set>" if v else "<empty>")
                    if str(k).lstrip("_") in _HISTORY_KEYS
                    else _clean(v)
                )
                for k, v in value.items()
            }
        if isinstance(value, (list, tuple)):
            return [_clean(v) for v in value]
        if isinstance(value, str) and "://" in value:
            return redact_path(value)
        return value

    try:
        return _clean(dict(mapping))
    except Exception:
        return "[unloggable mapping]"
