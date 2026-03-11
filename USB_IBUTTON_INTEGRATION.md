# Intégration lecteur iButton USB - ZeroRange

## Résumé

Migration complète de l'interface GPIO 1-Wire vers lecteur USB HID pour les challenges iButton.

## Matériel détecté

- **Périphérique**: HID c216:0101
- **Type**: USB HID Keyboard emulation
- **Device**: /dev/input/event1
- **Symlink**: /dev/input/by-id/usb-c216_0101-event-kbd

## Fichiers créés

### 1. `ibutton_usb_reader.py`
Module de lecture iButton via USB HID avec émulation clavier.

**Fonctionnalités:**
- Lecture asynchrone en arrière-plan (thread)
- Parsing automatique des scancodes HID
- Support format 16 caractères hex
- Callback pour notification immédiate
- Mode blocking et mode asynchrone

**API:**
```python
reader = IButtonUSBReader("/dev/input/event1")

# Mode blocking (simple)
ibutton_id = reader.read_blocking(timeout=30)

# Mode asynchrone (avec callback)
def on_detected(ibutton_id):
    print(f"Detected: {ibutton_id}")

reader.start(callback=on_detected)
# ... faire autre chose ...
reader.stop()
```

### 2. `test_usb_ibutton.py`
Script de test rapide pour vérifier le fonctionnement du lecteur.

**Usage:**
```bash
sudo python3 test_usb_ibutton.py
```

## Fichiers modifiés

### 1. `ibutton_handler.py`
**Modifications majeures:**

- **Suppression**: Interface 1-Wire GPIO complète
- **Ajout**: Support lecteur USB HID
- **Méthode read_ibutton()**: Simplifié, retourne last_detected_id
- **Méthode wait_for_ibutton()**: Utilise reader.start() avec callback
- **Méthode wait_ibutton_removed()**: Simplifié (USB envoie l'ID une seule fois)
- **Challenge 3**: Adapté pour utiliser le mode asynchrone du reader
- **Ajout close()**: Fermeture propre du reader USB

**Avant (GPIO):**
```python
def __init__(self, lcd):
    self.lcd = lcd
    self.w1_base = "/sys/bus/w1/devices/"
    # Vérification 1-Wire...

def read_ibutton(self):
    devices = os.listdir(self.w1_base)
    ibutton_devices = [d for d in devices if d.startswith("01-")]
    # Lecture depuis /sys/bus/w1/...
```

**Après (USB):**
```python
def __init__(self, lcd, usb_device="/dev/input/event1"):
    self.lcd = lcd
    self.usb_device = usb_device
    self.reader = IButtonUSBReader(usb_device)
    self.last_detected_id = None

def _on_ibutton_detected(self, ibutton_id):
    self.last_detected_id = ibutton_id

def read_ibutton(self):
    return self.last_detected_id
```

## Dépendances

### Nouvelle dépendance: python3-evdev

**Installation:**
```bash
sudo apt-get install python3-evdev
```

**Statut**: ✓ Installé sur Raspberry Pi

## Permissions

Le lecteur USB nécessite l'accès aux périphériques /dev/input/eventX.

**Méthode 1: Root (temporaire)**
```bash
sudo python3 zerorange.py
```

**Méthode 2: Groupe input (permanent)**
```bash
sudo usermod -a -G input sam
# Déconnexion/reconnexion requise
```

## Tests effectués

### Test 1: Détection périphérique USB ✓
```bash
lsusb
# Bus 001 Device 002: ID c216:0101 Card Device Expert Co., LTD
```

### Test 2: Périphérique input ✓
```bash
ls -la /dev/input/by-id/
# usb-c216_0101-event-kbd -> ../event1
```

### Test 3: Lecture directe ✓
```bash
sudo python3 test_usb_ibutton.py
# ✓ SUCCESS! iButton ID: 01-0000017A3962FF
```

**iButton de test officiel**: `01-0000017A3962FF`

Cet iButton est utilisé comme référence pour tous les challenges:
- **Challenge 1** (Touch & Read): Détection de cet ID spécifique
- **Challenge 2** (Clone): Lecture puis émulation de cet ID
- **Challenge 3** (Emulate Specific): Génération d'ID aléatoires à émuler

## Architecture

```
ZeroRange
├── ibutton_usb_reader.py (NEW)
│   ├── Class: IButtonUSBReader
│   │   ├── __init__(device_path)
│   │   ├── start(callback)          # Mode asynchrone
│   │   ├── stop()
│   │   ├── read_blocking(timeout)   # Mode simple
│   │   └── close()
│   └── Thread: _read_loop()         # Lecture événements HID
│
└── ibutton_handler.py (MODIFIED)
    ├── __init__(lcd, usb_device)    # Plus de GPIO
    ├── wait_for_ibutton(timeout)    # Utilise USB reader
    ├── challenge_1_touch()          # Inchangé
    ├── challenge_2_clone()          # Inchangé
    ├── challenge_3_emulate()        # Adapté pour USB async
    └── close()                      # NEW - Fermeture propre
```

## Avantages lecteur USB vs GPIO

| Aspect | GPIO 1-Wire | USB HID |
|--------|-------------|---------|
| **Câblage** | Complexe (pull-up, GPIO) | Simple (USB) |
| **Fiabilité** | Parasites, résistance critique | Stable, pas de bruit |
| **Vitesse** | Lent (1-Wire protocol) | Instantané |
| **Détection** | Polling continu | Événement instantané |
| **Ressources** | CPU polling | Thread événementiel |
| **Setup** | dtoverlay, w1-gpio | Plug & Play |

## Format ID iButton

Le lecteur USB envoie l'ID en hexadécimal via émulation clavier.

**Format reçu**: 16 caractères hexadécimaux
```
0000017A3962FF
├─┬─┘└──┬───┘└┬┘
│ │     │     └─ CRC (2 hex)
│ │     └─────── Serial Number (6 bytes = 12 hex)
│ └───────────── (padding/firmware specific)
└─────────────── Family Code (01 = DS1990A)
```

**Format ZeroRange**: `01-XXXXXXXXXXXX`
```python
# Parser dans ibutton_usb_reader.py
if len(cleaned) == 16:
    return f"{cleaned[:2]}-{cleaned[2:]}"  # "01-0000017A3962FF"
```

## Fichiers de configuration

**Aucune modification nécessaire** - Le paramètre GPIO dans config.json n'est plus utilisé.

## Lancement du système

```bash
cd /home/sam/ZeroRange
sudo python3 zerorange.py
```

Le système détectera automatiquement le lecteur USB iButton sur /dev/input/event1.

## Dépannage

### Lecteur non détecté
```bash
# Vérifier USB
lsusb | grep c216

# Vérifier input device
ls -la /dev/input/by-id/ | grep c216

# Tester directement
sudo python3 test_usb_ibutton.py
```

### Permission denied
```bash
# Ajouter au groupe input
sudo usermod -a -G input $USER
# Puis déconnexion/reconnexion

# Ou lancer en root
sudo python3 zerorange.py
```

### iButton non lu
1. Vérifier que l'iButton est bien placé sur le lecteur
2. Le lecteur émet généralement un bip à la lecture
3. Tester avec `test_usb_ibutton.py` d'abord

### Multiple détections
Le lecteur USB envoie l'ID **une seule fois** par placement. C'est normal et géré par le code:
- `last_detected_id` est réinitialisé après utilisation
- Pas besoin de "retirer" l'iButton comme avec GPIO

## Prochaines étapes

1. ✓ Lecteur USB détecté et fonctionnel
2. ✓ Module ibutton_usb_reader créé
3. ✓ ibutton_handler adapté
4. ✓ Test basique réussi (ID: 01-0000017A3962FF)
5. ⏳ Test des 3 challenges avec LCD
6. ⏳ Test intégration complète avec zerorange.py

## Notes

- Le lecteur USB **ne nécessite plus** de GPIO ni de résistance pull-up
- Les anciens scripts GPIO (test_ibutton_gpio5.py, etc.) sont **obsolètes**
- La détection est **beaucoup plus fiable** qu'avec GPIO 1-Wire
- Les challenges restent **identiques** du point de vue utilisateur
