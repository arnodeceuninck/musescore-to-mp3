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

Export all voice parts (one MP3 per voice):
```bash
python -m musescore_to_mp3.cli --all-voices input.mscz
```

All options:
```bash
python -m musescore_to_mp3.cli --help
```

**Note:** If the `musescore-to-mp3` command is not found in your PATH after installation, use `python -m musescore_to_mp3.cli` instead.

## Features

- Convert `.mscz` files to MP3
- **Export all voice parts**: Generate separate MP3 files for each voice in the score with a single command
- Highlight specific voice parts (soprano, alto, tenor, baritone, bass)
- Support for sub-voice groups (soprano1, soprano2, alto1, alto2, tenor1, tenor2, bass1, bass2)
- Automatically replaces voice with matching saxophone:
  - Soprano → Soprano Saxophone
  - Alto → Alto Saxophone
  - Tenor → Tenor Saxophone
  - Baritone/Bass → Baritone Saxophone
- Adjust volume levels
- Smart voice detection with fuzzy matching
- Organized output with numbered files for batch exports

## Options

```
positional arguments:
  input_file            Input MuseScore file (.mscz)

optional arguments:
  -o, --output          Output MP3 file path (or directory for --all-voices)
  -v, --voice-group     Voice group to highlight
  --all-voices          Export MP3s for all voice parts (one file per voice)
  --volume-boost        Volume boost in dB (default: 12)
  --master-volume       Master volume % for other parts (default: 60)
  --musescore-path      Path to MuseScore executable
  --keep-temp           Keep temporary files for debugging
```

### Examples

**Basic conversion:**
```bash
python -m musescore_to_mp3.cli input.mscz
# Output: input_output.mp3
```

**Single voice highlighting:**
```bash
python -m musescore_to_mp3.cli --voice-group bass input.mscz
# Output: input_output.mp3 (with bass highlighted)
```

**Export all voices:**
```bash
python -m musescore_to_mp3.cli --all-voices input.mscz
# Output directory: input_voices/
#   input_01_Soprano.mp3
#   input_02_Alto.mp3
#   input_03_Tenor.mp3
#   input_04_Bass.mp3
```

**Export all voices to custom directory:**
```bash
python -m musescore_to_mp3.cli --all-voices --output my_parts input.mscz
# Output directory: my_parts/
```

**Adjust volume settings:**
```bash
python -m musescore_to_mp3.cli --voice-group tenor --volume-boost 20 --master-volume 50 input.mscz
# Higher boost for highlighted voice, quieter background
```