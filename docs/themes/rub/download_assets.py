"""Download official RUB fonts and logos without storing them in Git."""

# cspell:ignore Blau CMYK RUBInter Universitaet
# ruff: file-ignore[print]

from io import BytesIO
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

FONT_URL = (
    "https://markenportal.ruhr-uni-bochum.de/wp-content/uploads/2026/09/RUB_Inter.zip"
)
LOGO_URL = (
    "https://markenportal.ruhr-uni-bochum.de/wp-content/uploads/2026/10/RUB_Logo.zip"
)
FONT_NAMES = tuple(
    f"RUBInter-{style}.ttf" for style in ("Regular", "Italic", "SemiBold", "ExtraBold")
)
LOGO_FILES = {
    "favicon.svg": "RUB_Logo/Screen RGB/SVG/Ruhr-Universitaet-Bochum_SoMe_Blau_screen_rgb.svg",
    "rub-blue.svg": "RUB_Logo/Screen RGB/SVG/Ruhr-Universitaet-Bochum_Logo_Blau_screen_rgb.svg",
    "rub-logo.pdf": "RUB_Logo/Print CMYK/Ruhr-Universitaet-Bochum_Logo_Blau_print_cmyk.pdf",
    "rub-white.svg": "RUB_Logo/Screen RGB/SVG/Ruhr-Universitaet-Bochum_Logo_Weiss_screen_rgb.svg",
}
LICENSE_URL = "https://raw.githubusercontent.com/rsms/inter/v4.1/LICENSE.txt"


def main() -> None:
    download_fonts()
    download_logos()


def download_fonts() -> None:
    directory = Path(__file__).resolve().parent / "fonts"
    if all((directory / name).is_file() for name in (*FONT_NAMES, "OFL.txt")):
        print("RUB Inter fonts are already downloaded")
        return
    with (
        urlopen(FONT_URL, timeout=60) as response,
        ZipFile(BytesIO(response.read())) as archive,
    ):
        fonts = {name: archive.read(f"RUB_Inter/{name}") for name in FONT_NAMES}
    with urlopen(LICENSE_URL, timeout=60) as response:
        fonts["OFL.txt"] = response.read()
    directory.mkdir(exist_ok=True)
    for name, data in fonts.items():
        (directory / name).write_bytes(data)
    print("Downloaded official RUB Inter fonts")


def download_logos() -> None:
    directory = Path(__file__).resolve().parent / "images"
    if all((directory / name).is_file() for name in LOGO_FILES):
        print("RUB logos are already downloaded")
        return
    with (
        urlopen(LOGO_URL, timeout=60) as response,
        ZipFile(BytesIO(response.read())) as archive,
    ):
        logos = {name: archive.read(source) for name, source in LOGO_FILES.items()}
    directory.mkdir(exist_ok=True)
    for name, data in logos.items():
        (directory / name).write_bytes(data)
    print("Downloaded official RUB logos")


if __name__ == "__main__":
    main()
