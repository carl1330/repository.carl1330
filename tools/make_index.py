"""
Writes the index.html files that let Kodi's HTTP file browser walk this
repository over GitHub Pages.

Pages serves static files only -- it does not generate directory listings --
so browsing to /repo/zips/ from Kodi's File Manager would 404. Kodi's HTTP VFS
builds a directory listing by parsing <a href> anchors out of the returned
HTML, so we generate those listings ourselves.

Also copies the newest repository.carl1330 zip to the repo root, so the very
first install is a single click from the source URL.

Run from the root of the checked-out repo, after _repo_generator.py.
"""

import os
import re
import shutil

REPO_ADDON_ID = "repository.carl1330"
ZIPS_DIR = os.path.join("repo", "zips")

_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
</head>
<body>
<h1>{title}</h1>
<ul>
{items}
</ul>
</body>
</html>
"""


def version_key(filename):
    """Sort key for `<addon-id>-<version>.zip` names, newest last."""
    match = re.search(r"-([0-9][0-9.+~-]*)\.zip$", filename)
    if not match:
        return ()
    return tuple(
        int(part) if part.isdigit() else 0
        for part in re.split(r"[.+~-]", match.group(1))
    )


def write_page(directory, title, entries):
    """Write an index.html listing `entries` (each an (href, label) pair)."""
    items = "\n".join(
        '<li><a href="{0}">{1}</a></li>'.format(href, label) for href, label in entries
    )
    path = os.path.join(directory, "index.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(_PAGE.format(title=title, items=items))
    print("Wrote {}".format(path))


def main():
    if not os.path.isdir(ZIPS_DIR):
        raise SystemExit("{} does not exist -- run _repo_generator.py first".format(ZIPS_DIR))

    addon_ids = sorted(
        name
        for name in os.listdir(ZIPS_DIR)
        if os.path.isdir(os.path.join(ZIPS_DIR, name))
    )

    root_entries = []

    # One listing per addon folder, e.g. /repo/zips/service.subtitles.jimaku-cc/
    for addon_id in addon_ids:
        addon_dir = os.path.join(ZIPS_DIR, addon_id)
        zips = sorted(
            (n for n in os.listdir(addon_dir) if n.endswith(".zip")), key=version_key
        )
        extras = sorted(
            n
            for n in os.listdir(addon_dir)
            if not n.endswith(".zip") and n != "index.html"
        )
        write_page(
            addon_dir,
            addon_id,
            [(n, n) for n in zips] + [(n, n) for n in extras],
        )

        if zips:
            root_entries.append(
                ("repo/zips/{0}/{1}".format(addon_id, zips[-1]), zips[-1])
            )

        # The repository addon itself gets copied to the root so that adding
        # the source URL in Kodi shows the installable zip immediately.
        if addon_id == REPO_ADDON_ID and zips:
            newest = zips[-1]
            for stale in os.listdir("."):
                if stale.startswith(REPO_ADDON_ID + "-") and stale.endswith(".zip"):
                    if stale != newest:
                        os.remove(stale)
            shutil.copy(os.path.join(addon_dir, newest), newest)
            print("Copied {} to repository root".format(newest))

    # /repo/zips/
    write_page(
        ZIPS_DIR,
        "zips",
        [("{}/".format(a), "{}/".format(a)) for a in addon_ids]
        + [(n, n) for n in ("addons.xml", "addons.xml.md5") if os.path.exists(os.path.join(ZIPS_DIR, n))],
    )

    # /repo/
    write_page("repo", "repo", [("zips/", "zips/")])

    # Repository root: the installable zip first, then everything else.
    root_zip = next(
        (
            n
            for n in sorted(os.listdir("."))
            if n.startswith(REPO_ADDON_ID + "-") and n.endswith(".zip")
        ),
        None,
    )
    entries = []
    if root_zip:
        entries.append((root_zip, root_zip))
    entries.append(("repo/zips/", "repo/zips/"))
    entries.extend(e for e in root_entries if not e[0].endswith(root_zip or "\0"))
    write_page(".", "carl1330's Kodi Repository", entries)


if __name__ == "__main__":
    main()
