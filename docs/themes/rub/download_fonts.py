"""Download the official RUB Inter fonts without storing them in Git."""

# cspell:ignore RUBInter
# ruff: file-ignore[print]

from io import BytesIO
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

FONT_URL = (
    "https://markenportal.ruhr-uni-bochum.de/wp-content/uploads/2026/09/RUB_Inter.zip"
)
FONT_NAMES = tuple(
    f"RUBInter-{style}.ttf" for style in ("Regular", "Italic", "SemiBold", "ExtraBold")
)
LICENSE_URL = "https://raw.githubusercontent.com/rsms/inter/v4.1/LICENSE.txt"


def main() -> None:
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


if __name__ == "__main__":
    main()
