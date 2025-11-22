"""Utilities for extracting and modifying .mscz files."""

import zipfile
import tempfile
import shutil
import json
from pathlib import Path
from typing import Optional
import xml.etree.ElementTree as ET

from .exceptions import InvalidMSCZFileError, XMLModificationError


class MSCZFile:
    """Handler for MuseScore .mscz files (ZIP archives containing XML)."""
    
    def __init__(self, file_path: Path):
        """Initialize MSCZ file handler.
        
        Args:
            file_path: Path to the .mscz file
            
        Raises:
            InvalidMSCZFileError: If the file is not a valid .mscz file
        """
        self.file_path = file_path
        self.temp_dir: Optional[Path] = None
        self._validate()
    
    def _validate(self) -> None:
        """Validate that the file is a valid .mscz file.
        
        Raises:
            InvalidMSCZFileError: If the file is not a valid .mscz file
        """
        if not zipfile.is_zipfile(self.file_path):
            raise InvalidMSCZFileError(f"'{self.file_path}' is not a valid .mscz file")
    
    def extract(self) -> Path:
        """Extract the .mscz file to a temporary directory.
        
        Returns:
            Path to the temporary directory
            
        Raises:
            InvalidMSCZFileError: If extraction fails
        """
        try:
            self.temp_dir = Path(tempfile.mkdtemp(prefix="mscz_"))
            
            with zipfile.ZipFile(self.file_path, 'r') as zip_ref:
                zip_ref.extractall(self.temp_dir)
            
            return self.temp_dir
            
        except Exception as e:
            if self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            raise InvalidMSCZFileError(f"Failed to extract .mscz file: {e}")
    
    def get_score_xml_path(self) -> Optional[Path]:
        """Get the path to the main score XML file.
        
        Returns:
            Path to the score XML file, or None if not found
        """
        if not self.temp_dir:
            return None
        
        # Try common locations for the score file
        possible_paths = [
            self.temp_dir / "score.mscx",
            self.temp_dir / f"{self.file_path.stem}.mscx",
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        # Search for any .mscx file
        mscx_files = list(self.temp_dir.glob("*.mscx"))
        if mscx_files:
            return mscx_files[0]
        
        return None
    
    def parse_xml(self) -> ET.ElementTree:
        """Parse the score XML file.
        
        Returns:
            ElementTree object
            
        Raises:
            XMLModificationError: If parsing fails
        """
        xml_path = self.get_score_xml_path()
        if not xml_path:
            raise XMLModificationError("Could not find score XML file in .mscz archive")
        
        try:
            return ET.parse(xml_path)
        except ET.ParseError as e:
            raise XMLModificationError(f"Failed to parse XML: {e}")
    
    def save_xml(self, tree: ET.ElementTree) -> None:
        """Save the modified XML back to the file.
        
        Args:
            tree: ElementTree to save
            
        Raises:
            XMLModificationError: If saving fails
        """
        xml_path = self.get_score_xml_path()
        if not xml_path:
            raise XMLModificationError("Could not find score XML file to save")
        
        try:
            tree.write(xml_path, encoding="utf-8", xml_declaration=True)
        except Exception as e:
            raise XMLModificationError(f"Failed to save XML: {e}")
    
    def remove_audiosettings(self) -> None:
        """Remove the audiosettings.json file if it exists.
        
        This ensures that MuseScore uses the instrument settings from the .mscx file
        instead of cached mixer settings that might have incorrect presets.
        
        DEPRECATED: Use update_audiosettings() instead.
        """
        if not self.temp_dir:
            return
        
        audiosettings_path = self.temp_dir / "audiosettings.json"
        if audiosettings_path.exists():
            audiosettings_path.unlink()
    
    def update_audiosettings(self) -> None:
        """Update the audiosettings.json file to use MS Basic without specific presets.
        
        This removes preset information (presetBank, presetName, presetProgram) from
        tracks, allowing MuseScore to use the instrument definitions from the .mscx file
        while keeping the MS Basic soundfont setting.
        """
        if not self.temp_dir:
            return
        
        audiosettings_path = self.temp_dir / "audiosettings.json"
        if not audiosettings_path.exists():
            return
        
        try:
            # Load the JSON file
            with open(audiosettings_path, 'r', encoding='utf-8') as f:
                audio_settings = json.load(f)
            
            # Update each track to remove preset information
            if 'tracks' in audio_settings:
                for track in audio_settings['tracks']:
                    if 'in' in track and 'resourceMeta' in track['in']:
                        resource_meta = track['in']['resourceMeta']
                        
                        # Update attributes to only keep MS Basic soundfont
                        if 'attributes' in resource_meta:
                            attributes = resource_meta['attributes']
                            
                            # Remove preset-specific attributes
                            attributes.pop('presetBank', None)
                            attributes.pop('presetName', None)
                            attributes.pop('presetProgram', None)
                            
                            # Ensure soundFontName is set to MS Basic
                            if 'soundFontName' not in attributes:
                                attributes['soundFontName'] = 'MS Basic'
                        
                        # Update the id to just be "MS Basic" without preset info
                        if resource_meta.get('id', '').startswith('MS Basic\\'):
                            resource_meta['id'] = 'MS Basic'
            
            # Save the updated JSON file
            with open(audiosettings_path, 'w', encoding='utf-8') as f:
                json.dump(audio_settings, f, indent=4)
                
        except Exception as e:
            # If we fail to update, just remove the file as fallback
            if audiosettings_path.exists():
                audiosettings_path.unlink()
    
    def create_modified_mscz(self, output_path: Path) -> None:
        """Create a new .mscz file from the modified contents.
        
        Args:
            output_path: Path where the new .mscz file should be created
            
        Raises:
            InvalidMSCZFileError: If creation fails
        """
        if not self.temp_dir:
            raise InvalidMSCZFileError("No extracted files to create .mscz from")
        
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
                for file_path in self.temp_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(self.temp_dir)
                        zip_ref.write(file_path, arcname)
        except Exception as e:
            raise InvalidMSCZFileError(f"Failed to create modified .mscz file: {e}")
    
    def cleanup(self) -> None:
        """Clean up temporary files."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            self.temp_dir = None
    
    def __enter__(self):
        """Context manager entry."""
        self.extract()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
