# iButton IDs - ZeroRange

## 📋 IDs officiels pour les challenges

### Challenge 1: Touch & Read
**ID attendu**: `01-62397A010000FF`

**Format Flipper Zero**: `01 62 39 7A 01 00 00 FF`

**Instructions**:
- Place l'iButton physique sur le lecteur USB
- OU émule cet ID avec ton Flipper Zero
- Le système détecte automatiquement l'ID

---

### Challenge 2: Clone iButton
**ID attendu**: `01-62397A010000FF`

**Format Flipper Zero**: `01 62 39 7A 01 00 00 FF`

**Instructions**:
- **Étape 1**: Place l'iButton physique pour lecture
- **Étape 2**: Émule le même ID avec ton Flipper Zero ou un T5577 cloné

---

### Challenge 3: Emulate Specific
**ID à programmer sur l'iButton**: `01 CA FE 11 11 11 11 D4`

**ID détecté par le lecteur USB**: `01-11111111FECAD4`

**Note**: Le lecteur USB lit les bytes à l'envers (little-endian). Programme ton iButton avec `01 CA FE 11 11 11 11 D4`, le système détectera automatiquement `01-11111111FECAD4`.

**Instructions**:
- Programme ton Flipper Zero avec cet ID exact
- OU programme un T5577 avec cet ID
- Place l'iButton/émulateur sur le lecteur pour validation

---

## 🔧 Programmation Flipper Zero

### Pour Challenge 1 & 2
```
iButton → Saved
→ Add Manually
→ Dallas
Type: 01 62 39 7A 01 00 00 FF
Name: ZeroRange_Ch1-2
```

### Pour Challenge 3
```
iButton → Saved
→ Add Manually
→ Dallas
Type: 01 CA FE 11 11 11 11 D4
Name: ZeroRange_Ch3
```

---

## 📝 Format des IDs

### Format ZeroRange (avec tiret)
- `01-XXXXXXXXXXXX`
- Le premier octet (01) = Family Code (Dallas DS1990A)
- Les 12 caractères hex suivants = 6 bytes de données

### Format Flipper Zero (avec espaces)
- `01 XX XX XX XX XX XX XX`
- Chaque paire = 1 byte
- Total: 8 bytes

### Conversion
| ZeroRange | Flipper Zero |
|-----------|--------------|
| `01-62397A010000FF` | `01 62 39 7A 01 00 00 FF` |
| `01-CAFE11111111D4` | `01 CA FE 11 11 11 11 D4` |

---

## ⚠️ Important

Le **lecteur USB iButton** (c216:0101) ne fonctionne qu'avec:
- ✅ iButtons physiques dans le socket
- ❌ Flipper Zero en émulation (pas compatible avec ce lecteur USB)

**Pour utiliser le Flipper Zero**, tu dois:
1. Avoir un iButton physique pour le Challenge 1
2. Connecter le Flipper Zero en GPIO 1-Wire au Raspberry Pi
3. Utiliser un mode hybride USB + GPIO

---

## 🎯 Récapitulatif rapide

| Challenge | ID à programmer | ID détecté par USB |
|-----------|----------------|-------------------|
| 1 & 2 | `01 62 39 7A 01 00 00 FF` | `01-0000017A3962FF` |
| 3 | `01 CA FE 11 11 11 11 D4` | `01-11111111FECAD4` |

**Note importante**: Le lecteur USB inverse l'ordre des bytes (little-endian).

**Total**: 3 challenges iButton = 30 points
