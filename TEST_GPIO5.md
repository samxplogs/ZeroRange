# 🔧 Test iButton sur GPIO 5 - Résumé

## ✅ Configuration effectuée

### 1. Mise à jour de la configuration

- **GPIO**: Changé de GPIO 4 à GPIO 5
- **Fichier modifié**: `/boot/firmware/config.txt`
- **Ligne ajoutée**: `dtoverlay=w1-gpio,gpiopin=5`
- **Module rechargé**: Interface 1-Wire activée

### 2. Fichiers mis à jour

| Fichier | Changement |
|---------|------------|
| `config.json` | w1_gpio: 5 |
| `install.sh` | GPIO 5 configuration |
| `README.md` | Documentation GPIO 5 |
| `test_ibutton_gpio5.py` | Script de test créé |
| `monitor_ibutton_gpio5.py` | Surveillance continue créée |

## 🧪 Tests disponibles

### Test 1: Vérification simple

```bash
ssh user@RASPBERRY_IP
cd /home/sam/ZeroRange
python3 test_ibutton_gpio5.py
```

**Ce que le test vérifie**:
1. Interface 1-Wire présente
2. Périphériques détectés
3. iButtons connectés (code famille 01-)
4. Lecture de l'ID

### Test 2: Surveillance continue

```bash
ssh user@RASPBERRY_IP
cd /home/sam/ZeroRange
python3 monitor_ibutton_gpio5.py
```

**Fonctionnalités**:
- Affichage en temps réel
- Détection instantanée des iButtons
- Compteur de détections
- Ctrl+C pour arrêter

### Test 3: Vérification manuelle

```bash
# Se connecter au Pi
ssh user@RASPBERRY_IP

# Vérifier l'interface 1-Wire
ls /sys/bus/w1/devices/

# Attendre qu'un iButton soit touché au probe, puis:
cat /sys/bus/w1/devices/01-*/id
```

## 📋 Résultat du dernier test

```
============================================================
Test iButton - GPIO 5
============================================================

[1/4] Vérification de l'interface 1-Wire...
✓ Interface 1-Wire trouvée

[2/4] Liste des périphériques 1-Wire...
✓ Trouvé 1 périphérique(s):
  - w1_bus_master1

[3/4] Recherche d'iButtons (code famille 01-)...
⚠ Aucun iButton détecté (normal si rien connecté)
```

**Statut**: ✅ Interface fonctionnelle, en attente d'iButton

## 🔌 Câblage à vérifier

```
Raspberry Pi 5          iButton Probe
--------------          -------------
GPIO 5 (Pin 29) ------> DATA
3.3V (Pin 1)    ------> Résistance 4.7kΩ ----+
                                              |
                        DATA <----------------+
GND (Pin 6)     ------> GND
```

**Points de vérification**:
- [ ] Résistance pull-up 4.7kΩ installée
- [ ] Connexion DATA sur GPIO 5
- [ ] GND connecté
- [ ] Contacts du probe propres

## 🎯 Test avec Flipper Zero

### Méthode 1: Lecture d'un iButton physique

1. Avoir un iButton physique (ex: DS1990A)
2. Flipper Zero → iButton → Read
3. Toucher le probe Raspberry Pi avec le Flipper
4. Le monitoring devrait afficher l'ID

### Méthode 2: Émulation

1. Flipper Zero → iButton → Saved
2. Sélectionner un iButton sauvegardé
3. Appuyer sur "Emulate"
4. Toucher le probe Raspberry Pi
5. L'ID devrait être détecté

### Méthode 3: Émulation manuelle

1. Flipper Zero → iButton → Add Manually
2. Entrer un ID (ex: 01-123456789ABC)
3. Sauvegarder
4. Emulate
5. Toucher le probe

## 🚀 Commandes rapides

### Relancer l'interface 1-Wire

```bash
ssh user@RASPBERRY_IP
sudo modprobe -r w1_gpio
sudo modprobe w1_gpio
```

### Voir les logs en direct

```bash
ssh user@RASPBERRY_IP
tail -f /home/sam/ZeroRange/logs/zerorange.log
```

### Lancer l'application complète

```bash
ssh user@RASPBERRY_IP
cd /home/sam/ZeroRange
python3 zerorange.py
```

## 📊 Prochaines étapes

1. **Tester avec un iButton physique** ou Flipper Zero
2. **Vérifier la détection** avec `monitor_ibutton_gpio5.py`
3. **Si détection OK**: Lancer l'application complète
4. **Si pas de détection**: Vérifier le câblage et la résistance pull-up

## 🐛 Troubleshooting

### Problème: w1_bus_master1 absent

```bash
# Vérifier la configuration
cat /boot/firmware/config.txt | grep w1-gpio

# Devrait afficher: dtoverlay=w1-gpio,gpiopin=5

# Si absent, ajouter et redémarrer
sudo nano /boot/firmware/config.txt
# Ajouter: dtoverlay=w1-gpio,gpiopin=5
sudo reboot
```

### Problème: Interface présente mais pas de détection

1. Vérifier la résistance pull-up (4.7kΩ)
2. Tester avec un autre iButton
3. Nettoyer les contacts du probe
4. Vérifier les soudures

### Problème: Détection intermittente

1. Fils trop longs → utiliser des fils courts
2. Interférences → éloigner des sources électriques
3. Contacts sales → nettoyer avec de l'alcool
4. Résistance incorrecte → vérifier 4.7kΩ

## 📖 Documentation

- [GPIO5_SETUP.md](GPIO5_SETUP.md) - Guide complet de configuration
- [README.md](README.md) - Documentation principale
- [config.json](config.json) - Configuration actuelle

## ✨ Commandes favorites

```bash
# Test rapide
cd /home/sam/ZeroRange && python3 test_ibutton_gpio5.py

# Surveillance
cd /home/sam/ZeroRange && python3 monitor_ibutton_gpio5.py

# Application complète
cd /home/sam/ZeroRange && python3 zerorange.py
```

---

**Status**: Configuration GPIO 5 terminée ✅
**Prêt pour**: Tests avec Flipper Zero 🎯
