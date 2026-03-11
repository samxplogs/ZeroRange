# ✅ Configuration terminée - Prêt pour les tests!

## 🎯 Résumé de la configuration

### Configuration GPIO
- ✅ **GPIO 5 (Pin 29)**: DATA 1-Wire iButton
- ✅ **GPIO 6 (Pin 31)**: Pull-up 3.3V (OUTPUT HIGH)
- ✅ **GND (Pin 30)**: Ground
- ✅ **Interface 1-Wire**: Active et fonctionnelle

### Résultat des tests
```
[1/5] Configuration pull-up GPIO 6 (Pin 31)...
✓ GPIO 6 configuré en HIGH (3.3V)

[2/5] Vérification de l'interface 1-Wire...
✓ Interface 1-Wire trouvée

[3/5] Liste des périphériques 1-Wire...
✓ Trouvé 3 périphérique(s):
  - w1_bus_master1
  - 00-c00000000000
  - 00-400000000000

[4/5] Recherche d'iButtons (code famille 01-)...
⚠ Aucun iButton détecté (normal, rien de connecté)
```

**Status**: ✅ Système fonctionnel, prêt pour les tests

---

## 🔌 Câblage à effectuer

```
Raspberry Pi 5          Composants              iButton Probe
--------------          ----------              -------------

Pin 31 (GPIO 6) ------> [Résistance 4.7kΩ] --+
                                              |
Pin 29 (GPIO 5) ---------------------------->+---> DATA

Pin 30 (GND)    ----------------------------------> GND
```

### Schéma électrique
```
         GPIO 6 (Pin 31)
         OUTPUT HIGH (3.3V)
              │
              │
             ┌┴┐
             │ │  4.7kΩ
             └┬┘
              │
GPIO 5 ───────┼─────── DATA iButton
              │
             ─┴─
             GND
```

---

## 🧪 Commandes de test

### 1. Surveillance en temps réel (RECOMMANDÉ)

```bash
ssh user@RASPBERRY_IP
cd /home/sam/ZeroRange
sudo python3 monitor_ibutton_gpio5.py
```

**Ce que vous verrez**:
```
======================================================================
  SURVEILLANCE CONTINUE - iButton sur GPIO 5
======================================================================

  Pull-up: GPIO 6 (Pin 31) = HIGH ✓
  État: ACTIF
  Appuyez sur Ctrl+C pour arrêter

----------------------------------------------------------------------

[HH:MM:SS] ✓ DÉTECTÉ    | 01-XXXXXXXXXXXX (#1)
[HH:MM:SS] - RETIRÉ     | Probe libre
```

**Touchez le probe avec**:
- Un iButton physique via Flipper Zero (mode Read)
- Le Flipper Zero en mode Emulate

---

### 2. Test simple

```bash
ssh user@RASPBERRY_IP
cd /home/sam/ZeroRange
sudo python3 test_ibutton_gpio5.py
```

---

### 3. Configuration manuelle GPIO 6 (si nécessaire)

```bash
ssh user@RASPBERRY_IP
sudo python3 /home/sam/ZeroRange/setup_gpio6_pullup_v2.py
```

---

## 📋 Checklist matériel

Avant de tester, vérifier:

- [ ] **Résistance 4.7kΩ** connectée entre Pin 31 (GPIO 6) et Pin 29 (GPIO 5)
- [ ] **Pin 29 (GPIO 5)** connecté au DATA du probe iButton
- [ ] **Pin 30 (GND)** connecté au GND du probe iButton
- [ ] **Contacts du probe** propres et en bon état
- [ ] **iButton ou Flipper Zero** disponible pour test

---

## 🎮 Tests avec Flipper Zero

### Test 1: Lecture d'iButton physique

1. Avoir un iButton physique (DS1990A ou similaire)
2. **Flipper Zero** → iButton → **Read**
3. Approcher le Flipper du probe Raspberry Pi
4. Le monitoring devrait afficher: `✓ DÉTECTÉ | 01-XXXXXXXXXXXX`

### Test 2: Émulation iButton

1. **Flipper Zero** → iButton → **Saved**
2. Sélectionner un iButton sauvegardé
3. Appuyer sur **Emulate**
4. Approcher le Flipper du probe Raspberry Pi
5. Le monitoring devrait détecter l'ID émulé

### Test 3: Émulation manuelle

1. **Flipper Zero** → iButton → **Add Manually**
2. Entrer un ID (ex: `01-123456789ABC`)
3. Sauvegarder et **Emulate**
4. Approcher du probe
5. Vérifier que l'ID correspond

---

## 🚀 Lancer l'application complète ZeroRange

Une fois les tests réussis:

```bash
ssh user@RASPBERRY_IP
cd /home/sam/ZeroRange
sudo python3 zerorange.py
```

L'application va:
1. Configurer automatiquement GPIO 6 en pull-up
2. Initialiser l'écran LCD
3. Afficher le menu principal
4. Attendre vos commandes pour lancer les challenges

---

## 🐛 Troubleshooting

### Problème: "GPIO 6 non configuré"

**Solution**:
```bash
sudo python3 /home/sam/ZeroRange/setup_gpio6_pullup_v2.py
```

### Problème: "Aucun iButton détecté"

**Vérifier**:
1. Résistance 4.7kΩ bien placée entre Pin 31 et Pin 29
2. Câblage DATA sur Pin 29
3. GND bien connecté sur Pin 30
4. Flipper Zero en mode Emulate actif
5. Distance Flipper ↔ Probe < 1cm

### Problème: "Permission denied"

**Solution**: Toujours utiliser `sudo`
```bash
sudo python3 test_ibutton_gpio5.py
sudo python3 monitor_ibutton_gpio5.py
sudo python3 zerorange.py
```

### Problème: Détection intermittente

**Solutions**:
1. Vérifier la valeur de la résistance (doit être 4.7kΩ, pas 47kΩ)
2. Nettoyer les contacts du probe avec de l'alcool
3. Maintenir le Flipper stable sur le probe pendant 1-2 secondes
4. Vérifier la soudure de la résistance

---

## 📊 Fichiers disponibles

| Fichier | Description |
|---------|-------------|
| `setup_gpio6_pullup_v2.py` | Configuration GPIO 6 |
| `gpio_helper.py` | Module helper GPIO |
| `test_ibutton_gpio5.py` | Test complet |
| `monitor_ibutton_gpio5.py` | Surveillance temps réel |
| `zerorange.py` | Application principale |
| `WIRING_GPIO5_GPIO6.md` | Guide câblage détaillé |

---

## ✨ Prochaines étapes

1. ✅ **Câbler** la résistance 4.7kΩ selon le schéma
2. ✅ **Lancer** le monitoring: `sudo python3 monitor_ibutton_gpio5.py`
3. ✅ **Tester** avec Flipper Zero en mode Read ou Emulate
4. ✅ **Vérifier** que l'ID s'affiche correctement
5. 🎯 **Lancer** l'application: `sudo python3 zerorange.py`
6. 🎮 **Jouer** aux challenges iButton!

---

## 📞 Commandes utiles

```bash
# Connexion SSH
ssh user@RASPBERRY_IP

# Accès au répertoire
cd /home/sam/ZeroRange

# Monitoring (CTRL+C pour arrêter)
sudo python3 monitor_ibutton_gpio5.py

# Application complète
sudo python3 zerorange.py

# Vérifier GPIO 6
cat /sys/class/gpio/gpio6/value
# Devrait afficher: 1

# Logs
tail -f logs/zerorange.log
```

---

**🎯 Le système est prêt! Il ne reste plus qu'à câbler et tester avec le Flipper Zero!**

**Bon test! 🚀**
