# carl1330's Kodi Repository

Kodi addon repository for [Jimaku](repo/service.subtitles.jimaku-cc) — a subtitle
service addon that searches and downloads Japanese subtitles from
[jimaku.cc](https://jimaku.cc).

Requires Kodi 19 (Matrix) or newer.

## Install

**Recommended — install the repository, so you get updates automatically:**

1. Kodi → *Settings* → *File manager* → *Add source*
2. Enter `https://carl1330.github.io/repository.carl1330/` and name it `carl1330`
3. *Settings* → *Add-ons* → *Install from zip file* → `carl1330` → `repository.carl1330-1.0.0.zip`
4. *Install from repository* → *carl1330's Repository* → *Subtitles* → *Jimaku*

If Kodi refuses step 3, enable *Settings* → *System* → *Add-ons* → *Unknown sources*.

**Direct zip install (no updates):** download the addon zip from
[`repo/zips/service.subtitles.jimaku-cc/`](repo/zips/service.subtitles.jimaku-cc/)
and use *Install from zip file*.

## Configuration

Jimaku needs an API key. Get one from your jimaku.cc account, then set it in
*Add-ons* → *Jimaku* → *Configure* → *API key*.

## Layout

```
_repo_generator.py    zips each addon and writes repo/zips/addons.xml{,.md5}
tools/make_index.py   writes the index.html listings Kodi browses over Pages
repo/
├── repository.carl1330/          the repository addon itself
├── service.subtitles.jimaku-cc/  the Jimaku addon source
└── zips/                         GENERATED — the published artifact, committed
```

GitHub Pages serves this repository from `main` / root, so
`repo/zips/addons.xml` is what Kodi polls for updates.

## Releasing a new version

1. Bump `version` in the addon's `addon.xml` — **this is what triggers a build**;
   `_repo_generator.py` only rebuilds a zip when the version differs from the
   one already recorded in `addons.xml`.
2. Add an entry to that addon's `changelog.txt`, and mirror it into the
   `<news>` element in `addon.xml` (Kodi shows `<news>` on the update prompt).
3. Push to `main`. The `Build Kodi repository` workflow regenerates the zips
   and listings and commits them back.

To build locally instead:

```sh
python3 _repo_generator.py && python3 tools/make_index.py
```

## Development

```sh
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt   # requests + Kodistubs, for editor completion
```

## License

GPL-2.0-only
