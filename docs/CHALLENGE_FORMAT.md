# ZeroRange Challenge Configuration Guide

This document describes how to create and customize challenges for ZeroRange modules.

## Overview

Challenges are defined in JSON configuration files located in the `challenges/` directory. Each module has its own file:

```
challenges/
├── schema.json      # JSON Schema (do not modify)
├── ibutton.json     # iButton/1-Wire challenges
├── nfc.json         # NFC/ISO14443A challenges
├── rfid.json        # RFID 125kHz challenges
└── subghz.json      # Sub-GHz RF challenges
```

## File Structure

Each challenge file follows this structure:

```json
{
  "$schema": "./schema.json",
  "module": "module_name",
  "version": "1.0",
  "description": "Module description",
  "challenges": [
    { /* challenge 1 */ },
    { /* challenge 2 */ },
    { /* ... */ }
  ]
}
```

### Root Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `$schema` | string | No | Reference to schema file for validation |
| `module` | string | Yes | Module identifier: `ibutton`, `nfc`, `rfid`, `subghz`, or `ir` |
| `version` | string | Yes | Configuration version (format: `X.Y`) |
| `description` | string | No | Human-readable description |
| `challenges` | array | Yes | Array of challenge objects |

## Challenge Object

Each challenge requires the following properties:

```json
{
  "id": "unique_challenge_id",
  "name": "Display Name",
  "description": "Full description of what the user must do",
  "difficulty": "beginner",
  "points": 10,
  "timeout_seconds": 60,
  "type": "detect",
  "instructions": [
    "Step 1: Do this",
    "Step 2: Do that"
  ],
  "validation": {
    "method": "any_detection",
    "parameters": {}
  }
}
```

### Required Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | string | Unique identifier (lowercase, underscores only: `^[a-z][a-z0-9_]*$`) |
| `name` | string | Short display name (max 20 characters for LCD compatibility) |
| `description` | string | Full description of the challenge objective |
| `difficulty` | string | One of: `beginner`, `intermediate`, `advanced`, `expert` |
| `points` | integer | Points awarded (1-100) |
| `timeout_seconds` | integer | Time limit (10-600 seconds) |
| `type` | string | Challenge type (see below) |
| `instructions` | array | Step-by-step instructions |
| `validation` | object | Validation configuration |

### Optional Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `success_message` | string | "" | Message shown on success. Supports `{placeholders}` |
| `failure_message` | string | "" | Message shown on failure |
| `hints` | array | [] | Optional hints for the user |
| `prerequisites` | array | [] | Challenge IDs that must be completed first |
| `enabled` | boolean | true | Whether this challenge is active |
| `custom_data` | object | {} | Module-specific custom data |

## Challenge Types

| Type | Description | Use Case |
|------|-------------|----------|
| `detect` | Simple detection/read | First challenges - just read something |
| `multi_step` | Multiple sequential steps | Clone operations (read then write) |
| `target_match` | Match a specific value | Emulate a given ID |
| `attack` | Security attack/exploit | Key recovery, MIFARE attacks |
| `emulation` | Device emulation | Flipper Zero emulation tasks |
| `capture` | Signal/data capture | Sub-GHz signal capture |
| `analysis` | Analysis/identification | Protocol identification |

## Validation Methods

### `any_detection`
Validates when any valid input is detected.

```json
{
  "method": "any_detection",
  "parameters": {
    "accepted_types": ["ISO14443A", "MIFARE Classic"]
  }
}
```

### `exact_match`
Validates when input matches a specific target.

```json
{
  "method": "exact_match",
  "parameters": {
    "target_ids": ["01:23:45:67:89:AB:CD:EF"],
    "random_selection": true
  }
}
```

### `clone_verify`
Validates a clone operation (original read + clone match).

```json
{
  "method": "clone_verify",
  "parameters": {
    "require_original_read": true,
    "require_emulation_match": true
  }
}
```

### `key_recovery`
Validates key recovery from attacks.

```json
{
  "method": "key_recovery",
  "parameters": {
    "min_keys_required": 1,
    "accepted_methods": ["nested", "hardnested"]
  }
}
```

### `emulation_detect`
Validates device emulation.

```json
{
  "method": "emulation_detect",
  "parameters": {
    "protocol": "EM410x",
    "require_valid_id": true
  }
}
```

### `signal_capture`
Validates RF signal capture.

```json
{
  "method": "signal_capture",
  "parameters": {
    "frequency_mhz": 433.92,
    "min_signal_strength_dbm": -55,
    "min_duration_ms": 100
  }
}
```

### `replay_count`
Validates multiple signal replays.

```json
{
  "method": "replay_count",
  "parameters": {
    "required_replays": 3,
    "max_time_between_replays_sec": 10
  }
}
```

### `protocol_identification`
Validates correct protocol/modulation identification.

```json
{
  "method": "protocol_identification",
  "parameters": {
    "test_signals": [
      {"protocol": "Princeton", "modulation": "OOK", "frequency": 433.92}
    ],
    "random_selection": true
  }
}
```

## Adding a New Challenge

### Step 1: Choose the Module

Decide which module your challenge belongs to based on the technology:
- **ibutton**: 1-Wire protocol, DS1990A keys
- **nfc**: ISO14443A/B, MIFARE, contactless cards
- **rfid**: 125kHz tags (EM4100, HID, etc.)
- **subghz**: Radio frequencies (315/433/868/915 MHz)
- **ir**: Infrared (coming soon)

### Step 2: Create the Challenge JSON

Add your challenge to the appropriate `challenges/*.json` file:

```json
{
  "id": "nfc_custom_challenge",
  "name": "My Challenge",
  "description": "Description of what the user needs to do",
  "difficulty": "intermediate",
  "points": 15,
  "timeout_seconds": 90,
  "type": "multi_step",
  "instructions": [
    "Step 1: Read the card",
    "Step 2: Analyze the data",
    "Step 3: Complete the objective"
  ],
  "success_message": "Challenge complete! Data: {result}",
  "failure_message": "Challenge failed. Try again.",
  "validation": {
    "method": "clone_verify",
    "parameters": {
      "require_original_read": true
    }
  },
  "hints": [
    "Hint 1: Try this approach",
    "Hint 2: Remember to check..."
  ],
  "enabled": true
}
```

### Step 3: Validate Your Configuration

Run the challenge loader to validate:

```bash
python3 challenge_loader.py
```

Expected output:
```
ZeroRange Challenge Loader Test
==================================================

Loaded modules: ['ibutton', 'nfc', 'rfid', 'subghz']
Total challenges: 12
Total points: 120

IBUTTON (3 challenges, 30 pts):
  - [beginner] Touch & Read: Detect and read any iButton using your Flipper...
  ...
```

### Step 4: Test Your Challenge

1. Start ZeroRange: `python3 zerorange.py`
2. Navigate to your module
3. Select your new challenge
4. Verify it works as expected

## Creating a New Module

To add an entirely new module (e.g., IR):

### 1. Create the Challenge File

Create `challenges/ir.json`:

```json
{
  "$schema": "./schema.json",
  "module": "ir",
  "version": "1.0",
  "description": "Challenges for Infrared protocol training",
  "challenges": [
    {
      "id": "ir_capture",
      "name": "Capture IR Signal",
      "description": "Capture an infrared remote signal",
      "difficulty": "beginner",
      "points": 10,
      "timeout_seconds": 60,
      "type": "capture",
      "instructions": [
        "Point an IR remote at the receiver",
        "Press any button on the remote",
        "The system will capture the signal"
      ],
      "validation": {
        "method": "any_detection",
        "parameters": {}
      }
    }
  ]
}
```

### 2. Create the Handler

Create `ir_handler.py` following the existing handler pattern.

### 3. Register in Main App

Add the module to `zerorange.py` state machine and menu.

## Message Placeholders

Success and failure messages support dynamic placeholders:

| Placeholder | Description |
|-------------|-------------|
| `{detected_id}` | Detected device/tag ID |
| `{detected_uid}` | Detected NFC UID |
| `{card_type}` | Card/tag type |
| `{tag_id}` | RFID tag ID |
| `{protocol}` | Detected protocol |
| `{signal_strength}` | Signal strength in dBm |
| `{replay_count}` | Number of replays detected |
| `{original_id}` | Original ID in clone operations |
| `{sector}` | MIFARE sector number |
| `{result}` | Generic result data |

## Best Practices

1. **Unique IDs**: Use descriptive, prefixed IDs: `module_action_detail`
2. **Clear Names**: Keep names under 20 characters for LCD display
3. **Progressive Difficulty**: Order challenges from easy to hard
4. **Helpful Instructions**: Be specific and actionable
5. **Useful Hints**: Provide hints that help without giving away the answer
6. **Reasonable Timeouts**: Allow enough time but create urgency
7. **Balanced Points**: Scale points with difficulty (10-25 typical)

## Example: Complete Challenge

```json
{
  "id": "rfid_bruteforce_sim",
  "name": "Brute Force Sim",
  "description": "Simulate multiple RFID tags to find the correct access code",
  "difficulty": "advanced",
  "points": 25,
  "timeout_seconds": 180,
  "type": "attack",
  "instructions": [
    "The target system accepts one of 10 possible tag IDs",
    "Use your Flipper to cycle through and emulate different IDs",
    "Find the correct ID that grants access",
    "The system will confirm when you find the right one"
  ],
  "success_message": "Access granted! Correct ID: {detected_id}",
  "failure_message": "Time's up! The correct ID was {target_id}",
  "validation": {
    "method": "exact_match",
    "parameters": {
      "target_ids": [
        "1234567890",
        "0987654321",
        "1122334455"
      ],
      "random_selection": true,
      "max_attempts": 10
    }
  },
  "hints": [
    "Start with common default IDs",
    "Try sequential patterns",
    "The ID is 10 digits long"
  ],
  "prerequisites": ["rfid_detect", "rfid_simulate"],
  "enabled": true
}
```

## Troubleshooting

### Challenge Not Loading
- Check JSON syntax with a validator
- Verify all required fields are present
- Ensure `id` is unique across all modules
- Check that `module` matches the filename

### Validation Not Working
- Verify `validation.method` is one of the supported methods
- Check `parameters` match the method requirements
- Enable debug logging: set `"log_level": "DEBUG"` in `config.json`

### Display Issues
- Keep `name` under 20 characters
- Test on actual LCD display
- Use ASCII characters only

## Support

For questions or issues:
- GitHub Issues: https://github.com/your-repo/zerorange/issues
- Documentation: See other files in `docs/`
