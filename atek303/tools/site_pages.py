#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""ATEK303's pages for GitHub Pages (the gh-pages branch, checked out in SITE): fm1-base's installer and backup pages
for a release, with the same bar on top as the rest of the site.

    python3 tools/site_pages.py SITE 1.2          (after ./build.sh --release 1.2 and ./build.sh --web)

It runs fm1-base's tools/make_site.py on app/ and the release package, and from what it makes takes into
SITE/atek303/:
  install/    the web installer (Chrome or Edge, Web MIDI): the package, back to the stock firmware, the crash report
  backup/     backup and restore of the presets in the browser (fm1.toml backup = true)
  firmware/   the package the installer writes (atek303-X.Y.fwsc)
  play/       the browser version (app/build/emu)
and puts the bar (Try it, Install, Backup, Cheat sheet, Source) on those pages and the cheat sheet. m-bootloader's
option on the installer is left out: its own author warns about it on FM-1s with the newer flash (0xB36014). On Linux
the installer writes the classic way (the fast one loses the USB there)."""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]           # atek303/
site, version = Path(sys.argv[1]).resolve(), sys.argv[2]
out = site / "atek303"
pkg = HERE / "app" / "build" / f"atek303-{version}.fwsc"
if not pkg.exists():
    sys.exit(f"no {pkg}: ./build.sh --release {version} first")

PAGES = [("play", "Try it"), ("install", "Install"), ("backup", "Backup"), ("cheatsheet", "Cheat sheet")]
STYLE = """<style id="atek-bar-css">
#atek-bar{background:#16181C;border-bottom:1px solid #2a2e35;font:600 15px/1 "Barlow Semi Condensed",system-ui,sans-serif;
 letter-spacing:.02em;display:flex;flex-wrap:wrap;align-items:center;gap:4px 18px;padding:10px 16px;position:relative;z-index:50}
#atek-bar a{color:#9aa2b5;text-decoration:none;padding:4px 0}
#atek-bar a:hover,#atek-bar a.on{color:#5DB7FF}
#atek-bar .home{color:#fff;font-weight:700;margin-right:6px}
#atek-bar .home b{color:#FD9A00;font-weight:700}
#atek-bar .src{margin-left:auto}
#mbootopt{display:none!important}
@media print{#atek-bar{display:none}}
</style>"""


def bar(here):
    links = "".join(f'<a href="../{p}/"{" class=\"on\"" if p == here else ""}>{t}</a>' for p, t in PAGES)
    return (f'<nav id="atek-bar"><a class="home" href="../../">ATEK<b>303</b></a>{links}'
            f'<a class="src" href="https://github.com/animatek/FM1-Animatek">Source</a></nav>')


# the fast install loses the USB on Linux (here, from Chrome as from fm1_install.py: "USB LOST" at 2 %): the classic one
# there, and anywhere with ?classic
CLASSIC_OLD = "const up = new Updater(midi, lg);"
CLASSIC_NEW = ("const up = new Updater(midi, lg); if ((/Linux/.test(navigator.userAgent) && !/Android/.test(navigator.userAgent))"
               " || /[?&]classic/.test(location.search)) up.classic = true;")


def classic_on_linux(page):
    html = page.read_text(encoding="utf-8")
    if CLASSIC_NEW not in html:
        if html.count(CLASSIC_OLD) != 1:
            sys.exit(f"{page}: the installer's Updater is not where it was (fm1-base changed): check CLASSIC_OLD")
        page.write_text(html.replace(CLASSIC_OLD, CLASSIC_NEW), encoding="utf-8")


def put_bar(page, here):
    html = page.read_text(encoding="utf-8")
    if 'id="atek-bar"' in html:                     # (again on a page that has it: the bar as it is now)
        a = html.index('<style id="atek-bar-css">')
        html = html[:a] + html[html.index("</style>", a) + 8:]
        a = html.index('<nav id="atek-bar">')
        html = html[:a] + html[html.index("</nav>", a) + 6:]
    html = html.replace("</head>", STYLE + "\n</head>", 1)
    i = html.index("<body")
    j = html.index(">", i) + 1
    page.write_text(html[:j] + bar(here) + html[j:], encoding="utf-8")


with tempfile.TemporaryDirectory() as tmp:
    made = Path(tmp) / "site"
    subprocess.run([sys.executable, str(HERE / "base" / "tools" / "make_site.py"), str(HERE / "app"), str(pkg),
                    version, str(made)], check=True)
    for d in ["install", "backup"]:
        shutil.rmtree(out / d, ignore_errors=True)
        shutil.copytree(made / d, out / d)
    (out / "firmware").mkdir(parents=True, exist_ok=True)
    shutil.copy(made / "firmware" / pkg.name, out / "firmware" / pkg.name)
shutil.rmtree(out / "play", ignore_errors=True)
shutil.copytree(HERE / "app" / "build" / "emu", out / "play", ignore=shutil.ignore_patterns("o2", "web", "*.o"))
shutil.copy(HERE / "cheatsheet" / "index.html", out / "cheatsheet" / "index.html")
classic_on_linux(out / "install" / "index.html")
for p, _ in PAGES:
    put_bar(out / p / "index.html", p)
print(f"{out}: play/, install/, backup/, firmware/{pkg.name}, cheatsheet/ with the bar")
