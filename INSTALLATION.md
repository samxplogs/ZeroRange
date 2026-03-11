# Installation du service ZeroRange

Ce guide explique comment installer ZeroRange en tant que service systemd qui démarre automatiquement au boot du Raspberry Pi.

## 📦 Ce qui sera installé

Le service systemd lance automatiquement **3 services** au démarrage:

1. **Application principale ZeroRange** - LCD + Boutons + Challenges
2. **Serveur HTTP** (port 8000) - Documentation et interface web
3. **API LCD** (port 5000) - Contrôle du LCD depuis le web

## 🚀 Installation rapide

### Depuis le réseau (si connecté au Raspberry Pi)

```bash
# Depuis ton Mac
scp -r /path/to/ZeroRange/* user@RASPBERRY_IP:/home/sam/ZeroRange/

# Puis sur le Raspberry Pi
ssh user@RASPBERRY_IP
cd /home/sam/ZeroRange
sudo bash install_service.sh
```

### Depuis le Raspberry Pi directement

```bash
cd /home/sam/ZeroRange
sudo bash install_service.sh
```

## 📋 Détails de l'installation

Le script `install_service.sh` effectue les actions suivantes:

1. Rend les scripts exécutables (`start_all.sh`, `stop_all.sh`)
2. Copie le fichier de service dans `/etc/systemd/system/`
3. Crée les répertoires de logs dans `/var/log/zerorange/`
4. Active le service au démarrage
5. Démarre le service immédiatement

## 🎮 Gestion du service

### Commandes de base

```bash
# Voir le statut
sudo systemctl status zerorange

# Démarrer
sudo systemctl start zerorange

# Arrêter
sudo systemctl stop zerorange

# Redémarrer
sudo systemctl restart zerorange

# Désactiver le démarrage automatique
sudo systemctl disable zerorange

# Réactiver le démarrage automatique
sudo systemctl enable zerorange
```

### Logs

```bash
# Voir tous les logs
sudo journalctl -u zerorange

# Voir les logs en temps réel
sudo journalctl -u zerorange -f

# Voir les dernières lignes
sudo journalctl -u zerorange -n 50

# Logs des services individuels
tail -f /var/log/zerorange/zerorange.log   # Application principale
tail -f /var/log/zerorange/http.log        # Serveur HTTP
tail -f /var/log/zerorange/lcd_api.log     # API LCD
```

## 🌐 Accès aux services

Une fois le service démarré, les interfaces sont accessibles:

### Interface Web (Documentation)
```
http://[IP_DU_RASPBERRY_PI]:8000
http://<RASPBERRY_PI_IP>:8000  (IP assigned via DHCP — run `hostname -I` on the Pi)
```

Pages disponibles:
- `/home.html` - Simulateur LCD en temps réel
- `/documentation.html` - Documentation complète
- `/contact.html` - Informations de contact

### API LCD (Contrôle à distance)
```
http://[IP_DU_RASPBERRY_PI]:5000
```

Endpoints:
- `GET /lcd` - État actuel du LCD
- `POST /lcd/clear` - Effacer le LCD
- `POST /lcd/write` - Écrire du texte
- `POST /button/{button_num}` - Simuler un appui de bouton

### Application principale
Accessible directement sur le LCD physique du Raspberry Pi.

## 🔧 Personnalisation

### Modifier les ports

Édite le fichier `start_all.sh`:

```bash
nano /home/sam/ZeroRange/start_all.sh

# Ligne HTTP server
python3 -m http.server 8000  # Changer 8000 pour un autre port

# Ligne web_lcd_server.py
# Édite web_lcd_server.py pour changer le port 5000
```

### Ajouter d'autres services

Ajoute des commandes dans `start_all.sh` avant le lancement de `zerorange.py`.

## 🐛 Dépannage

### Le service ne démarre pas

```bash
# Vérifier les erreurs
sudo journalctl -u zerorange -xe

# Tester manuellement
cd /home/sam/ZeroRange
sudo bash start_all.sh
```

### Ports déjà utilisés

```bash
# Vérifier quels processus utilisent les ports
sudo netstat -tlnp | grep -E '(8000|5000)'

# Tuer les processus
sudo pkill -f "http.server 8000"
sudo pkill -f "web_lcd_server"
```

### Plusieurs instances qui tournent

```bash
# Tout arrêter
sudo systemctl stop zerorange
sudo bash /home/sam/ZeroRange/stop_all.sh
sudo pkill -9 -f "python3.*zerorange"

# Redémarrer
sudo systemctl start zerorange
```

## 📝 Structure des fichiers

```
/home/sam/ZeroRange/
├── start_all.sh          # Script de démarrage complet
├── stop_all.sh           # Script d'arrêt complet
├── install_service.sh    # Script d'installation
├── zerorange.service     # Fichier de service systemd
├── zerorange.py          # Application principale
├── web_lcd_server.py     # API Flask pour LCD
└── web/                  # Fichiers web statiques
    ├── home.html
    ├── documentation.html
    └── contact.html

/etc/systemd/system/
└── zerorange.service     # Service installé

/var/log/zerorange/
├── zerorange.log         # Logs application principale
├── http.log              # Logs serveur HTTP
└── lcd_api.log           # Logs API LCD

/var/run/zerorange/
├── http.pid              # PID serveur HTTP
└── lcd_api.pid           # PID API LCD
```

## ✅ Vérification post-installation

```bash
# 1. Vérifier que le service tourne
sudo systemctl status zerorange

# 2. Vérifier les processus
ps aux | grep -E '(zerorange|http.server|web_lcd)'

# 3. Vérifier les ports
sudo netstat -tlnp | grep -E '(8000|5000)'

# 4. Tester l'interface web
curl http://localhost:8000/home.html

# 5. Tester l'API LCD
curl http://localhost:5000/lcd
```

## 🎯 Désinstallation

```bash
# Arrêter et désactiver le service
sudo systemctl stop zerorange
sudo systemctl disable zerorange

# Supprimer le fichier de service
sudo rm /etc/systemd/system/zerorange.service

# Recharger systemd
sudo systemctl daemon-reload

# Supprimer les logs (optionnel)
sudo rm -rf /var/log/zerorange
sudo rm -rf /var/run/zerorange
```

## 📚 Ressources

- [Documentation systemd](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [Guide Flask](https://flask.palletsprojects.com/)
- [Python HTTP Server](https://docs.python.org/3/library/http.server.html)
