# B2 Cloud Storage Manager

A simple Windows GUI application for managing Backblaze B2 cloud storage.

## Features

- Connect to B2 with Application Keys
- List and browse buckets
- Upload files to B2
- Download files from B2
- Delete files from B2
- Clean and intuitive interface

## Download

Download the latest release from the [Releases](https://github.com/MEIRMEIR513/b2-manager/releases) page.

## Usage

1. Download `B2Manager.exe`
2. Run the application
3. Enter your B2 Application Key ID and Key
4. Click "Connect"
5. Select a bucket to view files
6. Upload, download, or delete files as needed

## Building from Source

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --add-data "b2-windows.exe;." b2_manager.py
```

## Requirements

- Windows 10 or later
- b2-windows.exe (included in the build)
