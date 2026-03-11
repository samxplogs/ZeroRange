#!/usr/bin/env python3
"""
ZeroRange Challenge Loader

Loads and validates challenge configurations from JSON files.
Provides a unified interface for accessing challenge definitions.

Usage:
    from challenge_loader import ChallengeLoader

    loader = ChallengeLoader()
    challenges = loader.get_module_challenges('ibutton')
    challenge = loader.get_challenge('ibutton_detect')
"""

import json
import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# Valid values for enums
VALID_MODULES = ['ibutton', 'nfc', 'rfid', 'subghz', 'ir']
VALID_DIFFICULTIES = ['beginner', 'intermediate', 'advanced', 'expert']
VALID_TYPES = ['detect', 'multi_step', 'target_match', 'attack', 'emulation', 'capture', 'analysis']
VALID_METHODS = [
    'any_detection', 'exact_match', 'clone_verify', 'key_recovery',
    'emulation_detect', 'signal_capture', 'replay_count', 'protocol_identification'
]


@dataclass
class ValidationConfig:
    """Challenge validation configuration."""
    method: str
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Challenge:
    """Represents a single challenge configuration."""
    id: str
    name: str
    description: str
    difficulty: str
    points: int
    timeout_seconds: int
    type: str
    instructions: List[str]
    validation: ValidationConfig
    module: str = ""
    success_message: str = ""
    failure_message: str = ""
    hints: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    enabled: bool = True
    custom_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert challenge to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'difficulty': self.difficulty,
            'points': self.points,
            'timeout_seconds': self.timeout_seconds,
            'type': self.type,
            'instructions': self.instructions,
            'validation': {
                'method': self.validation.method,
                'parameters': self.validation.parameters
            },
            'module': self.module,
            'success_message': self.success_message,
            'failure_message': self.failure_message,
            'hints': self.hints,
            'prerequisites': self.prerequisites,
            'enabled': self.enabled,
            'custom_data': self.custom_data
        }


class ChallengeLoader:
    """
    Loads challenge configurations from JSON files.

    Attributes:
        challenges_dir: Path to the challenges directory
        challenges: Dictionary mapping challenge IDs to Challenge objects
        modules: Dictionary mapping module names to lists of challenges
    """

    def __init__(self, challenges_dir: Optional[str] = None):
        """
        Initialize the challenge loader.

        Args:
            challenges_dir: Path to challenges directory. Defaults to ./challenges/
        """
        if challenges_dir is None:
            # Default to challenges/ directory relative to this file
            base_dir = Path(__file__).parent
            challenges_dir = base_dir / 'challenges'

        self.challenges_dir = Path(challenges_dir)
        self.challenges: Dict[str, Challenge] = {}
        self.modules: Dict[str, List[Challenge]] = {}
        self._load_errors: List[str] = []

        self._load_all_challenges()

    def _load_all_challenges(self) -> None:
        """Load all challenge files from the challenges directory."""
        if not self.challenges_dir.exists():
            logger.warning(f"Challenges directory not found: {self.challenges_dir}")
            return

        # Find all JSON files (except schema.json)
        json_files = [
            f for f in self.challenges_dir.glob('*.json')
            if f.name != 'schema.json'
        ]

        for json_file in json_files:
            try:
                self._load_challenge_file(json_file)
            except Exception as e:
                error_msg = f"Failed to load {json_file.name}: {e}"
                logger.error(error_msg)
                self._load_errors.append(error_msg)

        logger.info(f"Loaded {len(self.challenges)} challenges from {len(self.modules)} modules")

    def _load_challenge_file(self, file_path: Path) -> None:
        """
        Load and validate a single challenge file.

        Args:
            file_path: Path to the JSON file
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Validate module
        module = data.get('module')
        if module not in VALID_MODULES:
            raise ValueError(f"Invalid module '{module}'. Must be one of: {VALID_MODULES}")

        # Initialize module list
        if module not in self.modules:
            self.modules[module] = []

        # Load each challenge
        for challenge_data in data.get('challenges', []):
            challenge = self._parse_challenge(challenge_data, module)

            # Check for duplicate IDs
            if challenge.id in self.challenges:
                raise ValueError(f"Duplicate challenge ID: {challenge.id}")

            self.challenges[challenge.id] = challenge
            self.modules[module].append(challenge)

    def _parse_challenge(self, data: Dict[str, Any], module: str) -> Challenge:
        """
        Parse a challenge dictionary into a Challenge object.

        Args:
            data: Challenge data dictionary
            module: Module name

        Returns:
            Challenge object
        """
        # Validate required fields
        required = ['id', 'name', 'description', 'difficulty', 'points',
                   'timeout_seconds', 'type', 'instructions', 'validation']
        for field in required:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Validate enum fields
        if data['difficulty'] not in VALID_DIFFICULTIES:
            raise ValueError(f"Invalid difficulty '{data['difficulty']}'")
        if data['type'] not in VALID_TYPES:
            raise ValueError(f"Invalid type '{data['type']}'")

        # Parse validation
        val_data = data['validation']
        if val_data['method'] not in VALID_METHODS:
            raise ValueError(f"Invalid validation method '{val_data['method']}'")

        validation = ValidationConfig(
            method=val_data['method'],
            parameters=val_data.get('parameters', {})
        )

        return Challenge(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            difficulty=data['difficulty'],
            points=data['points'],
            timeout_seconds=data['timeout_seconds'],
            type=data['type'],
            instructions=data['instructions'],
            validation=validation,
            module=module,
            success_message=data.get('success_message', ''),
            failure_message=data.get('failure_message', ''),
            hints=data.get('hints', []),
            prerequisites=data.get('prerequisites', []),
            enabled=data.get('enabled', True),
            custom_data=data.get('custom_data', {})
        )

    def get_challenge(self, challenge_id: str) -> Optional[Challenge]:
        """
        Get a challenge by its ID.

        Args:
            challenge_id: The unique challenge identifier

        Returns:
            Challenge object or None if not found
        """
        return self.challenges.get(challenge_id)

    def get_module_challenges(self, module: str, enabled_only: bool = True) -> List[Challenge]:
        """
        Get all challenges for a specific module.

        Args:
            module: Module name (ibutton, nfc, rfid, subghz, ir)
            enabled_only: If True, only return enabled challenges

        Returns:
            List of Challenge objects
        """
        challenges = self.modules.get(module, [])
        if enabled_only:
            challenges = [c for c in challenges if c.enabled]
        return challenges

    def get_all_challenges(self, enabled_only: bool = True) -> List[Challenge]:
        """
        Get all challenges across all modules.

        Args:
            enabled_only: If True, only return enabled challenges

        Returns:
            List of Challenge objects
        """
        if enabled_only:
            return [c for c in self.challenges.values() if c.enabled]
        return list(self.challenges.values())

    def get_available_modules(self) -> List[str]:
        """
        Get list of modules that have challenges loaded.

        Returns:
            List of module names
        """
        return list(self.modules.keys())

    def get_total_points(self, module: Optional[str] = None) -> int:
        """
        Calculate total possible points.

        Args:
            module: If specified, only count points for this module

        Returns:
            Total points available
        """
        if module:
            challenges = self.get_module_challenges(module)
        else:
            challenges = self.get_all_challenges()
        return sum(c.points for c in challenges)

    def get_challenges_by_difficulty(self, difficulty: str) -> List[Challenge]:
        """
        Get all challenges of a specific difficulty.

        Args:
            difficulty: beginner, intermediate, advanced, or expert

        Returns:
            List of Challenge objects
        """
        return [c for c in self.challenges.values() if c.difficulty == difficulty and c.enabled]

    def reload(self) -> None:
        """Reload all challenge files."""
        self.challenges.clear()
        self.modules.clear()
        self._load_errors.clear()
        self._load_all_challenges()

    def get_load_errors(self) -> List[str]:
        """Get list of errors that occurred during loading."""
        return self._load_errors.copy()

    def validate_prerequisites(self, challenge_id: str, completed_ids: List[str]) -> bool:
        """
        Check if all prerequisites for a challenge are met.

        Args:
            challenge_id: ID of the challenge to check
            completed_ids: List of completed challenge IDs

        Returns:
            True if all prerequisites are met
        """
        challenge = self.get_challenge(challenge_id)
        if not challenge:
            return False

        return all(prereq in completed_ids for prereq in challenge.prerequisites)


# Module-level convenience instance
_default_loader: Optional[ChallengeLoader] = None


def get_loader() -> ChallengeLoader:
    """
    Get the default challenge loader instance.

    Returns:
        ChallengeLoader instance (singleton)
    """
    global _default_loader
    if _default_loader is None:
        _default_loader = ChallengeLoader()
    return _default_loader


# Example usage and testing
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    loader = ChallengeLoader()

    print(f"\n{'='*50}")
    print("ZeroRange Challenge Loader Test")
    print(f"{'='*50}")

    print(f"\nLoaded modules: {loader.get_available_modules()}")
    print(f"Total challenges: {len(loader.get_all_challenges())}")
    print(f"Total points: {loader.get_total_points()}")

    for module in loader.get_available_modules():
        challenges = loader.get_module_challenges(module)
        print(f"\n{module.upper()} ({len(challenges)} challenges, {loader.get_total_points(module)} pts):")
        for c in challenges:
            print(f"  - [{c.difficulty}] {c.name}: {c.description[:50]}...")

    if loader.get_load_errors():
        print(f"\nLoad errors:")
        for error in loader.get_load_errors():
            print(f"  - {error}")
