# musescore-to-mp3

A command-line tool for converting MuseScore files to MP3 with optional voice highlighting.

## Installation

Requires MuseScore 4 or 3 to be installed on your system.

The tool will automatically find MuseScore in common installation locations:
- Windows: `C:\Program Files\MuseScore 4\bin\MuseScore4.exe` (and MuseScore 3)
- macOS: `/Applications/MuseScore 4.app/Contents/MacOS/mscore`
- Linux: `/usr/bin/musescore4`, `/usr/bin/musescore3`, etc.

```bash
pip install -e .
```

## Usage

Basic conversion:
```bash
python -m musescore_to_mp3.cli input.mscz
```

With voice highlighting:
```bash
python -m musescore_to_mp3.cli --voice-group bass input.mscz
```

All options:
```bash
python -m musescore_to_mp3.cli --help
```

**Note:** If the `musescore-to-mp3` command is not found in your PATH after installation, use `python -m musescore_to_mp3.cli` instead.

## Features

- Convert `.mscz` files to MP3
- Highlight specific voice parts (soprano, alto, tenor, baritone, bass)
- Support for sub-voice groups (soprano1, soprano2, alto1, alto2, tenor1, tenor2, bass1, bass2)
- Automatically replaces voice with matching saxophone:
  - Soprano → Soprano Saxophone
  - Alto → Alto Saxophone
  - Tenor → Tenor Saxophone
  - Baritone/Bass → Baritone Saxophone
- Adjust volume levels
- Smart voice detection with fuzzy matching

## Options

```
positional arguments:
  input_file            Input MuseScore file (.mscz)

optional arguments:
  -o, --output          Output MP3 file path
  -v, --voice-group     Voice group to highlight
  --volume-boost        Volume boost in dB (default: 10)
  --master-volume       Master volume % for other parts (default: 80)
  --musescore-path      Path to MuseScore executable
  --keep-temp           Keep temporary files for debugging
```