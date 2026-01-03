# brePodder

A desktop podcast client built with Python and PyQt5.

## Features

- Subscribe to podcast RSS/Atom feeds
- Add YouTube channels as podcast sources
- Download episodes for offline listening
- Organize channels into folders with drag-and-drop
- Built-in audio player
- Search and filter podcasts
- Import/export subscriptions via OPML
- System tray integration

## Screenshots

The application provides a tabbed interface with:
- **Channels**: Browse and manage your podcast subscriptions
- **Downloads**: Monitor active downloads with progress tracking
- **Latest Downloads**: Quick access to recently downloaded episodes
- **Newest Episodes**: See the latest episodes across all subscriptions
- **Playlist**: Queue episodes and play them with the built-in player

## Requirements

- Python 3.10+
- PyQt5
- feedparser
- requests
- favicon

## Installation

### From Source

1. Clone the repository:
```bash
git clone https://github.com/yourusername/brePodder.git
cd brePodder
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
cd brepodder
python main.py
```

### Using pip

```bash
pip install -e .
brepodder
```

## Usage

### Adding Podcasts

1. Copy an RSS feed URL or YouTube channel URL
2. Paste it into the input field at the bottom of the Channels tab
3. Click "Add"

The application will fetch the feed, download the channel logo, and add all episodes to your library.

### Organizing Channels

- **Create folders**: Menu > Channels > New Folder
- **Move channels**: Drag and drop channels into folders
- **Search**: Use the search box above the channel list to filter

### Downloading Episodes

- **Double-click** an episode to start downloading
- **Right-click** an episode for context menu options:
  - Add to playlist
  - Download episode

Downloads appear in the "Downloads" tab with progress information.

### Playing Episodes

1. Add episodes to the playlist (double-click from any episode list)
2. Go to the "Playlist" tab
3. Double-click an episode to start playback
4. Use the play/pause button and seek slider to control playback

### Import/Export

- **Export**: Menu > Podcasts > Export - saves all subscriptions to `brepodder.opml`
- **Import**: Menu > Podcasts > Import - select an OPML file to import subscriptions

## Data Storage

All data is stored in `~/.brePodder/`:

```
~/.brePodder/
├── podcasts.sqlite      # Database with channels and episodes
├── ChannelName/         # Per-channel directories
│   ├── episodes/        # Downloaded audio files
│   ├── logo.png         # Channel artwork
│   └── favicon.ico      # Channel favicon
└── ...
```

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Quit | Menu > Podcasts > Quit |
| Update All | Menu > Podcasts > Update All |
| Add New | Menu > Podcasts > Add New |

## Configuration

Currently, configuration is handled through the code. Future versions may include a settings dialog.

Key defaults:
- Maximum concurrent downloads: 20
- Episodes shown per list: 50
- Image thumbnail size: 300x300 pixels

## Known Issues

- This is an experimental/learning project
- Some features may be incomplete
- YouTube support requires the video to have an available RSS feed

## Development

### Project Structure

```
brePodder/
├── brepodder/
│   ├── main.py              # Entry point
│   ├── brePodder.py         # Main application class
│   ├── ui/                  # UI components
│   │   ├── Ui_mainwindow.py
│   │   ├── treeviewwidget.py
│   │   └── mylineeditwidget.py
│   └── utils/               # Utilities
│       ├── sql.py           # Database operations
│       ├── download.py      # Download manager
│       ├── audioplayer.py   # Audio player widget
│       ├── youtube.py       # YouTube integration
│       └── opml.py          # OPML import/export
├── requirements.txt
├── pyproject.toml
└── setup.py
```

### Running from Source

```bash
cd brepodder
python main.py
```

### Building

```bash
pip install build
python -m build
```

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

This project is open source. See the LICENSE file for details.

## Acknowledgments

- Built with [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)
- Feed parsing by [feedparser](https://feedparser.readthedocs.io/)
- HTTP requests with [requests](https://requests.readthedocs.io/)

# Run tests
    uv run pytest tests/ -v           # Run all tests
    uv run pytest tests/ --cov        # Run with coverage


# Make wheels
  python -m build
  pip install --force-reinstall  ../brePodder/dist/brepodder-0.1.0-py3-none-any.whl

# PyInstaller

pyinstaller --name brepodder --exclude-module pytest --exclude-module tests --strip --onefile brepodder/main.py
pyinstaller brepodder.spec

# AppImage
./build-appimage-opus.sh  

## Make it executable
chmod +x output/brepodder-1.0.0-x86_64.AppImage

## Run it
./output/brepodder-1.0.0-x86_64.AppImage

## Test on different distros using Docker
docker run -it -v $(pwd):/app ubuntu:latest /app/brepodder-1.0.0-x86_64.AppImage
