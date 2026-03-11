# 📡 ZeroRange - Mode Hotspot WiFi

## 🚀 Nouvelle fonctionnalité: Portabilité totale!

ZeroRange peut maintenant **créer son propre réseau WiFi**, le rendant complètement **autonome et portable**!

## ✨ Pourquoi c'est génial?

### Avant (mode réseau classique)
❌ Besoin d'un réseau WiFi existant
❌ Configuration IP complexe
❌ Dépendance à l'infrastructure
❌ Impossible à utiliser en déplacement

### Maintenant (mode hotspot)
✅ **Créez votre propre réseau WiFi**
✅ **Portail captif automatique**
✅ **Aucune configuration réseau**
✅ **Utilisable partout!**

## 🎯 Configuration ultra-simple

### 1️⃣ Installation (une seule fois)

```bash
cd /home/sam/ZeroRange
sudo bash setup_hotspot.sh
sudo reboot
```

**C'est tout!** 🎉

### 2️⃣ Utilisation quotidienne

1. **Allumez le Raspberry Pi**
2. **Cherchez le WiFi "ZeroRange"** sur votre smartphone/laptop
3. **Connectez-vous** avec le mot de passe configuré dans `setup_hotspot.sh`
4. **Le portail s'ouvre automatiquement!** ✨

## 📱 Accès depuis n'importe quel appareil

### Sur smartphone (iOS/Android)

1. Connectez-vous au WiFi **"ZeroRange"**
2. Le portail captif s'ouvre **automatiquement**
3. Vous êtes sur l'interface web de ZeroRange!

### Sur laptop/tablette

1. Connectez-vous au WiFi **"ZeroRange"**
2. Si le portail ne s'ouvre pas, allez sur: **http://10.0.0.1:8000**

### Accès SSH (pour les power users)

```bash
ssh user@10.0.0.1
# Use your configured password
```

## 🌐 Tous les services disponibles

| Service | URL | Description |
|---------|-----|-------------|
| 🎮 Interface web | http://10.0.0.1:8000 | Contrôle complet + Docs |
| 📺 Simulateur LCD | http://10.0.0.1:8000/home.html | LCD en temps réel |
| 📚 Documentation | http://10.0.0.1:8000/documentation.html | Guides complets |
| 🔌 API REST | http://10.0.0.1:5000 | Contrôle programmatique |
| 💻 SSH | ssh user@10.0.0.1 | Accès terminal |

## 🎪 Cas d'usage parfaits

### 🎓 Workshops & Formations
- **Pas besoin de WiFi de la salle** (souvent instable)
- Chaque participant se connecte à ZeroRange
- Démos en direct sur smartphone

### 🏆 Événements CTF
- Réseau dédié pour le challenge
- Pas de conflits avec le WiFi de l'événement
- Infrastructure contrôlée

### 🌳 Utilisation en extérieur
- Entraînement dans le jardin
- Pas besoin de rallonge Ethernet
- Complètement portable

### 🚗 Démonstrations mobiles
- Conférences de sécurité
- Présentations clients
- Meetups et hackerspaces

## 🔧 Configuration personnalisée

### Changer le nom du WiFi

```bash
sudo nano /etc/hostapd/hostapd.conf
# Modifiez: ssid=VotreNomIci
sudo systemctl restart hostapd
```

### Changer le mot de passe WiFi

```bash
sudo nano /etc/hostapd/hostapd.conf
# Modifiez: wpa_passphrase=VotreMotDePasse
sudo systemctl restart hostapd
```

### Désactiver le hotspot (retour en mode client)

```bash
sudo bash disable_hotspot.sh
sudo reboot
```

## 📊 Monitoring en temps réel

### Voir les appareils connectés

```bash
cat /var/lib/misc/dnsmasq.leases
```

### Logs du hotspot

```bash
sudo journalctl -u hostapd -f
```

## 🔒 Sécurité

### En atelier/chez vous
✅ Configuration par défaut OK

### En public
⚠️ Recommandations:

1. **Changez le mot de passe WiFi** (voir ci-dessus)
2. **Changez le mot de passe SSH:**
   ```bash
   passwd
   ```
3. **Activez le filtrage MAC** (liste blanche)

Voir `WIFI_HOTSPOT.md` pour les détails.

## 📖 Documentation complète

- **Installation détaillée:** `WIFI_HOTSPOT.md`
- **Dépannage:** `WIFI_HOTSPOT.md` section Troubleshooting
- **Configuration avancée:** `WIFI_HOTSPOT.md` section Advanced

## 🎯 Quick Start Complet

```bash
# 1. Installation du hotspot
cd /home/sam/ZeroRange
sudo bash setup_hotspot.sh
sudo reboot

# 2. Attendre le démarrage (~30 secondes)

# 3. Sur votre smartphone:
#    - Cherchez WiFi "ZeroRange"
#    - Mot de passe: "zero"
#    - Portail captif s'ouvre automatiquement

# 4. Profitez de ZeroRange partout! 🚀
```

## 💡 Astuces

### Combiner hotspot et internet

Si votre Raspberry Pi est aussi connecté en Ethernet:

```bash
# Activer le partage internet
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
sudo netfilter-persistent save
```

Les appareils connectés au hotspot auront internet! 🌐

### Portée du WiFi

- **Raspberry Pi 3/4:** ~10-20 mètres
- **Raspberry Pi 5:** ~15-30 mètres
- **Avec antenne externe:** Jusqu'à 50+ mètres

### Nombre d'appareils simultanés

- Recommandé: **5-10 appareils**
- Maximum testé: **20 appareils**
- Pour plus: Utilisez un switch WiFi

## 🆘 Problèmes courants

### Le WiFi n'apparaît pas

```bash
sudo systemctl restart hostapd
sudo rfkill unblock wifi
```

### Pas d'IP attribuée

```bash
sudo systemctl restart dnsmasq
```

### Portail captif ne s'ouvre pas

```bash
sudo systemctl restart lighttpd
# Puis ouvrez manuellement: http://10.0.0.1:8000
```

## 🎉 C'est tout!

ZeroRange est maintenant **100% portable et autonome**!

Emmenez-le partout, partagez avec vos amis, organisez des workshops sans stress réseau! 📡🚀

---

**Questions?** Consultez `WIFI_HOTSPOT.md` pour la doc complète!
