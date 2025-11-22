"""XML modification utilities for MuseScore files."""

import xml.etree.ElementTree as ET
from typing import List

from .exceptions import XMLModificationError
from .voice_matcher import VoiceMatcher


class XMLModifier:
    """Handles modification of MuseScore XML."""
    
    # Map voice groups to saxophone instruments with full properties
    VOICE_TO_SAXOPHONE = {
        "soprano": {
            "id": "soprano-saxophone",
            "instrumentId": "wind.reed.saxophone.soprano",
            "longName": "Soprano Saxophone",
            "shortName": "S. Sax.",
            "program": "64",
            "minPitchP": "56",
            "maxPitchP": "91",
            "minPitchA": "56",
            "maxPitchA": "87",
            "transposeDiatonic": "-1",
            "transposeChromatic": "-2",
        },
        "soprano1": {
            "id": "soprano-saxophone",
            "instrumentId": "wind.reed.saxophone.soprano",
            "longName": "Soprano Saxophone",
            "shortName": "S. Sax.",
            "program": "64",
            "minPitchP": "56",
            "maxPitchP": "91",
            "minPitchA": "56",
            "maxPitchA": "87",
            "transposeDiatonic": "-1",
            "transposeChromatic": "-2",
        },
        "soprano2": {
            "id": "soprano-saxophone",
            "instrumentId": "wind.reed.saxophone.soprano",
            "longName": "Soprano Saxophone",
            "shortName": "S. Sax.",
            "program": "64",
            "minPitchP": "56",
            "maxPitchP": "91",
            "minPitchA": "56",
            "maxPitchA": "87",
            "transposeDiatonic": "-1",
            "transposeChromatic": "-2",
        },
        "alto": {
            "id": "alto-saxophone",
            "instrumentId": "wind.reed.saxophone.alto",
            "longName": "Alto Saxophone",
            "shortName": "A. Sax.",
            "program": "65",
            "minPitchP": "49",
            "maxPitchP": "92",
            "minPitchA": "49",
            "maxPitchA": "80",
            "transposeDiatonic": "-5",
            "transposeChromatic": "-9",
        },
        "alto1": {
            "id": "alto-saxophone",
            "instrumentId": "wind.reed.saxophone.alto",
            "longName": "Alto Saxophone",
            "shortName": "A. Sax.",
            "program": "65",
            "minPitchP": "49",
            "maxPitchP": "92",
            "minPitchA": "49",
            "maxPitchA": "80",
            "transposeDiatonic": "-5",
            "transposeChromatic": "-9",
        },
        "alto2": {
            "id": "alto-saxophone",
            "instrumentId": "wind.reed.saxophone.alto",
            "longName": "Alto Saxophone",
            "shortName": "A. Sax.",
            "program": "65",
            "minPitchP": "49",
            "maxPitchP": "92",
            "minPitchA": "49",
            "maxPitchA": "80",
            "transposeDiatonic": "-5",
            "transposeChromatic": "-9",
        },
        "tenor": {
            "id": "tenor-saxophone",
            "instrumentId": "wind.reed.saxophone.tenor",
            "longName": "Tenor Saxophone",
            "shortName": "T. Sax.",
            "program": "66",
            "minPitchP": "44",
            "maxPitchP": "87",
            "minPitchA": "44",
            "maxPitchA": "75",
            "transposeDiatonic": "-8",
            "transposeChromatic": "-14",
        },
        "tenor1": {
            "id": "tenor-saxophone",
            "instrumentId": "wind.reed.saxophone.tenor",
            "longName": "Tenor Saxophone",
            "shortName": "T. Sax.",
            "program": "66",
            "minPitchP": "44",
            "maxPitchP": "87",
            "minPitchA": "44",
            "maxPitchA": "75",
            "transposeDiatonic": "-8",
            "transposeChromatic": "-14",
        },
        "tenor2": {
            "id": "tenor-saxophone",
            "instrumentId": "wind.reed.saxophone.tenor",
            "longName": "Tenor Saxophone",
            "shortName": "T. Sax.",
            "program": "66",
            "minPitchP": "44",
            "maxPitchP": "87",
            "minPitchA": "44",
            "maxPitchA": "75",
            "transposeDiatonic": "-8",
            "transposeChromatic": "-14",
        },
        "baritone": {
            "id": "baritone-saxophone",
            "instrumentId": "wind.reed.saxophone.baritone",
            "longName": "Baritone Saxophone",
            "shortName": "Bar. Sax.",
            "program": "67",
            "minPitchP": "36",
            "maxPitchP": "80",
            "minPitchA": "36",
            "maxPitchA": "68",
            "transposeDiatonic": "-12",
            "transposeChromatic": "-21",
        },
        "bass1": {
            "id": "baritone-saxophone",
            "instrumentId": "wind.reed.saxophone.baritone",
            "longName": "Baritone Saxophone",
            "shortName": "Bar. Sax.",
            "program": "67",
            "minPitchP": "36",
            "maxPitchP": "80",
            "minPitchA": "36",
            "maxPitchA": "68",
            "transposeDiatonic": "-12",
            "transposeChromatic": "-21",
        },
        "bass": {
            "id": "baritone-saxophone",
            "instrumentId": "wind.reed.saxophone.baritone",
            "longName": "Baritone Saxophone",
            "shortName": "Bar. Sax.",
            "program": "67",
            "minPitchP": "36",
            "maxPitchP": "80",
            "minPitchA": "36",
            "maxPitchA": "68",
            "transposeDiatonic": "-12",
            "transposeChromatic": "-21",
        },
        "bass2": {
            "id": "baritone-saxophone",
            "instrumentId": "wind.reed.saxophone.baritone",
            "longName": "Baritone Saxophone",
            "shortName": "Bar. Sax.",
            "program": "67",
            "minPitchP": "36",
            "maxPitchP": "80",
            "minPitchA": "36",
            "maxPitchA": "68",
            "transposeDiatonic": "-12",
            "transposeChromatic": "-21",
        },
        "baritone1": {
            "id": "baritone-saxophone",
            "instrumentId": "wind.reed.saxophone.baritone",
            "longName": "Baritone Saxophone",
            "shortName": "Bar. Sax.",
            "program": "67",
            "minPitchP": "36",
            "maxPitchP": "80",
            "minPitchA": "36",
            "maxPitchA": "68",
            "transposeDiatonic": "-12",
            "transposeChromatic": "-21",
        },
        "baritone2": {
            "id": "baritone-saxophone",
            "instrumentId": "wind.reed.saxophone.baritone",
            "longName": "Baritone Saxophone",
            "shortName": "Bar. Sax.",
            "program": "67",
            "minPitchP": "36",
            "maxPitchP": "80",
            "minPitchA": "36",
            "maxPitchA": "68",
            "transposeDiatonic": "-12",
            "transposeChromatic": "-21",
        },
    }
    
    @staticmethod
    def modify_voice_part(
        tree: ET.ElementTree,
        voice_group: str,
        replacement_instrument: str = "Baritone Saxophone",
        voice_volume_boost: int = 10,
        master_volume: int = 80,
    ) -> None:
        """Modify a voice part to stand out.
        
        This function:
        1. Finds the specified voice part
        2. Replaces its instrument
        3. Boosts its volume
        4. Reduces the master volume for other parts
        
        Args:
            tree: The MuseScore XML tree
            voice_group: The voice group to modify
            replacement_instrument: Instrument name to replace with
            voice_volume_boost: Volume boost for the voice in dB
            master_volume: Master volume percentage for other parts
            
        Raises:
            VoiceNotFoundError: If the voice group is not found
            XMLModificationError: If modification fails
        """
        # Find the target part
        target_part, matched_name = VoiceMatcher.find_part(tree, voice_group)
        
        try:
            # Get the appropriate saxophone for this voice group
            voice_normalized = voice_group.lower().replace(" ", "")
            sax_config = XMLModifier.VOICE_TO_SAXOPHONE.get(
                voice_normalized,
                XMLModifier.VOICE_TO_SAXOPHONE["bass"]  # Default to baritone sax
            )
            
            # Modify the instrument
            XMLModifier._replace_instrument(target_part, sax_config)
            
            # Boost the voice volume
            XMLModifier._set_part_volume(target_part, 100 + voice_volume_boost)
            
            # Reduce master volume for all other parts
            XMLModifier._set_other_parts_volume(tree, target_part, master_volume)
            
        except Exception as e:
            raise XMLModificationError(f"Failed to modify voice part: {e}")
    
    @staticmethod
    def _replace_instrument(part: ET.Element, sax_config: dict) -> None:
        """Replace the instrument for a part with a saxophone.
        
        Args:
            part: The Part element to modify
            sax_config: Dictionary with all saxophone properties
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
        instrument.set("id", sax_config["id"])
        
        # Update or create instrument name elements
        XMLModifier._set_or_create_element(instrument, "longName", sax_config["longName"])
        XMLModifier._set_or_create_element(instrument, "shortName", sax_config["shortName"])
        XMLModifier._set_or_create_element(instrument, "trackName", sax_config["longName"])
        
        # Set pitch ranges
        XMLModifier._set_or_create_element(instrument, "minPitchP", sax_config["minPitchP"])
        XMLModifier._set_or_create_element(instrument, "maxPitchP", sax_config["maxPitchP"])
        XMLModifier._set_or_create_element(instrument, "minPitchA", sax_config["minPitchA"])
        XMLModifier._set_or_create_element(instrument, "maxPitchA", sax_config["maxPitchA"])
        
        # Set transposition
        XMLModifier._set_or_create_element(instrument, "transposeDiatonic", sax_config["transposeDiatonic"])
        XMLModifier._set_or_create_element(instrument, "transposeChromatic", sax_config["transposeChromatic"])
        
        # Set instrument ID (critical for MuseScore to recognize the instrument)
        XMLModifier._set_or_create_element(instrument, "instrumentId", sax_config["instrumentId"])
        
        # Set MIDI program (General MIDI instrument number)
        channel = instrument.find(".//Channel")
        if channel is None:
            channel = ET.SubElement(instrument, "Channel")
        
        program = channel.find("program")
        if program is None:
            program = ET.SubElement(channel, "program")
        program.set("value", sax_config["program"])
        
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
