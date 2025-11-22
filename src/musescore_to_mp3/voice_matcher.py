"""Voice detection and matching utilities."""

from typing import List, Optional, Tuple
import xml.etree.ElementTree as ET

from .exceptions import VoiceNotFoundError


class VoiceMatcher:
    """Handles voice part detection and fuzzy matching."""
    
    # Common abbreviations for voice groups
    VOICE_ABBREVIATIONS = {
        "soprano": ["soprano", "sop", "s"],
        "soprano1": ["soprano1", "soprano 1", "sop1", "sop 1", "s1", "s 1"],
        "soprano2": ["soprano2", "soprano 2", "sop2", "sop 2", "s2", "s 2"],
        "alto": ["alto", "alt", "a"],
        "alto1": ["alto1", "alto 1", "alt1", "alt 1", "a1", "a 1"],
        "alto2": ["alto2", "alto 2", "alt2", "alt 2", "a2", "a 2"],
        "tenor": ["tenor", "ten", "t"],
        "tenor1": ["tenor1", "tenor 1", "ten1", "ten 1", "t1", "t 1"],
        "tenor2": ["tenor2", "tenor 2", "ten2", "ten 2", "t2", "t 2"],
        "baritone": ["baritone", "bariton", "bar", "bass1", "bass 1", "bas1", "bas 1", "b1", "b 1"],
        "bass1": ["baritone", "bariton", "bar", "bass1", "bass 1", "bas1", "bas 1", "b1", "b 1"],
        "bass": ["bass", "bas", "b"],
        "bass2": ["bass2", "bass 2", "bas2", "bas 2", "b2", "b 2"],
    }
    
    @classmethod
    def find_part(cls, tree: ET.ElementTree, voice_group: str) -> Tuple[ET.Element, str]:
        """Find a part element matching the voice group.
        
        Args:
            tree: The MuseScore XML tree
            voice_group: The voice group to search for (e.g., "bass", "baritone", "bass1", "bass2")
            
        Returns:
            Tuple of (part element, matched part name)
            
        Raises:
            VoiceNotFoundError: If no matching part is found
        """
        voice_group_lower = voice_group.lower().replace(" ", "")
        
        # Get all parts from the score
        parts = cls._get_all_parts(tree)
        
        if not parts:
            raise VoiceNotFoundError("No parts found in the score")
        
        # Find the best match using similarity scoring
        best_match = cls._find_best_match(voice_group_lower, parts)
        
        if best_match:
            part, part_name, score, is_exact = best_match
            if not is_exact:
                print(f"Warning: Using '{part_name}' for voice group '{voice_group}'")
            return part, part_name
        
        # List available parts for error message
        available_parts = [name for _, name in parts]
        raise VoiceNotFoundError(
            f"Could not find voice group '{voice_group}'. "
            f"Available parts: {', '.join(available_parts)}"
        )
    
    @classmethod
    def _get_all_parts(cls, tree: ET.ElementTree) -> List[Tuple[ET.Element, str]]:
        """Get all parts and their names from the score.
        
        Args:
            tree: The MuseScore XML tree
            
        Returns:
            List of (part element, part name) tuples
        """
        parts = []
        root = tree.getroot()
        
        # Find all Part elements
        for part in root.findall(".//Part"):
            # Try to get the part name from Staff/Instrument/trackName
            part_name = cls._get_part_name(part)
            if part_name:
                parts.append((part, part_name))
        
        return parts
    
    @classmethod
    def _get_part_name(cls, part: ET.Element) -> Optional[str]:
        """Extract the name of a part.
        
        Args:
            part: The Part element
            
        Returns:
            The part name, or None if not found
        """
        # Try multiple possible locations for the part name
        name_paths = [
            ".//Staff/Instrument/trackName",
            ".//Staff/Instrument/longName",
            ".//Instrument/trackName",
            ".//Instrument/longName",
        ]
        
        for path in name_paths:
            name_elem = part.find(path)
            if name_elem is not None and name_elem.text:
                return name_elem.text.strip()
        
        return None
    
    @classmethod
    def _find_best_match(
        cls, voice_group: str, parts: List[Tuple[ET.Element, str]]
    ) -> Optional[Tuple[ET.Element, str, int, bool]]:
        """Find the best matching part name using similarity scoring.
        
        Args:
            voice_group: The voice group to search for (lowercase, no spaces)
            parts: List of (part element, part name) tuples
            
        Returns:
            Tuple of (part element, matched part name, score, is_exact), or None if no reasonable match
        """
        if not parts:
            return None
        
        def normalize(text: str) -> str:
            """Normalize text for comparison."""
            return text.lower().replace(" ", "").replace(".", "")
        
        def calculate_similarity(voice_group: str, part_name: str) -> Tuple[int, bool]:
            """Calculate similarity score between voice group and part name.
            
            Returns:
                Tuple of (score, is_exact_match)
            """
            norm_part = normalize(part_name)
            norm_voice = voice_group  # Already normalized
            
            # Check for exact match
            if norm_part == norm_voice:
                return (1000, True)
            
            # Check if part name matches any known abbreviation for this voice group
            abbreviations = cls.VOICE_ABBREVIATIONS.get(norm_voice, [])
            for abbr in abbreviations:
                if norm_part == normalize(abbr):
                    return (900, False)
            
            # Also check reverse: if voice group matches any abbreviation of known groups
            for group_name, abbrs in cls.VOICE_ABBREVIATIONS.items():
                for abbr in abbrs:
                    if norm_voice == normalize(abbr):
                        # Now check if part_name matches this group
                        if norm_part == group_name or norm_part in [normalize(a) for a in abbrs]:
                            return (850, False)
            
            score = 0
            
            # Check if first letter matches
            if norm_part and norm_voice and norm_part[0] == norm_voice[0]:
                score += 50
            
            # Check if part name contains voice group or vice versa
            if norm_voice in norm_part:
                score += 40
            elif norm_part in norm_voice:
                score += 35
            
            # Count common characters (weighted by position)
            for i, char in enumerate(norm_voice):
                if char in norm_part:
                    # Earlier matches are more valuable
                    weight = len(norm_voice) - i
                    score += weight
            
            # Bonus for shorter names (more likely to be voice parts like "S", "B")
            if len(norm_part) <= 3:
                score += 20
            elif len(norm_part) <= 6:
                score += 10
            
            # Penalty for very long names (less likely to be voice parts)
            if len(norm_part) > 15:
                score -= 10
            
            return (score, False)
        
        # Calculate scores for all parts
        scored_parts = []
        for part, part_name in parts:
            score, is_exact = calculate_similarity(voice_group, part_name)
            scored_parts.append((part, part_name, score, is_exact))
        
        # Sort by score (highest first)
        scored_parts.sort(key=lambda x: x[2], reverse=True)
        
        # Return best match if score is reasonable (>0)
        if scored_parts and scored_parts[0][2] > 0:
            return scored_parts[0]
        
        return None
    
    @classmethod
    def get_staff_indices_for_part(cls, part: ET.Element) -> List[int]:
        """Get all staff indices associated with a part.
        
        Args:
            part: The Part element
            
        Returns:
            List of staff indices (1-based)
        """
        staff_indices = []
        
        # Find all Staff elements in the part
        for i, staff in enumerate(part.findall(".//Staff"), start=1):
            # Check if the staff has an 'id' attribute
            staff_id = staff.get('id')
            if staff_id:
                try:
                    staff_indices.append(int(staff_id))
                except ValueError:
                    pass
            else:
                # If no id, use sequential numbering
                staff_indices.append(i)
        
        return staff_indices if staff_indices else [1]
