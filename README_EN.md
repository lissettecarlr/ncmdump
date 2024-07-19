# ncm -> flac Converter
[English](./README_EN.md) | [中文](./README.md)

## Overview

Convert .ncm format audio files to flac format, providing both a Windows client and a web usage option.

## Usage

### Client Usage:
Download and run from [releases](https://github.com/lissettecarlr/ncmdump/releases). Currently, only the Windows version is compiled; other platforms can run the code directly.

Interface preview:
![s3](./file/s3.gif)

----------------------

### Web Usage
Currently deployed on Streamlit: [![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ncmdump.streamlit.app/)

Interface preview:
![s2](./file/s2.gif)

## Environment
To run the code, you need to install the corresponding libraries.

Basic environment:
```bash
pip install mutagen
pip install pycryptodome
```

GUI environment:
```bash
pip install PyQt6
pip install pyinstaller
```

Web environment:
```bash
pip install streamlit
```

If you're feeling lazy, you can install everything at once:
```bash
pip install -r requirements.txt
```

## Running

### GUI

You need to install both the basic and GUI environments first.

Run directly:
```bash
python gui.py
```

or

Compile into an executable:
```bash
pyinstaller --onefile --add-data="file:file" -wF -i file/favicon-32x32.png -n "NCM Converter" .\gui.py
```

### Web
You need to install both the basic and web environments first.

Run:
```bash
streamlit run web.py --server.port 1111
```