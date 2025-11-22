"""Main converter module for MuseScore to MP3 conversion."""

import subprocess
import shutil
from pathlib import Path
from typing import Optional, List
import tempfile
import platform

from .exceptions import (
    MuseScoreNotFoundError,
    MuseScoreExecutionError,
    InvalidMSCZFileError,
)
from .mscz_handler import MSCZFile
from .xml_modifier import XMLModifier


class MuseScoreConverter:
    """Handles conversion of MuseScore files to MP3."""
    
    # Common MuseScore installation paths
    MUSESCORE_FALLBACK_PATHS = {
        "Windows": [
            r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe",
            r"C:\Program Files (x86)\MuseScore 4\bin\MuseScore4.exe",
            r"C:\Program Files\MuseScore 3\bin\MuseScore3.exe",
            r"C:\Program Files (x86)\MuseScore 3\bin\MuseScore3.exe",
        ],
        "Darwin": [  # macOS
            "/Applications/MuseScore 4.app/Contents/MacOS/mscore",
            "/Applications/MuseScore 3.app/Contents/MacOS/mscore",
        ],
        "Linux": [
            "/usr/bin/musescore4",
            "/usr/bin/musescore3",
            "/usr/bin/musescore",
            "/usr/local/bin/musescore4",
            "/usr/local/bin/musescore3",
        ],
    }
    
    def __init__(
        self,
        musescore_executable: str = "MuseScore4",
        keep_temp_files: bool = False,
    ):
        """Initialize the converter.
        
        Args:
            musescore_executable: Path or name of the MuseScore executable
            keep_temp_files: Whether to keep temporary files for debugging
            
        Raises:
            MuseScoreNotFoundError: If MuseScore executable is not found
        """
        self.musescore_executable = self._find_musescore_executable(musescore_executable)
        self.keep_temp_files = keep_temp_files
    
    def _find_musescore_executable(self, preferred_executable: str) -> str:
        """Find the MuseScore executable, trying fallback paths if needed.
        
        Args:
            preferred_executable: The preferred executable name or path
            
        Returns:
            Path to the MuseScore executable
            
        Raises:
            MuseScoreNotFoundError: If MuseScore is not found
        """
        # First try the preferred executable in PATH
        if shutil.which(preferred_executable):
            return preferred_executable
        
        # If it's an absolute path, check if it exists
        if Path(preferred_executable).is_absolute() and Path(preferred_executable).exists():
            return preferred_executable
        
        # Try common alternatives in PATH
        for alt in ["MuseScore4", "MuseScore3", "musescore4", "musescore3", "musescore"]:
            if shutil.which(alt):
                print(f"Info: Using '{alt}' ('{preferred_executable}' not found in PATH)")
                return alt
        
        # Try platform-specific fallback paths
        system = platform.system()
        fallback_paths = self.MUSESCORE_FALLBACK_PATHS.get(system, [])
        
        for path in fallback_paths:
            if Path(path).exists():
                print(f"Info: Using MuseScore at '{path}'")
                return path
        
        # Not found anywhere
        raise MuseScoreNotFoundError(
            f"MuseScore executable '{preferred_executable}' not found. "
            f"Please install MuseScore 4 or 3, or specify the correct path with --musescore-path. "
            f"Tried: {preferred_executable}, PATH alternatives, and common installation locations."
        )
    
    def convert(
        self,
        input_file: Path,
        output_file: Path,
    ) -> None:
        """Convert a MuseScore file to MP3.
        
        Args:
            input_file: Path to the input .mscz file
            output_file: Path to the output .mp3 file
            
        Raises:
            MuseScoreExecutionError: If conversion fails
        """
        self._export_to_mp3(input_file, output_file)
    
    def convert_with_voice_highlight(
        self,
        input_file: Path,
        output_file: Path,
        voice_group: str,
        voice_volume_boost: int = 10,
        master_volume: int = 80,
        use_choir: bool = False,
    ) -> None:
        """Convert a MuseScore file to MP3 with voice highlighting.
        
        This method:
        1. Extracts the .mscz file
        2. Modifies the XML to highlight the specified voice with appropriate saxophone
        3. Creates a modified .mscz file
        4. Exports to MP3
        5. Cleans up temporary files
        
        Args:
            input_file: Path to the input .mscz file
            output_file: Path to the output .mp3 file
            voice_group: Voice group to highlight (e.g., "bass", "baritone")
            voice_volume_boost: Volume boost for the voice in dB
            master_volume: Master volume percentage for other parts
            use_choir: If True, convert non-highlighted voice parts to choir instruments
            
        Raises:
            InvalidMSCZFileError: If the input file is invalid
            VoiceNotFoundError: If the voice group is not found
            XMLModificationError: If XML modification fails
            MuseScoreExecutionError: If conversion fails
        """
        temp_mscz = None
        
        try:
            # Extract and modify the .mscz file
            with MSCZFile(input_file) as mscz:
                # Parse XML
                tree = mscz.parse_xml()
                
                # Modify the voice part
                XMLModifier.modify_voice_part(
                    tree=tree,
                    voice_group=voice_group,
                    voice_volume_boost=voice_volume_boost,
                    master_volume=master_volume,
                    use_choir=use_choir,
                )
                
                # Save modified XML
                mscz.save_xml(tree)
                
                # Update audiosettings.json to use MS Basic without presets
                mscz.update_audiosettings()
                
                # Create modified .mscz file
                temp_mscz = Path(tempfile.mktemp(suffix=".mscz", prefix="modified_"))
                mscz.create_modified_mscz(temp_mscz)
            
            # Export the modified file to MP3
            self._export_to_mp3(temp_mscz, output_file)
            
        finally:
            # Clean up temporary file unless keep_temp_files is True
            if temp_mscz and temp_mscz.exists():
                if self.keep_temp_files:
                    print(f"Temporary file kept: {temp_mscz}")
                else:
                    temp_mscz.unlink()
    
    def convert_all_voices(
        self,
        input_file: Path,
        output_dir: Optional[Path] = None,
        voice_volume_boost: int = 10,
        master_volume: int = 80,
        use_choir: bool = False,
    ) -> List[Path]:
        """Convert a MuseScore file to multiple MP3s, one for each voice part.
        
        This method:
        1. Extracts the .mscz file
        2. Identifies all voice parts in the score
        3. Creates a modified version for each voice part
        4. Exports each to MP3 in an organized directory structure
        5. Cleans up temporary files
        
        Args:
            input_file: Path to the input .mscz file
            output_dir: Directory to save MP3s (default: <input_stem>_voices/)
            voice_volume_boost: Volume boost for the voice in dB
            master_volume: Master volume percentage for other parts
            use_choir: If True, convert non-highlighted voice parts to choir instruments
            
        Returns:
            List of paths to the generated MP3 files
            
        Raises:
            InvalidMSCZFileError: If the input file is invalid
            XMLModificationError: If XML modification fails
            MuseScoreExecutionError: If conversion fails
        """
        # Determine output directory
        if output_dir is None:
            output_dir = input_file.parent / f"{input_file.stem}_voices"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get all voice parts from the score
        with MSCZFile(input_file) as mscz:
            tree = mscz.parse_xml()
            parts = XMLModifier.get_all_parts(tree)
        
        if not parts:
            raise InvalidMSCZFileError("No voice parts found in the score")
        
        print(f"Found {len(parts)} voice part(s) in '{input_file.name}':")
        for _, part_name in parts:
            print(f"  - {part_name}")
        
        # Generate MP3 for each voice part
        generated_files = []
        base_name = input_file.stem
        
        # First, create a regular MP3 without any highlighting
        print(f"\n[0/{len(parts)}] Creating regular MP3 (no voice highlighting)...")
        regular_output = output_dir / f"{base_name}_all.mp3"
        
        try:
            self.convert(
                input_file=input_file,
                output_file=regular_output,
            )
            generated_files.append(regular_output)
            print(f"  ✓ Created '{regular_output.name}'")
        except Exception as e:
            print(f"  ✗ Failed to create regular MP3: {e}")
        
        # Now generate MP3 for each voice part with highlighting
        for i, (part_element, part_name) in enumerate(parts, 1):
            # Create a safe filename from the part name
            safe_name = self._sanitize_filename(part_name)
            output_file = output_dir / f"{base_name}_{i:02d}_{safe_name}.mp3"
            
            print(f"\n[{i}/{len(parts)}] Processing '{part_name}'...")
            
            try:
                # Convert with this voice highlighted
                self.convert_with_voice_highlight(
                    input_file=input_file,
                    output_file=output_file,
                    voice_group=part_name,
                    voice_volume_boost=voice_volume_boost,
                    master_volume=master_volume,
                    use_choir=use_choir,
                )
                
                generated_files.append(output_file)
                print(f"  ✓ Created '{output_file.name}'")
                
            except Exception as e:
                print(f"  ✗ Failed to process '{part_name}': {e}")
                continue
        
        return generated_files
    
    def convert_directory(
        self,
        input_dir: Path,
        output_dir: Optional[Path] = None,
        voice_group: Optional[str] = None,
        all_voices: bool = False,
        voice_volume_boost: int = 10,
        master_volume: int = 80,
        use_choir: bool = False,
    ) -> dict:
        """Convert all MuseScore files in a directory to MP3.
        
        Args:
            input_dir: Directory containing .mscz files
            output_dir: Directory to save MP3s (default: same as input_dir)
            voice_group: Voice group to highlight (if specified)
            all_voices: If True, export all voice parts for each file
            voice_volume_boost: Volume boost for the voice in dB
            master_volume: Master volume percentage for other parts
            use_choir: If True, convert non-highlighted voice parts to choir instruments
            
        Returns:
            Dictionary mapping input files to their output files/directories
            
        Raises:
            FileNotFoundError: If the directory doesn't exist
        """
        if not input_dir.is_dir():
            raise FileNotFoundError(f"Directory not found: {input_dir}")
        
        # Find all .mscz files in the directory
        mscz_files = sorted(input_dir.glob("*.mscz"))
        
        if not mscz_files:
            print(f"No .mscz files found in '{input_dir}'")
            return {}
        
        print(f"Found {len(mscz_files)} .mscz file(s) in '{input_dir}':")
        for mscz_file in mscz_files:
            print(f"  - {mscz_file.name}")
        
        # Use input directory as output directory if not specified
        if output_dir is None:
            output_dir = input_dir
        
        results = {}
        
        # Process each file
        for i, mscz_file in enumerate(mscz_files, 1):
            print(f"\n{'='*60}")
            print(f"Processing file {i}/{len(mscz_files)}: {mscz_file.name}")
            print(f"{'='*60}")
            
            try:
                if all_voices:
                    # Export all voices for this file
                    file_output_dir = output_dir / f"{mscz_file.stem}_voices"
                    generated_files = self.convert_all_voices(
                        input_file=mscz_file,
                        output_dir=file_output_dir,
                        voice_volume_boost=voice_volume_boost,
                        master_volume=master_volume,
                        use_choir=use_choir,
                    )
                    results[mscz_file] = file_output_dir
                    print(f"✓ Exported {len(generated_files)} file(s) to '{file_output_dir}'")
                    
                elif voice_group:
                    # Export with specific voice highlighted
                    output_file = output_dir / f"{mscz_file.stem}_output.mp3"
                    self.convert_with_voice_highlight(
                        input_file=mscz_file,
                        output_file=output_file,
                        voice_group=voice_group,
                        voice_volume_boost=voice_volume_boost,
                        master_volume=master_volume,
                        use_choir=use_choir,
                    )
                    results[mscz_file] = output_file
                    print(f"✓ Created '{output_file.name}'")
                    
                else:
                    # Plain conversion
                    output_file = output_dir / f"{mscz_file.stem}_output.mp3"
                    self.convert(
                        input_file=mscz_file,
                        output_file=output_file,
                    )
                    results[mscz_file] = output_file
                    print(f"✓ Created '{output_file.name}'")
                    
            except Exception as e:
                print(f"✗ Failed to process '{mscz_file.name}': {e}")
                results[mscz_file] = None
                continue
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"SUMMARY: Processed {len(mscz_files)} file(s)")
        successful = sum(1 for v in results.values() if v is not None)
        print(f"  ✓ Successful: {successful}")
        print(f"  ✗ Failed: {len(mscz_files) - successful}")
        print(f"{'='*60}")
        
        return results
    
    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Sanitize a filename by removing or replacing invalid characters.
        
        Args:
            filename: The filename to sanitize
            
        Returns:
            Sanitized filename safe for use on all platforms
        """
        # Replace invalid characters with underscores
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Replace multiple spaces with single space
        filename = ' '.join(filename.split())
        
        # Remove leading/trailing spaces and dots
        filename = filename.strip(' .')
        
        # Limit length
        if len(filename) > 100:
            filename = filename[:100]
        
        return filename or "unnamed"
    
    def _export_to_mp3(self, input_file: Path, output_file: Path) -> None:
        """Export a MuseScore file to MP3 using the MuseScore executable.
        
        Args:
            input_file: Path to the .mscz file to export
            output_file: Path to the output .mp3 file
            
        Raises:
            MuseScoreExecutionError: If export fails
        """
        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Build the command
        cmd = [
            self.musescore_executable,
            "--export-to",
            str(output_file),
            str(input_file),
        ]
        
        try:
            # Run MuseScore
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown error"
                raise MuseScoreExecutionError(
                    f"MuseScore export failed: {error_msg}"
                )
            
            # Verify output file was created
            if not output_file.exists():
                raise MuseScoreExecutionError(
                    "MuseScore did not create the output file"
                )
                
        except subprocess.TimeoutExpired:
            raise MuseScoreExecutionError(
                "MuseScore export timed out (>5 minutes)"
            )
        except FileNotFoundError:
            raise MuseScoreNotFoundError(
                f"Could not execute '{self.musescore_executable}'"
            )
        except Exception as e:
            if isinstance(e, MuseScoreExecutionError):
                raise
            raise MuseScoreExecutionError(f"Unexpected error during export: {e}")
