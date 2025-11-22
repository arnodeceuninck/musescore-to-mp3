"""Main converter module for MuseScore to MP3 conversion."""

import subprocess
import shutil
from pathlib import Path
from typing import Optional
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
                )
                
                # Save modified XML
                mscz.save_xml(tree)
                
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
