# 🚀 Déploiement automatique ZeroRange

## ✨ Nouveautés

Le système ZeroRange lance maintenant **automatiquement au démarrage**:

1. ✅ **Application principale** (LCD + Boutons + Challenges)
2. ✅ **Serveur web** (Documentation) - Port 8000
3. ✅ **API LCD** (Contrôle à distance) - Port 5000

## 📦 Fichiers créés

- `start_all.sh` - Lance tous les services
- `stop_all.sh` - Arrête tous les services
- `install_service.sh` - Installe le service systemd
- `zerorange.service` - Configuration systemd
- `deploy_to_pi.sh` - Déploie depuis ton Mac (quand tu es sur le réseau)
- `INSTALLATION.md` - Documentation complète d'installation

## 🎯 Déploiement rapide

### Option 1: Depuis ton Mac (quand connecté au réseau)

```bash
cd /path/to/ZeroRange
./deploy_to_pi.sh
```

Le script va:
- ✅ Vérifier la connexion au Raspberry Pi
- ✅ Copier tous les fichiers nécessaires
- ✅ Configurer les permissions
- ✅ Proposer d'installer le service automatiquement

### Option 2: Manuellement depuis le Raspberry Pi

```bash
# 1. Copier les fichiers (par clé USB, scp, etc.)
# 2. Sur le Raspberry Pi:
cd /home/sam/ZeroRange
sudo bash install_service.sh
```

## 🌐 Accès après installation

### Interface Web
```
http://<RASPBERRY_PI_IP>:8000/home.html
http://<RASPBERRY_PI_IP>:8000/documentation.html
```

> The Raspberry Pi gets its IP via DHCP. Run `hostname -I` on the Pi to find it.

### API LCD
```
http://<RASPBERRY_PI_IP>:5000/lcd
```

### Application physique
Directement sur l'écran LCD du Raspberry Pi!

## 🎮 Gestion du service

```bash
# Voir le statut
sudo systemctl status zerorange

# Redémarrer
sudo systemctl restart zerorange

# Arrêter
sudo systemctl stop zerorange

# Voir les logs en direct
sudo journalctl -u zerorange -f
```

## 📋 Logs des services

```bash
# Application principale
tail -f /var/log/zerorange/zerorange.log

# Serveur web
tail -f /var/log/zerorange/http.log

# API LCD
tail -f /var/log/zerorange/lcd_api.log
```

## 🔧 Ce qui se passe au démarrage

1. **Raspberry Pi démarre**
2. **Systemd lance zerorange.service**
3. **start_all.sh s'exécute**:
   - Démarre le serveur HTTP (port 8000)
   - Démarre l'API LCD Flask (port 5000)
   - Lance l'application principale ZeroRange
4. **Tous les services sont opérationnels!**

## ✅ Avantages

- ✅ **Automatique** - Tout démarre au boot
- ✅ **Fiable** - Systemd relance automatiquement en cas de crash
- ✅ **Complet** - LCD + Web + API en un seul service
- ✅ **Logs centralisés** - Tout dans /var/log/zerorange/
- ✅ **Facile à gérer** - Commandes systemctl standard

## 📚 Documentation complète

Consulte `INSTALLATION.md` pour:
- Guide d'installation détaillé
- Toutes les commandes de gestion
- Dépannage
- Personnalisation
- Désinstallation

## 🎉 C'est tout!

Quand tu seras de retour sur le réseau du Raspberry Pi, lance simplement:

```bash
cd /path/to/ZeroRange
./deploy_to_pi.sh
```

Et tout sera configuré automatiquement! 🚀
