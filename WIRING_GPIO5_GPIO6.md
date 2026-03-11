# 🔌 Câblage iButton - GPIO 5 + GPIO 6 Pull-up

## Configuration choisie: Solution 1
**GPIO 6 (Pin 31) comme source 3.3V pour pull-up**

---

## 📍 Schéma de câblage

```
Raspberry Pi 5          Composants              iButton Probe
--------------          ----------              -------------

Pin 31 (GPIO 6) ------> [Résistance 4.7kΩ] --+
                                              |
Pin 29 (GPIO 5) ---------------------------->+---> DATA

Pin 30 (GND)    ----------------------------------> GND
```

---

## 🎯 Connexions détaillées

### 1. Pull-up (3.3V via GPIO 6)
```
Pin 31 (GPIO 6) --> Une extrémité de la résistance 4.7kΩ
```

### 2. Ligne DATA
```
Pin 29 (GPIO 5) --> DATA du probe iButton
                --> Autre extrémité de la résistance 4.7kΩ
```

### 3. Ground
```
Pin 30 (GND) --> GND du probe iButton
```

---

## 🛠️ Matériel nécessaire

- ✅ **1 résistance 4.7kΩ** (ou entre 4.7kΩ et 10kΩ)
- ✅ **3 fils Dupont femelle-femelle** (ou adaptés à vos connecteurs)
- ✅ **iButton probe DS9092** (ou compatible)
- ✅ **Breadboard** (optionnel, facilite le montage)

---

## 📐 Schéma avec breadboard

```
Raspberry Pi 5          Breadboard                iButton Probe
--------------          ----------                -------------

Pin 31 (GPIO 6) ------> Rail (+) ----+
                                     |
                                   [4.7kΩ]
                                     |
Pin 29 (GPIO 5) ------> Rail DATA <--+--------> DATA

Pin 30 (GND)    ------> Rail (-)  -------------> GND
```

---

## 📊 Schéma électrique détaillé

```
         GPIO 6 (Pin 31)
         OUTPUT HIGH (3.3V)
              │
              │
             ┌┴┐
             │ │  Résistance 4.7kΩ
             │ │  (Pull-up)
             └┬┘
              │
              ├─────────── GPIO 5 (Pin 29) [1-Wire DATA]
              │
              └─────────── DATA iButton Probe


             GND (Pin 30) ──── GND iButton Probe
```

---

## 🔢 Localisation des pins

```
Raspberry Pi 5 - Pins 27-40 (Zone libre)

27 28
29 30  ← GPIO 5 (Pin 29) + GND (Pin 30)
31 32  ← GPIO 6 (Pin 31)
33 34
35 36
37 38
39 40
```

**Pins utilisés**:
- **Pin 29**: GPIO 5 (DATA 1-Wire)
- **Pin 30**: GND
- **Pin 31**: GPIO 6 (Pull-up 3.3V)

---

## ⚡ Configuration logicielle

Le code active automatiquement GPIO 6:

```python
# GPIO 6 configuré en OUTPUT HIGH (3.3V)
# Cela fournit 3.3V pour la résistance pull-up
```

Pas de configuration manuelle nécessaire!

---

## ✅ Vérification du câblage

### Étape 1: Vérifier les connexions physiques

```bash
# Se connecter au Pi
ssh user@RASPBERRY_IP

# Configurer GPIO 6 en pull-up
sudo python3 /home/sam/ZeroRange/setup_gpio6_pullup.py
```

**Résultat attendu**:
```
✓ GPIO 6 exporté
✓ GPIO 6 configuré en OUTPUT
✓ GPIO 6 = HIGH (3.3V)
```

### Étape 2: Vérifier l'interface 1-Wire

```bash
ls /sys/bus/w1/devices/
```

**Résultat attendu**: `w1_bus_master1`

### Étape 3: Tester la détection

```bash
sudo python3 /home/sam/ZeroRange/monitor_ibutton_gpio5.py
```

Toucher le probe avec un iButton → Devrait afficher l'ID

---

## 🔍 Troubleshooting

### Problème 1: Aucun périphérique détecté

**Vérifier**:
1. Résistance 4.7kΩ bien connectée entre Pin 31 et Pin 29
2. DATA du probe bien sur Pin 29
3. GND du probe bien sur Pin 30

### Problème 2: GPIO 6 ne s'active pas

**Solution**:
```bash
# Exécuter avec sudo
sudo python3 setup_gpio6_pullup.py

# Vérifier l'état
cat /sys/class/gpio/gpio6/value
# Devrait afficher: 1
```

### Problème 3: Détection intermittente

**Solutions**:
1. Vérifier que la résistance est bien 4.7kΩ (pas 47kΩ ou 470Ω)
2. Utiliser des fils courts
3. Vérifier les soudures/contacts
4. Nettoyer le probe iButton

### Problème 4: "Device or resource busy"

**Solution**:
```bash
# Reset GPIO 6
echo 6 | sudo tee /sys/class/gpio/unexport
echo 6 | sudo tee /sys/class/gpio/export
echo out | sudo tee /sys/class/gpio/gpio6/direction
echo 1 | sudo tee /sys/class/gpio/gpio6/value
```

---

## 📸 Photos/Schémas

### Vue du dessus (conceptuel)

```
[LCD occupe pins 1-26]

              .─────.
Pin 27-28    │     │
             │     │
Pin 29 ─────▶│ 5   │──── DATA iButton
Pin 30 ─────▶│ GND │──── GND iButton
Pin 31 ─────▶│ 6   │──── [4.7kΩ] vers Pin 29
Pin 32-40    │     │
              '─────'
```

---

## 🧪 Commandes de test

### Configuration initiale (une seule fois)

```bash
ssh user@RASPBERRY_IP
cd /home/sam/ZeroRange
sudo python3 setup_gpio6_pullup.py
```

### Test complet

```bash
sudo python3 test_ibutton_gpio5.py
```

### Surveillance en continu

```bash
sudo python3 monitor_ibutton_gpio5.py
```

**Note**: `sudo` est nécessaire pour contrôler GPIO 6

---

## 📝 Notes importantes

1. ⚠️ **Toujours utiliser `sudo`** pour les scripts (GPIO 6 nécessite des privilèges)
2. ✅ **Résistance 4.7kΩ obligatoire** (ne pas omettre)
3. ✅ **GPIO 6 doit rester HIGH** pendant l'utilisation
4. ⚠️ **Ne pas dépasser 3.3V** sur les pins GPIO
5. ✅ **Scripts configurent automatiquement** GPIO 6

---

## 🎯 Résumé - Checklist

- [ ] Résistance 4.7kΩ connectée entre Pin 31 et Pin 29
- [ ] Pin 29 (GPIO 5) connecté au DATA du probe
- [ ] Pin 30 (GND) connecté au GND du probe
- [ ] Script `setup_gpio6_pullup.py` exécuté avec sudo
- [ ] Interface 1-Wire activée (dtoverlay=w1-gpio,gpiopin=5)
- [ ] Tests lancés avec sudo

**Une fois tout coché → Prêt pour les tests! 🚀**
