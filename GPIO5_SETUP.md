# Configuration GPIO 5 pour iButton

Guide rapide pour configurer le lecteur iButton sur GPIO 5.

## 🔧 Prérequis

- Raspberry Pi 5 ou Pi 4
- Raspberry Pi OS installé
- Lecteur iButton DS9092 ou compatible
- Résistance pull-up 4.7kΩ

## 📋 Étapes d'installation

### 1. Activer l'interface 1-Wire sur GPIO 5

Ouvrir le fichier de configuration:
```bash
sudo nano /boot/config.txt
```

Ajouter cette ligne à la fin du fichier:
```
dtoverlay=w1-gpio,gpiopin=5
```

Sauvegarder et quitter (Ctrl+X, puis Y, puis Entrée).

### 2. Redémarrer le Raspberry Pi

```bash
sudo reboot
```

### 3. Vérifier l'interface 1-Wire

Après le redémarrage, vérifier que l'interface est active:

```bash
ls -la /sys/bus/w1/devices/
```

Vous devriez voir au moins `w1_bus_master1`.

### 4. Tester le lecteur iButton

Utiliser le script de test fourni:

```bash
cd /path/to/ZeroRange
python3 test_ibutton_gpio5.py
```

Le script va:
1. ✓ Vérifier l'interface 1-Wire
2. ✓ Lister les périphériques connectés
3. ✓ Détecter les iButtons (code famille 01-)
4. ✓ Lire l'ID de l'iButton

### 5. Mode surveillance continue

Pour surveiller en continu la détection des iButtons:

```bash
python3 test_ibutton_gpio5.py
# Répondre 'o' quand demandé
```

Appuyez sur Ctrl+C pour arrêter.

## 🔌 Câblage

```
Raspberry Pi 5          iButton Probe DS9092
--------------          --------------------
GPIO 5 (Pin 29) ------> DATA (avec résistance 4.7kΩ vers 3.3V)
3.3V (Pin 1)    ------> Pull-up résistance (4.7kΩ)
GND (Pin 6)     ------> GND
```

**Important**: N'oubliez pas la résistance pull-up de 4.7kΩ entre DATA et 3.3V!

## 📊 Schéma de connexion

```
         3.3V
          │
          │
         ┌┴┐
         │ │  4.7kΩ
         └┬┘
          │
GPIO5 ────┼──── DATA (iButton Probe)
          │
         ─┴─
         GND
```

## ✅ Vérification manuelle

Tester avec un iButton physique:

```bash
# 1. Lister les périphériques 1-Wire
ls /sys/bus/w1/devices/

# 2. Si un iButton est connecté, vous verrez quelque chose comme:
# 01-xxxxxxxxxxxx

# 3. Lire l'ID de l'iButton
cat /sys/bus/w1/devices/01-*/id
```

## 🐛 Dépannage

### Problème: Interface 1-Wire non trouvée

**Symptôme**: `/sys/bus/w1/devices/` n'existe pas

**Solution**:
1. Vérifier que la ligne est bien dans `/boot/config.txt`:
   ```bash
   cat /boot/config.txt | grep w1-gpio
   ```
2. Redémarrer si nécessaire
3. Vérifier les permissions du fichier config.txt

### Problème: Aucun iButton détecté

**Symptôme**: Seul `w1_bus_master1` apparaît

**Solutions possibles**:
1. Vérifier le câblage (DATA, GND)
2. Vérifier la résistance pull-up (4.7kΩ)
3. Tester avec un autre iButton
4. Vérifier les contacts du probe

### Problème: Détection intermittente

**Solutions**:
1. Nettoyer les contacts du probe
2. Vérifier la soudure de la résistance pull-up
3. Utiliser des fils plus courts
4. Vérifier l'alimentation 3.3V stable

## 🧪 Tests avec Flipper Zero

Pour tester avec le Flipper Zero:

1. **Mode lecture**:
   - Flipper Zero → iButton → Read
   - Toucher le probe avec le Flipper
   - Le Raspberry Pi devrait détecter l'iButton

2. **Mode émulation**:
   - Flipper Zero → iButton → Saved → Sélectionner un iButton
   - Emulate
   - Toucher le probe avec le Flipper
   - Le Raspberry Pi devrait lire l'ID émulé

## 📝 Notes importantes

- GPIO 5 = Pin physique 29 sur le Raspberry Pi
- Le pull-up de 4.7kΩ est **obligatoire**
- Ne pas connecter de tension supérieure à 3.3V
- Utiliser des fils courts pour éviter les interférences
- Le polling est fait toutes les 200-300ms

## 🚀 Lancer l'application complète

Une fois les tests réussis:

```bash
cd /path/to/ZeroRange
python3 zerorange.py
```

Ou activer le service systemd:

```bash
sudo systemctl start zerorange
sudo systemctl status zerorange
```

## 📖 Ressources

- [Documentation Raspberry Pi GPIO](https://pinout.xyz/)
- [Datasheet DS9092](https://www.maximintegrated.com/en/products/ibutton-one-wire/ibutton/DS9092.html)
- [1-Wire Protocol](https://www.maximintegrated.com/en/products/ibutton-one-wire/one-wire.html)

---

**Bon test! 🎯**
