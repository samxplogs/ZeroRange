# ZeroRange - Guide de démarrage rapide

## ✅ État actuel du système

### Matériel détecté et fonctionnel
- ✓ **Raspberry Pi 5** - En fonctionnement
- ✓ **Écran LCD I2C** - Connecté et opérationnel
- ✓ **Lecteur iButton USB** (c216:0101) - Détecté sur `/dev/input/event1`
- ⏳ **Proxmark3** - À connecter pour challenges NFC/RFID

### Logiciels installés
- ✓ ZeroRange application principale
- ✓ Module iButton USB (ibutton_usb_reader.py)
- ✓ Modules Proxmark3 (NFC + RFID)
- ✓ Base de données étendue (9 challenges)
- ✓ python3-evdev (pour lecteur USB)
- ✓ python3-flask et python3-flask-cors (pour interface web)

### Services en cours d'exécution
- ✓ **zerorange.py** - Application principale (PID 861)
- ✓ **HTTP server** - Port 8000 (interface web)
- ⏳ **LCD API server** - Port 5000 (nécessite configuration)

## 🎯 iButton de test officiels

### Challenge 1 & 2: `01-62397A010000FF`
### Challenge 3: `01-CAFE11111111D4`

Format avec espaces (Flipper Zero): `01 62 39 7A 01 00 00 FF` (pour challenges 1 & 2)

Ces iButtons sont utilisés pour les challenges:

#### Challenge 1: Touch & Read (10 pts)
- Placez l'iButton sur le lecteur USB
- Le système détectera automatiquement l'ID `01-62397A010000FF`
- Timeout: 60 secondes
- **ID attendu**: `01-62397A010000FF` ou `01 62 39 7A 01 00 00 FF`

#### Challenge 2: Clone iButton (10 pts)
**Étape 1**: Lecture
- Placez l'iButton de test sur le lecteur
- Le système lit l'ID `01-62397A010000FF`

**Étape 2**: Émulation
- Programmez votre émulateur avec l'ID `01-62397A010000FF`
- Présentez l'émulateur au lecteur pour validation
- **ID attendu**: `01-62397A010000FF` ou `01 62 39 7A 01 00 00 FF`

#### Challenge 3: Emulate Specific (10 pts)
- Le système attend un ID spécifique fixe
- Programmez votre émulateur/iButton avec l'ID `01-CAFE11111111D4`
- Présentez l'émulateur au lecteur pour validation
- Timeout: 120 secondes
- **ID attendu**: `01-CAFE11111111D4`

## 🌐 Interface Web

### Accès
**URL principale**: http://<RASPBERRY_PI_IP>:8000

> The Raspberry Pi gets its IP via DHCP. Check your router or run `hostname -I` on the Pi to find it.

### Pages disponibles
- **Home** (http://<RASPBERRY_PI_IP>:8000/home.html)
  - Simulation LCD en temps réel
  - Contrôle des boutons depuis le navigateur

- **Documentation** (http://<RASPBERRY_PI_IP>:8000/documentation.html)
  - Guide complet des challenges
  - Instructions d'utilisation

- **Contact** (http://<RASPBERRY_PI_IP>:8000/contact.html)
  - Informations de contact

### État actuel
- ✓ **Serveur HTTP actif** sur port 8000
- ⚠️ **API LCD** (port 5000) - En cours de configuration

Pour le moment, l'interface web affiche les pages mais le contrôle LCD en direct nécessite que l'API LCD soit fonctionnelle.

## 🎮 Utilisation du système

### Via LCD physique

#### Menu principal
```
[ZeroRange v1.0]
[1:iBut 2:NFC 3:RF]
```

- **BTN1**: iButton (Challenges 1-3) ✓ Fonctionnel
- **BTN2**: NFC (Challenges 4-6) - Nécessite Proxmark3
- **BTN3**: RFID (Challenges 7-9) - Nécessite Proxmark3
- **BTN5**: Paramètres

#### Dans un challenge
```
[Place iButton...]
[5:Skip   [60s]]
```

- Le countdown s'affiche en temps réel
- **BTN5**: Abandonner le challenge

### Score
- **Maximum**: 90 points
- **iButton**: 30 pts (3 × 10)
- **NFC**: 30 pts (3 × 10)
- **RFID**: 30 pts (3 × 10)

## 🔧 Commandes utiles

### Vérifier l'état du système
```bash
# Voir si ZeroRange tourne
ps aux | grep zerorange

# Voir le serveur web
ps aux | grep http.server

# Vérifier les ports
sudo netstat -tlnp | grep -E '(8000|5000)'
```

### Redémarrer ZeroRange
```bash
# Arrêter
sudo pkill -f zerorange.py

# Démarrer
cd /home/sam/ZeroRange
sudo python3 zerorange.py
```

### Tester l'iButton USB
```bash
cd /home/sam/ZeroRange
sudo python3 test_usb_ibutton.py

# Résultat attendu: 01-0000017A3962FF
```

### Voir les logs en temps réel
```bash
# Si lancé dans un terminal
cd /home/sam/ZeroRange
sudo python3 zerorange.py
# Les logs s'affichent directement
```

## 📊 Challenges disponibles

### ✓ iButton (Prêt à l'usage)
| # | Challenge | Points | Matériel requis |
|---|-----------|--------|-----------------|
| 1 | Touch & Read | 10 | iButton de test |
| 2 | Clone iButton | 10 | iButton de test + Émulateur |
| 3 | Emulate Specific | 10 | Émulateur programmable |

### ⏳ NFC (Nécessite Proxmark3)
| # | Challenge | Points | Matériel requis |
|---|-----------|--------|-----------------|
| 4 | Detect & Read | 10 | Carte NFC |
| 5 | Clone Card | 10 | Carte NFC + Carte vierge |
| 6 | MIFARE Attack | 10 | MIFARE Classic |

### ⏳ RFID 125kHz (Nécessite Proxmark3)
| # | Challenge | Points | Matériel requis |
|---|-----------|--------|-----------------|
| 7 | Detect Tag | 10 | Tag RFID 125kHz |
| 8 | Clone to T5577 | 10 | Tag RFID + T5577 |
| 9 | Simulate EM410x | 10 | Proxmark3 |

## 🔍 Dépannage rapide

### iButton non détecté
```bash
# Vérifier le lecteur USB
ls -la /dev/input/by-id/ | grep c216

# Devrait afficher:
# usb-c216_0101-event-kbd -> ../event1

# Test direct
sudo python3 test_usb_ibutton.py
```

### LCD non responsive
```bash
# Vérifier I2C
sudo i2cdetect -y 1

# Devrait montrer 0x27
```

### Site web non accessible
```bash
# Vérifier le serveur HTTP
curl http://localhost:8000/home.html

# Si erreur, relancer:
cd /home/sam/ZeroRange
python3 -m http.server 8000 &
```

## 📝 Prochaines étapes

### Pour utiliser NFC et RFID
1. Connecter le Proxmark3 via USB
2. Vérifier la détection: `lsusb | grep -i proxmark`
3. Installer le client Proxmark3 (voir `docs/PROXMARK_SETUP.md`)
4. Tester: `proxmark3 /dev/ttyACM0 -c "hw version"`

### Pour activer le contrôle LCD depuis le web
Le serveur API LCD nécessite une configuration supplémentaire pour fonctionner avec sudo. Pour le moment, utilisez:
- Le LCD physique pour interagir avec le système
- L'interface web pour consulter la documentation

## 📚 Documentation complète

- **README.md** - Documentation générale
- **USB_IBUTTON_INTEGRATION.md** - Détails lecteur USB
- **PROXMARK_INTEGRATION.md** - Intégration Proxmark3
- **PROXMARK_SETUP.md** - Installation Proxmark3

## 🎓 Commencer maintenant

1. **Allumez le Raspberry Pi** (déjà fait ✓)
2. **Regardez l'écran LCD** - Le menu principal s'affiche
3. **Appuyez sur BTN1** - Accéder au menu iButton
4. **Appuyez sur BTN1** - Lancer Challenge 1
5. **Placez l'iButton** `01-0000017A3962FF` sur le lecteur
6. **Succès!** +10 points

Le système est prêt à l'emploi pour les challenges iButton!

## ⚡ Résumé

- ✅ **Système principal**: Opérationnel
- ✅ **Challenges iButton**: Prêts (3/9 challenges)
- ✅ **Interface web**: Accessible en lecture seule
- ⏳ **Challenges NFC/RFID**: Nécessitent Proxmark3
- 🎯 **iButton de test**: `01-0000017A3962FF`
