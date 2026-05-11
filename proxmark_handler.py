#!/usr/bin/env python3
"""
Proxmark Handler for ZeroRange
Interface avec le Proxmark3 pour NFC et RFID
"""

import subprocess
import re
import tempfile
import threading
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Iterable, List, Tuple

logger = logging.getLogger(__name__)


class ProxmarkHandler:
    """Interface pour communiquer avec le Proxmark3"""

    def __init__(self, port: str = "/dev/ttyACM0"):
        """
        Initialize Proxmark handler

        Args:
            port: Port série du Proxmark (ex: /dev/ttyACM0)
        """
        self.port = port
        self.client_path = "proxmark3"  # ou chemin complet si nécessaire

        # Vérifier que le Proxmark est disponible
        if not self.check_proxmark():
            logger.warning("Proxmark non détecté, fonctionnement en mode simulation")
            self.simulation_mode = True
        else:
            logger.info("Proxmark détecté et prêt")
            self.simulation_mode = False

    def check_proxmark(self) -> bool:
        """
        Vérifie que le Proxmark est connecté et fonctionnel

        Returns:
            bool: True si le Proxmark est disponible
        """
        try:
            result = subprocess.run(
                [self.client_path, self.port, "-c", "hw version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return "Proxmark3" in result.stdout or "pm3" in result.stdout
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du Proxmark: {e}")
            return False

    def run_command(self, command: str, timeout: int = 10) -> Tuple[bool, str]:
        """
        Exécute une commande Proxmark

        Args:
            command: Commande à exécuter
            timeout: Timeout en secondes

        Returns:
            tuple: (success, output)
        """
        try:
            logger.debug(f"Exécution commande Proxmark: {command}")

            result = subprocess.run(
                [self.client_path, self.port, "-c", command],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            output = result.stdout + result.stderr
            success = result.returncode == 0

            logger.debug(f"Résultat: {success}, Output: {output[:200]}...")

            return success, output

        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout lors de l'exécution de: {command}")
            return False, "Timeout"
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de {command}: {e}")
            return False, str(e)

    # ==================== NFC (ISO14443A) ====================

    def nfc_scan(self) -> Optional[Dict[str, str]]:
        """
        Scanne pour détecter une carte NFC (ISO14443A)

        Returns:
            dict: Informations de la carte (uid, type, etc.) ou None
        """
        success, output = self.run_command("hf 14a reader", timeout=5)

        if not success:
            return None

        # Parser l'output pour extraire les infos
        card_info = {}

        # UID
        uid_match = re.search(r"UID\s*:\s*([0-9a-fA-F\s]+)", output)
        if uid_match:
            card_info['uid'] = uid_match.group(1).replace(" ", "").strip()

        # ATQA
        atqa_match = re.search(r"ATQA\s*:\s*([0-9a-fA-F\s]+)", output)
        if atqa_match:
            card_info['atqa'] = atqa_match.group(1).strip()

        # SAK
        sak_match = re.search(r"SAK\s*:\s*([0-9a-fA-F\s]+)", output)
        if sak_match:
            card_info['sak'] = sak_match.group(1).strip()

        # Type de carte
        if "MIFARE Classic" in output:
            card_info['type'] = "MIFARE Classic"
        elif "MIFARE Ultralight" in output:
            card_info['type'] = "MIFARE Ultralight"
        elif "NTAG" in output:
            card_info['type'] = "NTAG"
        elif "DESFire" in output:
            card_info['type'] = "DESFire"
        else:
            card_info['type'] = "Unknown"

        if card_info:
            logger.info(f"Carte NFC détectée: {card_info}")
            return card_info

        return None

    def nfc_read_block(self, block: int, key: str = "FFFFFFFFFFFF", key_type: str = "A") -> Optional[str]:
        """
        Lit un bloc MIFARE Classic

        Args:
            block: Numéro du bloc
            key: Clé (hex)
            key_type: Type de clé (A ou B)

        Returns:
            str: Données du bloc (hex) ou None
        """
        command = f"hf mf rdbl {block} {key_type} {key}"
        success, output = self.run_command(command, timeout=5)

        if success:
            # Parser les données
            data_match = re.search(r"data:\s*([0-9a-fA-F\s]+)", output, re.IGNORECASE)
            if data_match:
                return data_match.group(1).replace(" ", "").strip()

        return None

    def nfc_dump_mifare(self) -> Optional[Dict[int, str]]:
        """
        Dump complet d'une carte MIFARE Classic

        Returns:
            dict: {block_number: data} ou None
        """
        command = "hf mf dump"
        success, output = self.run_command(command, timeout=30)

        if success and "Dump saved" in output:
            logger.info("Dump MIFARE réussi")
            return self._parse_mifare_dump(output)

        return None

    def _parse_mifare_dump(self, output: str) -> Dict[int, str]:
        """Parse l'output d'un dump MIFARE"""
        blocks = {}

        # Rechercher les lignes de type: "Block  0: XXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        for match in re.finditer(r"Block\s+(\d+):\s*([0-9a-fA-F\s]+)", output, re.IGNORECASE):
            block_num = int(match.group(1))
            data = match.group(2).replace(" ", "").strip()
            blocks[block_num] = data

        return blocks

    # ==================== RFID 125kHz (LF) ====================

    def rfid_scan(self) -> Optional[Dict[str, str]]:
        """
        Scanne pour détecter un tag RFID 125kHz

        Returns:
            dict: Informations du tag (id, type, etc.) ou None
        """
        success, output = self.run_command("lf search", timeout=10)

        if not success:
            return None

        tag_info = {}

        # EM410x
        em_match = re.search(r"EM410x\s+ID\s+found:\s+([0-9a-fA-F]+)", output, re.IGNORECASE)
        if em_match:
            tag_info['type'] = "EM410x"
            tag_info['id'] = em_match.group(1).strip()

        # HID Prox
        hid_match = re.search(r"HID Prox\s+TAG\s+ID:\s+([0-9a-fA-F]+)", output, re.IGNORECASE)
        if hid_match:
            tag_info['type'] = "HID Prox"
            tag_info['id'] = hid_match.group(1).strip()

        # Indala
        indala_match = re.search(r"Indala\s+ID\s+found:\s+([0-9a-fA-F]+)", output, re.IGNORECASE)
        if indala_match:
            tag_info['type'] = "Indala"
            tag_info['id'] = indala_match.group(1).strip()

        if tag_info:
            logger.info(f"Tag RFID détecté: {tag_info}")
            return tag_info

        return None

    def rfid_read_em410x(self) -> Optional[str]:
        """
        Lit spécifiquement un tag EM410x

        Returns:
            str: ID du tag (hex) ou None
        """
        success, output = self.run_command("lf em 410x reader", timeout=5)

        if success:
            em_match = re.search(r"EM TAG ID\s*:\s*([0-9a-fA-F]+)", output, re.IGNORECASE)
            if em_match:
                return em_match.group(1).strip()

        return None

    def rfid_clone_to_t5577(self, tag_id: str, tag_type: str = "em410x") -> bool:
        """
        Clone un tag vers un T5577

        Args:
            tag_id: ID du tag à cloner
            tag_type: Type de tag (em410x, hid, indala)

        Returns:
            bool: True si le clonage a réussi
        """
        if tag_type.lower() == "em410x":
            command = f"lf em 410x clone {tag_id}"
        elif tag_type.lower() == "hid":
            command = f"lf hid clone {tag_id}"
        else:
            logger.error(f"Type de tag non supporté pour le clonage: {tag_type}")
            return False

        success, output = self.run_command(command, timeout=10)

        if success and ("done" in output.lower() or "success" in output.lower()):
            logger.info(f"Clonage {tag_type} réussi: {tag_id}")
            return True

        return False

    def rfid_simulate_em410x(self, tag_id: str) -> bool:
        """
        Simule un tag EM410x

        Args:
            tag_id: ID à simuler

        Returns:
            bool: True si la simulation démarre
        """
        command = f"lf em 410x sim {tag_id}"
        success, output = self.run_command(command, timeout=5)
        return success

    # ==================== Utilitaires ====================

    def wait_for_card(self, timeout: int = 30, card_type: str = "nfc") -> Optional[Dict[str, str]]:
        """
        Attend qu'une carte soit détectée

        Args:
            timeout: Timeout en secondes
            card_type: Type de carte ("nfc" ou "rfid")

        Returns:
            dict: Informations de la carte ou None
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            if card_type.lower() == "nfc":
                card_info = self.nfc_scan()
            else:
                card_info = self.rfid_scan()

            if card_info:
                return card_info

            time.sleep(0.5)

        return None

    def get_hardware_version(self) -> Optional[str]:
        """
        Récupère la version du hardware Proxmark

        Returns:
            str: Version ou None
        """
        success, output = self.run_command("hw version", timeout=5)

        if success:
            version_match = re.search(r"Proxmark3\s+([^\n]+)", output)
            if version_match:
                return version_match.group(1).strip()

        return None

    # ==================== Coffee module extensions ====================

    def emulate_mfc_from_file(self, nfc_path: Path) -> "EmulationHandle":
        """Start a MIFARE Classic 1K emulation from a Flipper .nfc file.

        Converts the file to a Proxmark3 .eml in a temp dir, loads it with
        hf mf eload, then starts hf mf sim.  Returns an EmulationHandle
        whose stop() terminates the simulation and cleans up.
        """
        from challenges.coffee.nfc_to_pm3_eml import parse_nfc, blocks_to_eml

        blocks = parse_nfc(nfc_path)
        eml_text = blocks_to_eml(blocks)

        tmp_dir = tempfile.mkdtemp(prefix="zr_coffee_")
        eml_file = Path(tmp_dir) / "badge.eml"
        eml_file.write_text(eml_text, encoding="utf-8")

        # Load the card image
        logger.info(f"Loading badge image from {eml_file}")
        ok, out = self.run_command(f"hf mf eload -f {eml_file}", timeout=15)
        if not ok and "not found" not in out.lower():
            # Some PM3 versions accept the command silently; log but continue
            logger.warning(f"hf mf eload returned non-zero: {out[:200]}")

        return EmulationHandle(self, eml_file)

    def read_block(self, block: int, key: bytes, key_type: str = "B") -> bytes:
        """Read a single 16-byte MIFARE Classic block.

        Args:
            block:    Block number (0-63).
            key:      6-byte authentication key.
            key_type: 'A' or 'B'.

        Returns:
            16 raw bytes.

        Raises:
            ProxmarkAuthError: when the card rejects the key.
            ProxmarkReadError: on other failures.
        """
        key_hex = key.hex().upper()
        command = f"hf mf rdbl --blk {block} --{key_type.lower()} --key {key_hex}"
        success, output = self.run_command(command, timeout=8)

        if not success:
            # Older PM3 CLI syntax
            command = f"hf mf rdbl {block} {key_type.upper()} {key_hex}"
            success, output = self.run_command(command, timeout=8)

        if "auth" in output.lower() and "fail" in output.lower():
            raise ProxmarkAuthError(f"Block {block} auth failed with key {key_hex}")

        # Parse hex data from output
        m = re.search(r"(?:data|block)\s*[:\|]\s*([0-9a-fA-F\s]{32,47})", output, re.IGNORECASE)
        if m:
            raw = bytes.fromhex(m.group(1).replace(" ", ""))
            if len(raw) == 16:
                return raw

        # Try plain 32-hex-char line
        for line in output.splitlines():
            cleaned = line.strip().replace(" ", "")
            if len(cleaned) == 32 and all(c in "0123456789abcdefABCDEF" for c in cleaned):
                return bytes.fromhex(cleaned)

        raise ProxmarkReadError(f"Could not parse block {block} data from: {output[:200]}")


class ProxmarkAuthError(RuntimeError):
    """PM3 authentication failure."""


class ProxmarkReadError(RuntimeError):
    """PM3 read failure (not auth-related)."""


class EmulationHandle:
    """Context for an active hf mf sim emulation session."""

    def __init__(self, pm3: "ProxmarkHandler", eml_file: Path):
        self._pm3 = pm3
        self._eml_file = eml_file
        self._log_lines: List[str] = []
        self._proc: Optional[subprocess.Popen] = None
        self._reader_thread: Optional[threading.Thread] = None
        self._running = False
        self._start()

    def _start(self) -> None:
        cmd = [
            self._pm3.client_path,
            self._pm3.port,
            "-c",
            "hf mf sim",
        ]
        try:
            self._proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            self._running = True
            self._reader_thread = threading.Thread(
                target=self._read_output, daemon=True
            )
            self._reader_thread.start()
            logger.info("PM3 MFC emulation started")
        except Exception as exc:
            logger.error(f"Failed to start PM3 emulation process: {exc}")
            raise

    def _read_output(self) -> None:
        try:
            assert self._proc and self._proc.stdout
            for line in self._proc.stdout:
                self._log_lines.append(line.rstrip())
                logger.debug(f"PM3 sim: {line.rstrip()}")
        except Exception:
            pass

    def read_log_lines(self) -> List[str]:
        """Return accumulated log lines from the emulation process."""
        return list(self._log_lines)

    def stop(self) -> None:
        """Terminate the emulation and clean up temp files."""
        self._running = False
        if self._proc is not None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=5)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
            self._proc = None
            logger.info("PM3 MFC emulation stopped")

        # Clean up temp eml
        try:
            self._eml_file.unlink(missing_ok=True)
            self._eml_file.parent.rmdir()
        except Exception:
            pass


# Test code
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
    )

    print("=" * 60)
    print("Test Proxmark Handler")
    print("=" * 60)

    pm = ProxmarkHandler()

    print("\n1. Version du Proxmark:")
    version = pm.get_hardware_version()
    if version:
        print(f"   ✓ {version}")
    else:
        print("   ✗ Non détecté")

    print("\n2. Scan NFC (5 secondes)...")
    nfc_card = pm.wait_for_card(timeout=5, card_type="nfc")
    if nfc_card:
        print(f"   ✓ Carte NFC détectée:")
        for key, value in nfc_card.items():
            print(f"     {key}: {value}")
    else:
        print("   - Aucune carte NFC détectée")

    print("\n3. Scan RFID 125kHz (5 secondes)...")
    rfid_tag = pm.wait_for_card(timeout=5, card_type="rfid")
    if rfid_tag:
        print(f"   ✓ Tag RFID détecté:")
        for key, value in rfid_tag.items():
            print(f"     {key}: {value}")
    else:
        print("   - Aucun tag RFID détecté")

    print("\n" + "=" * 60)
