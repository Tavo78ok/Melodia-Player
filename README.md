## 🎵 Melodia Music Player

> A beautiful, dark music player for Linux — built with **Python 3**, **GTK4**, and **libadwaita**.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![GTK](https://img.shields.io/badge/GTK-4.0-green)
![libadwaita](https://img.shields.io/badge/libadwaita-1.x-orange)
![License](https://img.shields.io/badge/License-GPL--3.0-red)

---

## Features

- 🎨 Dark luxury aesthetic with coral accent colour
- 🎵 Plays **MP3, FLAC, OGG, M4A, AAC, WAV, Opus** and more
- 🖼  Embedded **album art** with gradient placeholders
- 📊 Animated **equaliser bars** on the playing track
- 🔀 Shuffle & repeat modes
- 🔍 Real-time search across title / artist / album
- 🗂  Recursive folder scanner
- ⌨  Keyboard-friendly (GTK4 native)

---

## Install from .deb

```bash
# Build dependencies (once)
sudo apt install build-essential devscripts debhelper \
                 dh-python python3-all python3-setuptools

# Build the package
chmod +x build_deb.sh
./build_deb.sh

# Install
sudo dpkg -i ../melodia_1.0.0-1_all.deb
sudo apt-get install -f   # resolve any missing runtime deps
```

---

## Run from source (no install)

```bash
# Runtime dependencies
sudo apt install python3-gi python3-gi-cairo \
                 gir1.2-gtk-4.0 gir1.2-adw-1 \
                 gir1.2-gst-plugins-base-1.0 \
                 gstreamer1.0-plugins-good \
                 gstreamer1.0-plugins-ugly \
                 gstreamer1.0-libav \
                 python3-mutagen

python3 melodia.py
```

---

## Project structure

```
melodia/
├── src/melodia/
│   ├── __init__.py   — version
│   ├── main.py       — Adw.Application
│   ├── window.py     — main UI (GTK4 + CSS)
│   ├── player.py     — GStreamer backend
│   └── library.py    — music scanner / mutagen
├── data/
│   ├── com.github.melodia.desktop
│   └── icons/…/com.github.melodia.svg
├── debian/           — Debian packaging
├── melodia.py        — source-run launcher
├── setup.py
└── build_deb.sh
```

---

## Customisation

- **Accent colour** — change `ACCENT = '#E8725A'` in `window.py`
- **Default music folder** — change `Path.home() / 'Music'` in `_try_load_default_library`
- **Window size** — change `self.set_default_size(1280, 780)` in `_build_ui`

---

## License

GNU General Public License v3.0

<img width="1440" height="900" alt="Captura de pantalla_2026-03-19_04-16-41" src="https://github.com/user-attachments/assets/586575d9-9742-4aa2-a545-1f9352379378" />

<img width="1440" height="900" alt="Captura de pantalla_2026-03-19_04-17-16" src="https://github.com/user-attachments/assets/516eec69-4322-4ab9-af74-2bc095cd1803" />


<img width="1440" height="900" alt="Captura de pantalla_2026-03-19_04-17-50" src="https://github.com/user-attachments/assets/43dc3402-a79a-4712-b551-33bd45848c49" />



