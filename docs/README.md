# ZeroRange - Documentation

## Vue d'ensemble

ZeroRange est un système d'entraînement pour Flipper Zero utilisant un Raspberry Pi avec écran LCD et divers périphériques de sécurité physique.

## Matériel

### Composants principaux
- **Raspberry Pi 5** (8GB RAM)
- **Écran LCD I2C** 16x2 avec 5 boutons
- **Lecteur iButton USB** (HID c216:0101)
- **Proxmark3** (pour NFC et RFID 125kHz)

### iButton de test
**ID Challenge 1 & 2**: `01-62397A010000FF` (ou format avec espaces: `01 62 39 7A 01 00 00 FF`)
**ID Challenge 3**: `01-CAFE11111111D4`

Ces iButtons sont utilisés pour les challenges:
- **Challenge 1** (Touch & Read): Détecte et lit l'iButton `01-62397A010000FF`
- **Challenge 2** (Clone): Lit `01-62397A010000FF` puis émule le même ID
- **Challenge 3** (Emulate Specific): Émule l'ID fixe `01-CAFE11111111D4`

## Challenges disponibles

### iButton (30 points)
1. **Touch & Read** (10pts) - Détecter et lire l'iButton de test
   - Timeout: 60 secondes
   - **ID attendu**: `01-62397A010000FF`
   - Place l'iButton physique ou émule cet ID avec ton Flipper Zero

2. **Clone iButton** (10pts) - Lire puis émuler l'iButton
   - Étape 1: Lire l'iButton de test (45s)
   - Étape 2: Émuler le même ID (45s)
   - **ID attendu**: `01-62397A010000FF`

3. **Emulate Specific** (10pts) - Émuler un ID spécifique
   - **ID attendu**: `01-CAFE11111111D4`
   - Timeout: 120 secondes
   - Programme ton Flipper Zero ou T5577 avec cet ID exact

### NFC (30 points)
4. **Detect & Read** (10pts) - Détecter une carte NFC
   - Timeout: 60 secondes
   - Support: MIFARE Classic, Ultralight, NTAG, DESFire

5. **Clone Card** (10pts) - Lire et dumper une carte NFC
   - Étape 1: Lire la carte originale (45s)
   - Étape 2: Vérifier la lecture (45s)

6. **MIFARE Attack** (10pts) - Attaque nested sur MIFARE Classic
   - Timeout: 60 secondes
   - Nécessite une carte MIFARE Classic

### RFID 125kHz (30 points)
7. **Detect Tag** (10pts) - Détecter un tag RFID
   - Timeout: 60 secondes
   - Support: EM410x, HID Prox, Indala

8. **Clone to T5577** (10pts) - Cloner vers T5577
   - Étape 1: Lire le tag original (45s)
   - Étape 2: Cloner vers T5577 et vérifier (45s)

9. **Simulate EM410x** (10pts) - Simuler un tag EM410x
   - Timeout: 60 secondes
   - Nécessite un tag EM410x

## Score total
**90 points maximum** (9 challenges × 10 points)

## Interface LCD

### Navigation
- **BTN1**: iButton (challenges 1-3)
- **BTN2**: NFC (challenges 4-6)
- **BTN3**: RFID (challenges 7-9)
- **BTN4**: Infrarouge (à venir)
- **BTN5**: Paramètres / Retour

### Menu iButton/NFC/RFID
- **BTN1**: Challenge 1
- **BTN2**: Challenge 2
- **BTN3**: Challenge 3
- **BTN5**: Retour au menu principal

### Pendant un challenge
- **BTN5**: Skip (abandonner)
- Countdown visible sur LCD

## Interface Web

### Pages disponibles
- **Home** (`/`) - LCD simulator en direct
- **Documentation** (`/docs`) - Documentation complète
- **Contact** (`/contact`) - Informations de contact

### Lancement des serveurs web

```bash
cd /home/sam/ZeroRange/web

# Terminal 1: Serveur HTTP (port 8000)
python3 -m http.server 8000

# Terminal 2: API LCD (port 5000)
sudo python3 /home/sam/ZeroRange/web_lcd_server.py
```

### Accès
- **Interface web**: http://<RASPBERRY_PI_IP>:8000
- **API LCD**: http://<RASPBERRY_PI_IP>:5000

### Fonctionnalités web
- Simulation LCD en temps réel
- Contrôle des boutons depuis le navigateur
- Synchronisation avec le LCD physique

## Installation

### Prérequis système
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-smbus python3-evdev
sudo apt-get install -y i2c-tools git
```

### Configuration I2C
```bash
sudo raspi-config
# Interface Options → I2C → Enable
sudo reboot
```

### Installation Python
```bash
cd /home/sam/ZeroRange
pip3 install -r requirements.txt
sudo apt-get install python3-adafruit-circuitpython-charlcd
```

### Installation Proxmark3
Voir [PROXMARK_SETUP.md](PROXMARK_SETUP.md) pour les instructions détaillées.

## Utilisation

### Lancement du système principal
```bash
cd /home/sam/ZeroRange
sudo python3 zerorange.py
```

**Note**: `sudo` est requis pour:
- Accès au lecteur USB iButton (`/dev/input/event1`)
- Accès I2C pour le LCD
- Accès au Proxmark3 (`/dev/ttyACM0`)

### Tests individuels

#### Test iButton USB
```bash
sudo python3 test_usb_ibutton.py
```

#### Test NFC
```bash
sudo python3 nfc_handler.py
```

#### Test RFID
```bash
sudo python3 rfid_handler.py
```

## Base de données

**Fichier**: `scores.db` (SQLite)

### Tables

#### challenges
```sql
CREATE TABLE challenges (
    id INTEGER PRIMARY KEY,
    module TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    points INTEGER NOT NULL,
    completed BOOLEAN DEFAULT 0,
    best_time INTEGER DEFAULT NULL
);
```

#### history
```sql
CREATE TABLE history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    challenge_id INTEGER NOT NULL,
    success BOOLEAN NOT NULL,
    time_taken INTEGER NOT NULL,
    FOREIGN KEY (challenge_id) REFERENCES challenges(id)
);
```

### Réinitialisation des scores
Via le menu LCD: Paramètres → Reset → Confirm

## Architecture logicielle

```
ZeroRange
├── zerorange.py              # Application principale
├── lcd_manager.py            # Gestion LCD I2C
├── database.py               # Gestion SQLite
├── ibutton_handler.py        # Challenges iButton
├── ibutton_usb_reader.py     # Lecteur USB iButton
├── nfc_handler.py            # Challenges NFC
├── rfid_handler.py           # Challenges RFID
├── proxmark_handler.py       # Interface Proxmark3
├── web_lcd_server.py         # API Flask pour web
└── web/                      # Interface web
    ├── home.html
    ├── documentation.html
    └── contact.html
```

## Configuration

### config.json
```json
{
    "lcd": {
        "i2c_address": "0x27",
        "columns": 16,
        "rows": 2
    },
    "hardware": {
        "ibutton": {
            "usb_device": "/dev/input/event1"
        },
        "proxmark": {
            "port": "/dev/ttyACM0"
        }
    },
    "web": {
        "host": "0.0.0.0",
        "port_http": 8000,
        "port_api": 5000
    }
}
```

## Dépannage

### LCD non détecté
```bash
# Vérifier I2C
sudo i2cdetect -y 1

# Doit afficher 0x27 ou 0x3f
```

### iButton non lu
```bash
# Vérifier le périphérique USB
ls -la /dev/input/by-id/ | grep c216

# Tester directement
sudo python3 test_usb_ibutton.py

# ID attendu: 01-0000017A3962FF
```

### Proxmark non détecté
```bash
# Vérifier USB
lsusb | grep -i proxmark

# Vérifier le port
ls -la /dev/ttyACM*

# Test manuel
proxmark3 /dev/ttyACM0 -c "hw version"
```

### Serveurs web non accessibles
```bash
# Vérifier les ports
sudo netstat -tlnp | grep -E '(8000|5000)'

# Relancer les serveurs
cd /home/sam/ZeroRange/web
python3 -m http.server 8000 &
cd /home/sam/ZeroRange
sudo python3 web_lcd_server.py &
```

## Logs

Les logs sont affichés sur stdout avec le format:
```
[TIMESTAMP] [LEVEL] [MODULE] Message
```

**Niveaux**:
- DEBUG: Détails techniques
- INFO: Actions utilisateur
- WARNING: Problèmes non bloquants
- ERROR: Erreurs nécessitant attention

## Sécurité

- Les serveurs web sont accessibles en local uniquement (LAN)
- Pas d'authentification (usage en environnement de formation)
- Base de données locale non chiffrée
- Exécution en root pour accès matériel

## Maintenance

### Backup de la base de données
```bash
cp scores.db scores.db.backup
```

### Mise à jour du code
```bash
cd /home/sam/ZeroRange
git pull  # Si repository Git configuré
```

### Redémarrage complet
```bash
sudo pkill -f zerorange.py
sudo python3 zerorange.py
```

## Ressources

- [Proxmark3 Documentation](https://github.com/RfidResearchGroup/proxmark3)
- [Adafruit LCD Guide](https://learn.adafruit.com/character-lcds/)
- [iButton Protocol](https://www.maximintegrated.com/en/products/ibutton.html)

## Support

Pour toute question ou problème:
- Consulter les logs en temps réel
- Vérifier les connexions matérielles
- Tester chaque module individuellement
- Consulter la documentation spécifique (PROXMARK_SETUP.md, USB_IBUTTON_INTEGRATION.md)
