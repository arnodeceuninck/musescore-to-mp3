"""XML modification utilities for MuseScore files."""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List
import yaml

from .exceptions import XMLModificationError
from .voice_matcher import VoiceMatcher


class XMLModifier:
    """Handles modification of MuseScore XML."""
    
    # Class variables to cache loaded configurations
    _VOICE_TO_CHOIR: Dict[str, dict] = None
    _VOICE_HIGHLIGHT: Dict[str, dict] = None
    
    @classmethod
    def _load_config(cls, config_name: str) -> Dict[str, dict]:
        """Load a configuration file from the config directory.
        
        Args:
            config_name: Name of the config file (without .yaml extension)
            
        Returns:
            Dictionary loaded from the YAML file
        """
        config_dir = Path(__file__).parent / "config"
        config_file = config_dir / f"{config_name}.yaml"
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise XMLModificationError(f"Configuration file not found: {config_file}")
        except yaml.YAMLError as e:
            raise XMLModificationError(f"Error parsing configuration file {config_file}: {e}")
    
    @classmethod
    def get_voice_to_choir(cls) -> Dict[str, dict]:
        """Lazy-load and return the choir instrument configuration."""
        if cls._VOICE_TO_CHOIR is None:
            cls._VOICE_TO_CHOIR = cls._load_config("choir_instruments")
        return cls._VOICE_TO_CHOIR
    
    @classmethod
    def get_voice_highlight_config(cls) -> Dict[str, dict]:
        """Lazy-load and return the voice highlight instrument configuration."""
        if cls._VOICE_HIGHLIGHT is None:
            cls._VOICE_HIGHLIGHT = cls._load_config("voice_highlight")
        return cls._VOICE_HIGHLIGHT
    
    @staticmethod
    def modify_voice_part(
        tree: ET.ElementTree,
        voice_group: str,
        replacement_instrument: str = "Baritone Saxophone",
        voice_volume_boost: int = 10,
        master_volume: int = 80,
        use_choir: bool = False,
    ) -> None:
        """Modify a voice part to stand out.
        
        This function:
        1. Finds the specified voice part
        2. Replaces its instrument
        3. Boosts its volume
        4. Reduces the master volume for other parts
        5. Optionally converts non-highlighted voice parts to choir instruments
        
        Args:
            tree: The MuseScore XML tree
            voice_group: The voice group to modify
            replacement_instrument: Instrument name to replace with
            voice_volume_boost: Volume boost for the voice in dB
            master_volume: Master volume percentage for other parts
            use_choir: If True, convert other voice parts to choir instruments
            
        Raises:
            VoiceNotFoundError: If the voice group is not found
            XMLModificationError: If modification fails
        """
        # Find the target part
        target_part, matched_name = VoiceMatcher.find_part(tree, voice_group)
        
        try:
            # Get the appropriate highlight instrument for this voice group
            voice_normalized = voice_group.lower().replace(" ", "")
            highlight_config = XMLModifier.get_voice_highlight_config()
            instrument_config = highlight_config.get(
                voice_normalized,
                highlight_config["bass"]  # Default to baritone sax
            )
            
            # Modify the instrument
            XMLModifier._replace_instrument(target_part, instrument_config)
            
            # Boost the voice volume
            XMLModifier._set_part_volume(target_part, 100 + voice_volume_boost)
            
            # Reduce master volume for all other parts
            XMLModifier._set_other_parts_volume(tree, target_part, master_volume)
            
            # If use_choir is True, convert other voice parts to choir instruments
            if use_choir:
                XMLModifier._convert_other_parts_to_choir(tree, target_part)
            
        except Exception as e:
            raise XMLModificationError(f"Failed to modify voice part: {e}")
    
    @staticmethod
    def _replace_instrument(part: ET.Element, instrument_config: dict) -> None:
        """Replace the instrument for a part with a highlight instrument.
        
        Args:
            part: The Part element to modify
            instrument_config: Dictionary with all instrument properties
        """
        # Find the Instrument element
        instrument = part.find(".//Instrument")
        
        if instrument is None:
            # Create one if it doesn't exist
            staff = part.find(".//Staff")
            if staff is None:
                raise XMLModificationError("Cannot find Staff element in part")
            instrument = ET.SubElement(staff, "Instrument")
        
        # Set the id attribute (e.g., "soprano-saxophone")
        instrument.set("id", instrument_config["id"])
        
        # Update or create instrument name elements
        XMLModifier._set_or_create_element(instrument, "longName", instrument_config["longName"])
        XMLModifier._set_or_create_element(instrument, "shortName", instrument_config["shortName"])
        XMLModifier._set_or_create_element(instrument, "trackName", instrument_config["longName"])
        
        # Set pitch ranges
        XMLModifier._set_or_create_element(instrument, "minPitchP", instrument_config["minPitchP"])
        XMLModifier._set_or_create_element(instrument, "maxPitchP", instrument_config["maxPitchP"])
        XMLModifier._set_or_create_element(instrument, "minPitchA", instrument_config["minPitchA"])
        XMLModifier._set_or_create_element(instrument, "maxPitchA", instrument_config["maxPitchA"])
        
        # Set transposition
        XMLModifier._set_or_create_element(instrument, "transposeDiatonic", instrument_config["transposeDiatonic"])
        XMLModifier._set_or_create_element(instrument, "transposeChromatic", instrument_config["transposeChromatic"])
        
        # Set instrument ID (critical for MuseScore to recognize the instrument)
        XMLModifier._set_or_create_element(instrument, "instrumentId", instrument_config["instrumentId"])
        
        # Set MIDI program (General MIDI instrument number)
        channel = instrument.find(".//Channel")
        if channel is None:
            channel = ET.SubElement(instrument, "Channel")
        
        program = channel.find("program")
        if program is None:
            program = ET.SubElement(channel, "program")
        program.set("value", instrument_config["program"])
        
        # Ensure synti is set
        synti = channel.find("synti")
        if synti is None:
            synti = ET.SubElement(channel, "synti")
            synti.text = "Fluid"
    
    @staticmethod
    def _set_part_volume(part: ET.Element, volume: int) -> None:
        """Set the volume for a part.
        
        Args:
            part: The Part element
            volume: Volume level (0-127, or percentage-based)
        """
        # Ensure volume is in valid range
        volume = max(0, min(127, volume))
        
        # Find or create Channel element
        instrument = part.find(".//Instrument")
        if instrument is None:
            return
        
        channel = instrument.find(".//Channel")
        if channel is None:
            channel = ET.SubElement(instrument, "Channel")
        
        # Find or create controller for volume (CC 7)
        volume_controller = None
        for controller in channel.findall(".//controller"):
            ctrl_attr = controller.get("ctrl")
            if ctrl_attr == "7":
                volume_controller = controller
                break
        
        if volume_controller is None:
            volume_controller = ET.SubElement(channel, "controller")
            volume_controller.set("ctrl", "7")
        
        volume_controller.set("value", str(volume))
    
    @staticmethod
    def _set_other_parts_volume(
        tree: ET.ElementTree, 
        target_part: ET.Element, 
        volume: int
    ) -> None:
        """Set volume for all parts except the target part.
        
        Args:
            tree: The MuseScore XML tree
            target_part: The part to exclude
            volume: Volume level for other parts
        """
        root = tree.getroot()
        
        for part in root.findall(".//Part"):
            if part is not target_part:
                XMLModifier._set_part_volume(part, volume)
    
    @staticmethod
    def _set_or_create_element(parent: ET.Element, tag: str, text: str) -> ET.Element:
        """Set text for an element, creating it if it doesn't exist.
        
        Args:
            parent: Parent element
            tag: Tag name for the element
            text: Text content
            
        Returns:
            The element
        """
        element = parent.find(tag)
        if element is None:
            element = ET.SubElement(parent, tag)
        element.text = text
        return element
    
    @staticmethod
    def get_part_names(tree: ET.ElementTree) -> List[str]:
        """Get all part names from the score.
        
        Args:
            tree: The MuseScore XML tree
            
        Returns:
            List of part names
        """
        parts = VoiceMatcher._get_all_parts(tree)
        return [name for _, name in parts]
    
    @staticmethod
    def get_all_parts(tree: ET.ElementTree) -> List[tuple]:
        """Get all parts with their elements and names from the score.
        
        Args:
            tree: The MuseScore XML tree
            
        Returns:
            List of (part_element, part_name) tuples
        """
        return VoiceMatcher._get_all_parts(tree)
    
    @staticmethod
    def _convert_other_parts_to_choir(tree: ET.ElementTree, target_part: ET.Element) -> None:
        """Convert all voice parts (except the target) to choir instruments.
        
        This replaces parts that might be using non-standard instruments (e.g., clarinet)
        with proper choir voice instruments to ensure better sound quality.
        
        Args:
            tree: The MuseScore XML tree
            target_part: The part to exclude (the highlighted voice)
        """
        root = tree.getroot()
        
        for part in root.findall(".//Part"):
            if part is target_part:
                continue
            
            # Get the instrument element
            instrument = part.find(".//Instrument")
            if instrument is None:
                continue
            
            # Check if this is a voice part by looking at the instrumentId
            instrument_id_elem = instrument.find("instrumentId")
            if instrument_id_elem is None:
                continue
            
            instrument_id = instrument_id_elem.text
            if not instrument_id or not instrument_id.startswith("voice."):
                # Not a voice part, skip it
                continue
            
            # Determine which voice type this is based on the instrumentId
            voice_type = instrument_id.replace("voice.", "")  # e.g., "soprano", "alto", "tenor", "bass"
            
            # Get the choir configuration for this voice type
            choir_configs = XMLModifier.get_voice_to_choir()
            choir_config = choir_configs.get(voice_type)
            if not choir_config:
                # Unknown voice type, skip
                continue
            
            # Replace with choir instrument
            XMLModifier._replace_with_choir_instrument(part, choir_config)
    
    @staticmethod
    def _replace_with_choir_instrument(part: ET.Element, choir_config: dict) -> None:
        """Replace the instrument for a part with a choir voice instrument.
        
        Args:
            part: The Part element to modify
            choir_config: Dictionary with choir instrument properties
        """
        # Find the Instrument element
        instrument = part.find(".//Instrument")
        
        if instrument is None:
            # Create one if it doesn't exist
            staff = part.find(".//Staff")
            if staff is None:
                raise XMLModificationError("Cannot find Staff element in part")
            instrument = ET.SubElement(staff, "Instrument")
        
        # Set the id attribute
        instrument.set("id", choir_config["id"])
        
        # Update or create instrument name elements
        XMLModifier._set_or_create_element(instrument, "longName", choir_config["longName"])
        XMLModifier._set_or_create_element(instrument, "shortName", choir_config["shortName"])
        XMLModifier._set_or_create_element(instrument, "trackName", choir_config["longName"])
        
        # Set pitch ranges
        XMLModifier._set_or_create_element(instrument, "minPitchP", choir_config["minPitchP"])
        XMLModifier._set_or_create_element(instrument, "maxPitchP", choir_config["maxPitchP"])
        XMLModifier._set_or_create_element(instrument, "minPitchA", choir_config["minPitchA"])
        XMLModifier._set_or_create_element(instrument, "maxPitchA", choir_config["maxPitchA"])
        
        # Set instrument ID
        XMLModifier._set_or_create_element(instrument, "instrumentId", choir_config["instrumentId"])
        
        # Set clef if specified
        if "clef" in choir_config:
            XMLModifier._set_or_create_element(instrument, "clef", choir_config["clef"])
        
        # Add glissandoStyle for choir voices
        XMLModifier._set_or_create_element(instrument, "glissandoStyle", "portamento")
        
        # Remove any transposition settings (choir voices don't transpose)
        for elem_name in ["transposeDiatonic", "transposeChromatic", "concertClef", "transposingClef"]:
            elem = instrument.find(elem_name)
            if elem is not None:
                instrument.remove(elem)
        
        # Set up MIDI channel
        channel = instrument.find(".//Channel")
        if channel is None:
            channel = ET.SubElement(instrument, "Channel")
        
        # Set program to 52 (Choir Aahs)
        program = channel.find("program")
        if program is None:
            program = ET.SubElement(channel, "program")
        program.set("value", "52")
        
        # Ensure synti is set to Fluid
        synti = channel.find("synti")
        if synti is None:
            synti = ET.SubElement(channel, "synti")
        synti.text = "Fluid"
