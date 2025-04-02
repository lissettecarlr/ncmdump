# NCM Format Converter

[English](./README_EN.md) | [中文](./README.md)

## Overview

A tool that converts NetEase Cloud Music's .ncm format audio files to flac format, offering both Windows client and Web usage options.

## Usage

### Client Usage

Download the latest version from [releases](https://github.com/lissettecarlr/ncmdump/releases) and run it directly. Currently, only the Windows version is compiled; other platforms can run the source code directly.

Operation demonstration:
![Client Demo](./file/s3.gif)

File import methods:
* Drag and drop files into the interface
* Double-click the interface to open the file selection dialog

### Web Usage

Visit the Streamlit deployed version: [![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ncmdump.streamlit.app/)

Operation demonstration:
![Web Demo](./file/s2.gif)

## Environment Setup

If you need to run from source code, you'll need to install the following dependencies:

### Basic Environment

```bash
pip install mutagen
pip install pycryptodome
```

### GUI Environment

```bash
pip install PyQt6
pip install pyinstaller
```

### Web Environment

```bash
pip install streamlit
```

### Docker Environment

```bash
docker build -t ncmdump .
docker run -d -p 23231:23231 ncmdump
```

If you want to install all dependencies at once:

```bash
pip install -r requirements.txt
```

## Running Instructions

### GUI Application

You need to install both the basic and GUI environments first.

Run directly:
```bash
python gui.py
```

Or compile into an executable:
```bash
pyinstaller --onefile --add-data="file:file" -wF -i file/favicon-32x32.png -n "NCM Converter" .\gui.py
```

### Web Application

You need to install both the basic and web environments first.

Run:
```bash
streamlit run web.py --server.port 1111 --server.maxUploadSize=500
```

Parameter description:
- `--server.port 1111`: Set the server port to 1111
- `--server.maxUploadSize=500`: Set the maximum upload file size to 500MB