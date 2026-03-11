# 📡 ZeroRange - Hotspot WiFi & Portail Captif

## 🎯 Vue d'ensemble

ZeroRange peut fonctionner en **mode hotspot WiFi** autonome, transformant le Raspberry Pi en point d'accès portable. Cette fonctionnalité permet d'utiliser ZeroRange **n'importe où** sans infrastructure réseau existante.

## ✨ Fonctionnalités

### Mode Hotspot activé

✅ **Point d'accès WiFi autonome**
- SSID: `ZeroRange`
- Mot de passe: `your_password_here`
- Portée: ~10-30 mètres (selon Raspberry Pi)

✅ **Portail captif automatique**
- Redirection automatique vers l'interface web
- Compatible iOS, Android, Windows, macOS
- Pas besoin de taper l'URL manuellement

✅ **Accès complet aux services**
- Interface web (http://10.0.0.1:8000)
- API LCD (http://10.0.0.1:5000)
- SSH (ssh sam@10.0.0.1)

✅ **Plug & Play**
- Allumez le Raspberry Pi
- Connectez-vous au WiFi "ZeroRange"
- Le portail s'ouvre automatiquement

## 📋 Prérequis

**Matériel:**
- Raspberry Pi avec WiFi intégré (Pi 3, 4, 5, Zero W)
- Carte SD avec Raspberry Pi OS

**Logiciels:**
- hostapd (point d'accès)
- dnsmasq (DHCP + DNS)
- lighttpd (serveur web pour portail captif)

## 🚀 Installation

### Méthode automatique (recommandée)

```bash
cd /home/sam/ZeroRange
sudo bash setup_hotspot.sh
```

Le script va:
1. ✅ Installer les paquets nécessaires
2. ✅ Configurer le point d'accès WiFi
3. ✅ Configurer le serveur DHCP
4. ✅ Mettre en place le portail captif
5. ✅ Activer les services au démarrage

**Redémarrez après l'installation:**
```bash
sudo reboot
```

### Configuration manuelle (avancée)

Si vous préférez configurer manuellement, consultez le contenu du script `setup_hotspot.sh` pour les détails.

## 🌐 Utilisation

### Connexion au hotspot

**Sur smartphone/tablette/ordinateur:**

1. **Recherchez le réseau WiFi "ZeroRange"**
2. **Entrez le mot de passe:** `zero`
3. **Le portail captif s'ouvre automatiquement**
   - iOS: Notification "Se connecter au réseau"
   - Android: "Se connecter" dans les notifications
   - Windows: "Ouvrir le navigateur"
   - macOS: Popup automatique

4. **Si le portail ne s'ouvre pas automatiquement:**
   - Ouvrez votre navigateur
   - Allez sur n'importe quel site (ex: http://example.com)
   - Vous serez redirigé vers http://10.0.0.1:8000/home.html

### Accès SSH via hotspot

```bash
# Depuis un terminal sur votre appareil connecté au hotspot
ssh user@10.0.0.1

# Use your configured password
```

**Depuis un smartphone:**
- iOS: Utilisez l'app "Termius" ou "Blink Shell"
- Android: Utilisez "JuiceSSH" ou "Termux"

### URLs disponibles

| Service | URL | Description |
|---------|-----|-------------|
| **Interface web** | http://10.0.0.1:8000 | Documentation + Simulateur LCD |
| **Portail captif** | http://10.0.0.1 | Redirection automatique |
| **API LCD** | http://10.0.0.1:5000 | API REST pour contrôle |
| **SSH** | ssh sam@10.0.0.1 | Accès terminal |

## 🔧 Configuration avancée

### Modifier le SSID et mot de passe

Éditez `/etc/hostapd/hostapd.conf`:

```bash
sudo nano /etc/hostapd/hostapd.conf
```

Modifiez:
```ini
ssid=ZeroRange           # Changez ici
wpa_passphrase=zero      # Changez ici
```

Redémarrez hostapd:
```bash
sudo systemctl restart hostapd
```

### Changer l'IP du hotspot

Éditez `/etc/dhcpcd.conf`:

```bash
sudo nano /etc/dhcpcd.conf
```

Modifiez:
```ini
interface wlan0
    static ip_address=10.0.0.1/24    # Changez ici
```

Éditez `/etc/dnsmasq.conf`:
```ini
dhcp-range=10.0.0.10,10.0.0.50,255.255.255.0,24h  # Changez ici
address=/#/10.0.0.1                                # Changez ici
```

Redémarrez:
```bash
sudo systemctl restart dhcpcd
sudo systemctl restart dnsmasq
```

### Activer le partage internet (optionnel)

Si votre Raspberry Pi a accès à internet via Ethernet (eth0):

```bash
# Activer le NAT
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
sudo iptables -A FORWARD -i eth0 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i wlan0 -o eth0 -j ACCEPT

# Sauvegarder les règles
sudo netfilter-persistent save

# Activer le forwarding IP (déjà fait par setup_hotspot.sh)
sudo sysctl -w net.ipv4.ip_forward=1
```

Les appareils connectés au hotspot auront alors accès à internet!

## 🔄 Basculer entre mode hotspot et mode client

### Désactiver le hotspot

Pour revenir en mode client WiFi normal:

```bash
cd /home/sam/ZeroRange
sudo bash disable_hotspot.sh
sudo reboot
```

### Réactiver le hotspot

```bash
sudo systemctl start hostapd
sudo systemctl start dnsmasq
sudo systemctl start lighttpd
```

Ou relancez:
```bash
sudo bash setup_hotspot.sh
```

## 📱 Applications mobiles recommandées

### Pour contrôler ZeroRange depuis smartphone

**iOS:**
- **Safari** - Interface web
- **Termius** - SSH client
- **Network Analyzer** - Diagnostics réseau

**Android:**
- **Chrome** - Interface web
- **JuiceSSH** - SSH client
- **Fing** - Scanner réseau

## 🐛 Dépannage

### Le hotspot n'apparaît pas

```bash
# Vérifier le statut de hostapd
sudo systemctl status hostapd

# Vérifier les logs
sudo journalctl -u hostapd -n 50

# Vérifier que wlan0 n'est pas bloqué
sudo rfkill list
sudo rfkill unblock wifi

# Redémarrer le service
sudo systemctl restart hostapd
```

### Pas d'IP attribuée aux clients

```bash
# Vérifier dnsmasq
sudo systemctl status dnsmasq

# Voir les logs DHCP
tail -f /var/log/dnsmasq.log

# Redémarrer
sudo systemctl restart dnsmasq
```

### Le portail captif ne s'ouvre pas

```bash
# Vérifier lighttpd
sudo systemctl status lighttpd

# Vérifier les logs
tail -f /var/log/lighttpd/error.log

# Tester manuellement
curl http://10.0.0.1

# Redémarrer
sudo systemctl restart lighttpd
```

### Connexion SSH impossible

```bash
# Vérifier que SSH est actif
sudo systemctl status ssh

# Vérifier le firewall
sudo iptables -L -n | grep 22

# Activer SSH si nécessaire
sudo systemctl enable ssh
sudo systemctl start ssh
```

### Conflits avec réseau existant

Si le réseau 10.0.0.0/24 entre en conflit:

```bash
# Changer pour 192.168.4.0/24 (exemple)
sudo nano /etc/dhcpcd.conf
# Changez: static ip_address=192.168.4.1/24

sudo nano /etc/dnsmasq.conf
# Changez: dhcp-range=192.168.4.10,192.168.4.50
# Changez: address=/#/192.168.4.1

sudo reboot
```

## 🔒 Sécurité

### Recommandations

✅ **En environnement contrôlé (chez vous, workshop):**
- Configuration par défaut OK
- Mot de passe "zero" suffisant

⚠️ **En environnement public (conférences, événements):**

1. **Changez le mot de passe WiFi:**
   ```bash
   sudo nano /etc/hostapd/hostapd.conf
   # wpa_passphrase=VotreMotDePasseFort123
   ```

2. **Changez le mot de passe SSH:**
   ```bash
   passwd  # Pour l'utilisateur sam
   ```

3. **Désactivez le portail captif public:**
   ```bash
   sudo systemctl stop lighttpd
   sudo systemctl disable lighttpd
   ```

4. **Filtrez par adresse MAC (liste blanche):**
   ```bash
   sudo nano /etc/hostapd/hostapd.conf
   # Ajoutez:
   # macaddr_acl=1
   # accept_mac_file=/etc/hostapd/accept_macs
   ```

### Isolation réseau

Par défaut, tous les clients connectés peuvent se voir. Pour isoler:

```bash
sudo nano /etc/hostapd/hostapd.conf
# Ajoutez:
# ap_isolate=1
```

## 📊 Monitoring

### Voir les clients connectés

```bash
# Liste des baux DHCP actifs
cat /var/lib/misc/dnsmasq.leases

# Avec détails
sudo arp -a

# Scan réseau complet
sudo nmap -sn 10.0.0.0/24
```

### Statistiques du hotspot

```bash
# Trafic WiFi
sudo iwconfig wlan0

# Clients actifs en temps réel
watch -n 2 'cat /var/lib/misc/dnsmasq.leases'

# Logs en direct
sudo journalctl -f -u hostapd -u dnsmasq
```

## 🎯 Cas d'usage

### 1. Démonstrations sur le terrain
- Workshops mobiles
- Présentations en conférence
- Formations en extérieur

### 2. Environnement isolé
- Tests sans accès internet
- Réseau dédié pour pentest
- Sandbox sécurisé

### 3. Événements CTF
- Plusieurs participants connectés
- Pas de dépendance au WiFi de la salle
- Contrôle total de l'infrastructure

### 4. Utilisation personnelle
- Entraînement dans le jardin
- Pas besoin de rallonge Ethernet
- Portable et autonome

## 🚀 Déploiement

Le hotspot est **automatiquement configuré** lors de l'installation du service ZeroRange si vous utilisez:

```bash
sudo bash install_service.sh --with-hotspot
```

Ou installez séparément:

```bash
sudo bash setup_hotspot.sh
```

## 📚 Ressources

- [Documentation hostapd](https://w1.fi/hostapd/)
- [Guide dnsmasq](https://thekelleys.org.uk/dnsmasq/doc.html)
- [Raspberry Pi Access Point](https://www.raspberrypi.com/documentation/computers/configuration.html#setting-up-a-routed-wireless-access-point)

## ✅ Checklist de vérification

Après installation, vérifiez:

- [ ] Le SSID "ZeroRange" est visible
- [ ] Connexion possible avec mot de passe "zero"
- [ ] IP attribuée automatiquement (10.0.0.x)
- [ ] Portail captif s'ouvre automatiquement
- [ ] Interface web accessible (http://10.0.0.1:8000)
- [ ] SSH fonctionnel (ssh sam@10.0.0.1)
- [ ] API LCD répond (curl http://10.0.0.1:5000/lcd)
- [ ] Services démarrent au boot

---

**Profitez de ZeroRange partout, sans réseau existant!** 📡🚀
