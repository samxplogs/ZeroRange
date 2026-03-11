# Installation Proxmark3 pour ZeroRange

## Prérequis

- Raspberry Pi avec Raspbian/Raspberry Pi OS
- Proxmark3 RDV4 ou compatible
- Câble USB

## Installation du client Proxmark3

### 1. Installer les dépendances

```bash
sudo apt update
sudo apt install -y git build-essential libreadline-dev \
    gcc-arm-none-eabi libnewlib-dev qtbase5-dev \
    libbz2-dev liblz4-dev libbluetooth-dev libpython3-dev \
    libssl-dev
```

### 2. Cloner le repository Proxmark3

```bash
cd ~
git clone https://github.com/RfidResearchGroup/proxmark3.git
cd proxmark3
```

### 3. Compiler le client

```bash
make clean && make -j4
```

### 4. Installer le client

```bash
sudo make install
```

### 5. Configurer les permissions USB

```bash
sudo usermod -a -G dialout $USER
```

**Important**: Déconnectez-vous et reconnectez-vous pour que les changements de groupe prennent effet.

### 6. Vérifier l'installation

Connectez votre Proxmark3 via USB et exécutez:

```bash
proxmark3 /dev/ttyACM0
```

Vous devriez voir le prompt Proxmark3. Testez avec:

```
pm3 --> hw version
pm3 --> hw status
```

Quittez avec `quit` ou `Ctrl+D`.

## Configuration pour ZeroRange

Le module `proxmark_handler.py` de ZeroRange utilise le client Proxmark3 en ligne de commande.

### Port par défaut

Par défaut, ZeroRange utilise `/dev/ttyACM0`. Si votre Proxmark est sur un autre port, modifiez dans `zerorange.py`:

```python
self.proxmark = ProxmarkHandler(port="/dev/ttyACM1")  # ou autre port
```

### Vérifier le port

```bash
ls -l /dev/ttyACM*
```

## Tests des fonctionnalités

### Test NFC

```bash
cd ~/ZeroRange
python3 nfc_handler.py
```

Placez une carte NFC près du Proxmark pendant le test.

### Test RFID 125kHz

```bash
cd ~/ZeroRange
python3 rfid_handler.py
```

Placez un tag RFID 125kHz près du Proxmark pendant le test.

## Challenges disponibles

### NFC (30 points)

1. **Detect & Read** (10pts) - Détecter et lire une carte NFC
2. **Clone Card** (10pts) - Lire et dumper les données d'une carte NFC
3. **MIFARE Attack** (10pts) - Effectuer une attaque nested sur MIFARE Classic

### RFID 125kHz (30 points)

1. **Detect Tag** (10pts) - Détecter un tag RFID (EM410x, HID, Indala)
2. **Clone to T5577** (10pts) - Cloner un tag vers un T5577
3. **Simulate EM410x** (10pts) - Simuler un tag EM410x

## Dépannage

### Proxmark non détecté

1. Vérifiez la connexion USB:
   ```bash
   lsusb | grep -i proxmark
   ```

2. Vérifiez les permissions:
   ```bash
   groups | grep dialout
   ```

3. Reconnectez le Proxmark ou redémarrez le Raspberry Pi

### Timeout lors des commandes

- Augmentez le timeout dans `proxmark_handler.py` si nécessaire
- Vérifiez que le Proxmark répond manuellement: `proxmark3 /dev/ttyACM0 -c "hw version"`

### Mode simulation

Si le Proxmark n'est pas détecté, ZeroRange fonctionnera en mode simulation (logs uniquement, pas d'interaction réelle).

## Ressources

- Documentation Proxmark3: https://github.com/RfidResearchGroup/proxmark3/tree/master/doc
- Forum Proxmark3: https://forum.proxmark.org/
- Wiki ZeroRange: voir `docs/README.md`
