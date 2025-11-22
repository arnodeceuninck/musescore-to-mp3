# Instrument Configuration Files

This directory contains YAML configuration files that define how voice parts are mapped to different instruments in MuseScore.

## Files

### `choir_instruments.yaml`
Defines the mapping from voice groups (soprano, alto, tenor, bass, etc.) to MuseScore choir voice instruments. These are used when converting non-highlighted voice parts to choir instruments.

### `voice_highlight.yaml`
Defines the mapping from voice groups to highlight instruments. These are used when highlighting a specific voice part (the highlighted part is replaced with the instrument defined here). By default, saxophones are used, but you can configure any instrument you prefer.

## Configuration Format

Each YAML file contains voice group names as keys, with instrument properties as values:

```yaml
soprano:
  id: soprano                      # Instrument ID
  instrumentId: voice.soprano      # MuseScore instrument ID
  longName: Soprano                # Full instrument name
  shortName: S.                    # Abbreviated name
  minPitchP: "60"                  # Minimum pitch (professional)
  maxPitchP: "84"                  # Maximum pitch (professional)
  minPitchA: "60"                  # Minimum pitch (amateur)
  maxPitchA: "79"                  # Maximum pitch (amateur)
  clef: G8vb                       # Optional: Clef specification
  program: "64"                    # Optional: MIDI program number (for saxophones)
  transposeDiatonic: "-1"          # Optional: Diatonic transposition
  transposeChromatic: "-2"         # Optional: Chromatic transposition
```

## Supported Voice Groups

The following voice groups are recognized:
- `soprano`, `soprano1`, `soprano2`
- `alto`, `alto1`, `alto2`
- `tenor`, `tenor1`, `tenor2`
- `bass`, `bass1`, `bass2`
- `baritone`, `baritone1`, `baritone2`

## Editing Configurations

You can edit these YAML files to:
- Add new voice group mappings
- Change instrument properties (pitch ranges, names, etc.)
- Modify MIDI program numbers for different sounds (e.g., use clarinet instead of saxophone for highlighting)
- Adjust transposition settings

After editing, the changes will be automatically loaded the next time the application runs.

## MIDI Pitch Numbers

Pitch numbers use MIDI note numbering where:
- Middle C (C4) = 60
- A4 (440 Hz) = 69
- Each semitone = +1

## MIDI Program Numbers

Common MIDI program numbers used in this project:
- 52: Choir Aahs (used for choir instruments)
- 64: Soprano Saxophone
- 65: Alto Saxophone
- 66: Tenor Saxophone
- 67: Baritone Saxophone
