# LinyGUI

**Elegant Image Compression for Linux**

LinyGUI is a modern, beautifully designed desktop application for compressing and resizing images using the TinyPNG API. Built with GTK4 and libadwaita, it features a stunning glassmorphism UI and is distributed as a Flatpak for universal Linux compatibility.

## Features

- **Smart Compression** — Lossless-quality PNG, JPEG, and WebP compression via TinyPNG
- **Smart Resize** — Scale, Fit, Cover, and Thumb modes for intelligent image resizing
- **Drag & Drop** — Simply drop images onto the window to compress
- **Batch Processing** — Compress multiple images at once with progress tracking
- **Metadata Preservation** — Optionally keep copyright, GPS location, and creation date
- **Modern UI** — Dark glassmorphism design with smooth animations

## Requirements

- Linux (any distribution with Flatpak support)
- TinyPNG API key — get one free at [tinypng.com/developers](https://tinypng.com/developers)

## Installation

### Flatpak (Recommended)

```bash
flatpak install org.devopsinquisitor.linygui
```

### From Source

```bash
# Dependencies: python3, gtk4, libadwaita, python3-tinify
cd linygui/src
python3 main.py
```

## License

MIT License — Copyright (c) 2026 DevOpsInquisitor

## Author

**DevOpsInquisitor**
