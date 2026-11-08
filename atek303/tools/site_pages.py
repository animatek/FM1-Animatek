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
and puts the bar (Try it, Install, Backup, Cheat sheet, Source) on those pages and the cheat sheet, fm1-base's three in
Animatek's colours; and writes the front page (SITE/index.html), a hero with the cover. m-bootloader's
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
# the bar, on every page; on fm1-base's three (play, install, backup) Animatek's colours over their own (their variables,
# the light and the dark ones alike: the site is dark, slate and blue), the bar full width at the very top (no gap above it)
# and the emulator's own title gone (the bar says it)
BAR_CSS = """@import url('https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@600;700&display=swap');
#atek-bar{background:#16181C;border-bottom:1px solid #2a2e35;font:600 15px/1 "Barlow Semi Condensed",system-ui,sans-serif;
 letter-spacing:.02em;display:flex;flex-wrap:wrap;align-items:center;gap:4px 20px;padding:14px max(16px,calc(50vw - 520px));
 position:sticky;top:0;z-index:50;box-sizing:border-box}
#atek-bar a{color:#9aa2b5;text-decoration:none;padding:4px 0}
#atek-bar a:hover,#atek-bar a.on{color:#5DB7FF}
#atek-bar .home{color:#fff;font-weight:700;font-size:17px;margin-right:8px}
#atek-bar .home b{color:#2C7FFF;font-weight:700}
#atek-bar .src{margin-left:auto}
@media (max-width:560px){#atek-bar{gap:4px 14px}#atek-bar .src{display:none}}
@media print{#atek-bar{display:none}}"""
THEME_CSS = """:root,:root[data-theme],:root:not([data-theme="light"]){--bg:#0f1114!important;--ground:#0f1114!important;
 --fg:#e8ecf3!important;--ink:#e8ecf3!important;--dim:#9aa2b5!important;--muted:#9aa2b5!important;--rule:#2a2e35!important;
 --card:#181b20!important;--accent:#2C7FFF!important;--accent-ink:#5DB7FF!important;--on-accent:#fff!important;
 --teal:#5DB7FF!important;--bad:#ff6b6b!important;--focus:#5DB7FF!important;color-scheme:dark!important}
html{background:#0f1114}
body{padding-top:0!important;overflow-x:hidden}
body>#atek-bar{margin:0 calc(50% - 50vw) 28px;width:100vw}
body>header{display:none!important}
a{color:#5DB7FF}
.start button{background:#2C7FFF!important;color:#fff!important}
.held .btnface,.held .keyface{stroke:#FD9A00!important}
.latched .btnface,.latched .keyface{stroke:#5DB7FF!important}
#mbootopt{display:none!important}"""


def style(theme):
    return f'<style id="atek-bar-css">\n{BAR_CSS}\n{THEME_CSS if theme else ""}\n</style>'


def bar(here, up="../"):
    links = "".join(f'<a href="{up}{p}/"{" class=\"on\"" if p == here else ""}>{t}</a>' for p, t in PAGES)
    return (f'<nav id="atek-bar"><a class="home" href="{up}../">ATEK<b>303</b></a>{links}'
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


def put_bar(page, here, theme=True):
    html = page.read_text(encoding="utf-8")
    if 'id="atek-bar"' in html:                     # (again on a page that has it: the bar as it is now)
        a = html.index('<style id="atek-bar-css">')
        html = html[:a] + html[html.index("</style>", a) + 8:]
        a = html.index('<nav id="atek-bar">')
        html = html[:a] + html[html.index("</nav>", a) + 6:]
    html = html.replace("</head>", style(theme) + "\n</head>", 1)
    i = html.index("<body")
    j = html.index(">", i) + 1
    page.write_text(html[:j] + bar(here) + html[j:], encoding="utf-8")


# the front page: a hero, the cover on the left (it carries the name), what it is and the ways in on the right
FRONT = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ATEK303 for M-VAVE FM-1 · Animatek</title>
<meta name="description" content="ATEK303, an acid firmware for the M-VAVE FM-1 by Animatek: play it in your browser, install it from the browser, back up your presets, read the cheat sheet.">
<meta property="og:image" content="https://animatek.github.io/FM1-Animatek/atek303/art/cover-1024.jpg">
<link rel="icon" href="atek303/art/splash-smiley.png">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
{css}
:root{color-scheme:dark}
html,body{background:#0f1114}
body{margin:0;min-height:100vh;color:#e8ecf3;font-family:Inter,system-ui,sans-serif;display:flex;flex-direction:column}
.hero{flex:1;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:56px;align-items:center;
 max-width:1040px;width:100%;margin:0 auto;padding:56px 24px;box-sizing:border-box;
 background:radial-gradient(ellipse 60% 55% at 28% 50%,rgba(44,127,255,.14),transparent 70%)}
.hero img{width:100%;height:auto;border-radius:18px;box-shadow:0 24px 70px rgba(0,0,0,.65)}
.kicker{color:#5DB7FF;font-weight:600;font-size:14px;letter-spacing:.14em;text-transform:uppercase;margin:0 0 14px}
.lead{font-size:clamp(20px,2.3vw,26px);line-height:1.35;font-weight:600;margin:0 0 14px}
.sub{color:#9aa2b5;font-size:16px;line-height:1.6;margin:0 0 28px}
.btns{display:flex;flex-wrap:wrap;gap:12px}
a.btn{display:inline-flex;align-items:center;min-height:46px;padding:0 22px;border-radius:999px;font-weight:600;
 text-decoration:none;font-size:15px;box-sizing:border-box}
a.pri{background:#2C7FFF;color:#fff}
a.pri:hover{background:#4a92ff}
a.sec{border:1.5px solid #2a2e35;color:#e8ecf3}
a.sec:hover{border-color:#5DB7FF;color:#5DB7FF}
.ver{margin:22px 0 0;color:#6f7787;font-size:13px}
.ver b{color:#FD9A00;font-weight:600}
footer{color:#6f7787;font-size:13px;line-height:1.6;text-align:center;padding:24px 16px 36px;border-top:1px solid #1d2026}
footer a{color:#9aa2b5}
@media (max-width:760px){.hero{grid-template-columns:1fr;gap:32px;padding:28px 16px}
 .hero img{max-width:440px;margin:0 auto;display:block}}
</style>
</head>
<body>
{bar}
<main class="hero">
  <img src="atek303/art/cover.jpg" width="1024" height="1024" alt="ATEK303 by Animatek, firmware for the M-VAVE FM-1">
  <div>
    <p class="kicker">Firmware for the M-VAVE FM-1</p>
    <p class="lead">An acid machine: the ATEK303 voice from VCV Rack with its own pattern generator. Press PLAY and a line plays.</p>
    <p class="sub">14 oscillators, 64 steps with a piano-roll editor, drive, chorus, a synced delay and a plate reverb, 12 factory presets in 32 slots, MIDI in, out and clock.</p>
    <div class="btns">
      <a class="btn pri" href="atek303/play/">Play it in your browser</a>
      <a class="btn pri" href="atek303/install/">Install on your FM-1</a>
      <a class="btn sec" href="atek303/backup/">Back up presets</a>
      <a class="btn sec" href="atek303/cheatsheet/">Cheat sheet</a>
      <a class="btn sec" href="atek303/firmware/{pkg}">Download .fwsc</a>
    </div>
    <p class="ver">Version <b>{version}</b> · Chrome or Edge to install, over USB</p>
  </div>
</main>
<footer>The browser version runs the firmware's own code, compiled to WebAssembly (fm1-base's emulator). Computer keys and the mouse play it.<br>
GPL-3.0 · <a href="https://github.com/animatek/FM1-Animatek">source on GitHub</a> · <a href="https://animatek.net">animatek.net</a> · Not affiliated with M-VAVE or Roland.</footer>
</body>
</html>
"""


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
    put_bar(out / p / "index.html", p, theme=p != "cheatsheet")   # (the cheat sheet keeps its own look: it prints)
(site / "index.html").write_text(FRONT.replace("{css}", BAR_CSS).replace("{bar}", bar("", up="atek303/"))
                                 .replace("{pkg}", pkg.name).replace("{version}", version), encoding="utf-8")
print(f"{out}: play/, install/, backup/, firmware/{pkg.name}, cheatsheet/ with the bar")
