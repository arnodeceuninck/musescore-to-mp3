"""Command-line interface for musescore-to-mp3."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .converter import MuseScoreConverter
from .exceptions import MuseScoreConverterError


def parse_args(args: Optional[list] = None) -> argparse.Namespace:
    """Parse command-line arguments.
    
    Args:
        args: Optional list of arguments (for testing)
        
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        prog="musescore-to-mp3",
        description="Convert MuseScore files to MP3 with optional voice highlighting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.mscz
  %(prog)s --voice-group bass input.mscz
  %(prog)s --voice-group baritone --output my_output.mp3 input.mscz
  %(prog)s --voice-group tenor --volume-boost 20 input.mscz
  %(prog)s --all-voices input.mscz
  %(prog)s --all-voices --output my_voices_dir input.mscz
        """,
    )
    
    parser.add_argument(
        "input_file",
        type=str,
        help="Input MuseScore file (.mscz)",
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Output MP3 file path (default: <input>_output.mp3)",
    )
    
    parser.add_argument(
        "-v", "--voice-group",
        type=str,
        help="Voice group to highlight (e.g., bass, baritone, tenor, soprano)",
    )
    
    parser.add_argument(
        "--all-voices",
        action="store_true",
        help="Export MP3s for all voice parts in the score (one file per voice)",
    )
    
    parser.add_argument(
        "--volume-boost",
        type=int,
        default=12,
        help="Volume boost for the highlighted voice in dB (default: 12)",
    )
    
    parser.add_argument(
        "--master-volume",
        type=int,
        default=60,
        help="Master volume percentage for non-highlighted parts (default: 60)",
    )
    
    parser.add_argument(
        "--musescore-path",
        type=str,
        default="MuseScore4",
        help="Path to MuseScore executable (default: MuseScore4)",
    )
    
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep temporary modified .mscz file for debugging",
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0",
    )
    
    return parser.parse_args(args)


def main(args: Optional[list] = None) -> int:
    """Main entry point for the CLI.
    
    Args:
        args: Optional list of arguments (for testing)
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parsed_args = parse_args(args)
    
    # Validate input file
    input_path = Path(parsed_args.input_file)
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' does not exist", file=sys.stderr)
        return 1
    
    if not input_path.suffix.lower() == ".mscz":
        print(f"Error: Input file must be a .mscz file", file=sys.stderr)
        return 1
    
    # Validate arguments
    if parsed_args.all_voices and parsed_args.voice_group:
        print(f"Error: Cannot use both --all-voices and --voice-group", file=sys.stderr)
        return 1
    
    # Determine output file path or directory
    if parsed_args.all_voices:
        # For all-voices, output is a directory
        if parsed_args.output:
            output_path = Path(parsed_args.output)
        else:
            output_path = input_path.parent / f"{input_path.stem}_voices"
    else:
        # For single voice or plain conversion, output is a file
        if parsed_args.output:
            output_path = Path(parsed_args.output)
        else:
            output_path = input_path.with_name(f"{input_path.stem}_output.mp3")
    
    try:
        # Create converter instance
        converter = MuseScoreConverter(
            musescore_executable=parsed_args.musescore_path,
            keep_temp_files=parsed_args.keep_temp,
        )
        
        # Convert file
        if parsed_args.all_voices:
            # Export all voice parts
            print(f"Converting all voice parts from '{input_path}'...")
            print(f"Output directory: '{output_path}'\n")
            
            generated_files = converter.convert_all_voices(
                input_file=input_path,
                output_dir=output_path,
                voice_volume_boost=parsed_args.volume_boost,
                master_volume=parsed_args.master_volume,
            )
            
            print(f"\n✓ Successfully created {len(generated_files)} MP3 file(s) in '{output_path}'")
            
        elif parsed_args.voice_group:
            # Export single voice with highlighting
            print(f"Converting '{input_path}' to '{output_path}'...")
            print(f"Highlighting voice group: {parsed_args.voice_group}")
            
            converter.convert_with_voice_highlight(
                input_file=input_path,
                output_file=output_path,
                voice_group=parsed_args.voice_group,
                voice_volume_boost=parsed_args.volume_boost,
                master_volume=parsed_args.master_volume,
            )
            
            print(f"✓ Successfully created '{output_path}'")
            
        else:
            # Plain conversion
            print(f"Converting '{input_path}' to '{output_path}'...")
            
            converter.convert(
                input_file=input_path,
                output_file=output_path,
            )
            
            print(f"✓ Successfully created '{output_path}'")
        
        return 0
        
    except MuseScoreConverterError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
