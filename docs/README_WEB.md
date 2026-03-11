# 🌐 ZeroRange - Site Web

## 📁 Structure des fichiers

```
docs/
├── index.html          # Page de redirection vers home.html
├── home.html           # 🏠 Landing page (page d'accueil)
├── documentation.html  # 📖 Documentation complète
└── contact.html        # ✉️ Page de contact
```

## 🎯 Pages créées

### 1. Landing Page (home.html)

**Caractéristiques**:
- ✅ Court paragraphe d'introduction à ZeroRange
- ✅ Écran LCD simulé en temps réel (interactif)
- ✅ Grille de fonctionnalités (iButton, NFC, RFID, IR)
- ✅ Bouton CTA vers la documentation
- ✅ Menu de navigation horizontal

**Contenu**:
- Titre: "ZeroRange - Practice. Master. Repeat."
- Description: Système d'entraînement interactif pour Flipper Zero
- 4 cartes de fonctionnalités
- LCD en direct avec boutons interactifs
- Status "🟢 LIVE - Simulation en temps réel"

### 2. Documentation (documentation.html)

**Modifications**:
- ✅ Menu de navigation horizontal ajouté
- ✅ Conserve toute la documentation existante
- ✅ Système multilingue (FR/EN) conservé
- ✅ LCD simulé conservé

### 3. Contact (contact.html)

**Contenu**:
- ✅ Informations de contact (GitHub, Email, Discord, Issues)
- ✅ Section "Contribuer au projet"
- ✅ Liens sociaux
- ✅ Design cohérent avec le reste du site

### 4. Index (index.html)

**Fonction**:
- Redirection automatique vers home.html
- Fallback avec lien manuel si JS désactivé

## 🎨 Menu de navigation

Présent sur toutes les pages:

```
┌──────────────────────────────────────────┐
│  🏠 Home  │  📖 Documentation  │  ✉️ Contact  │
└──────────────────────────────────────────┘
```

**Fonctionnalités**:
- Position sticky (reste en haut lors du scroll)
- Indicateur visuel de la page active
- Effet hover
- Design semi-transparent avec backdrop-filter
- Responsive

## 💻 Écran LCD Live

**Fonctionnalités identiques sur Home et Documentation**:
- Simulation temps réel du menu ZeroRange
- 5 boutons interactifs (UP, DOWN, LEFT, RIGHT, SELECT)
- Navigation dans les menus (iButton, NFC, RFID, IR, Settings)
- Affichage 16x2 caractères
- Design réaliste avec effet LCD vert
- Score affiché (0/40)

**État**:
- Badge "🟢 LIVE - Simulation en temps réel" sur la landing page
- Fully interactive sur les deux pages

## 🎨 Design

**Couleurs principales**:
- Gradient: #667eea → #764ba2
- Fond LCD: #2d5016 (vert foncé)
- Texte LCD: #c5f776 (vert clair)
- Accents: #667eea (bleu-violet)

**Typographie**:
- Corps: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif
- LCD: 'Courier New', monospace

**Responsive**:
- Desktop: Grid 2 colonnes (contenu + LCD)
- Mobile: 1 colonne (LCD en haut)
- Breakpoint: 1024px

## 🚀 Accès

### Local
```
file:///path/to/ZeroRange/docs/index.html
```

### Sur Raspberry Pi
```
/home/sam/ZeroRange/docs/index.html
```

Si un serveur web est configuré:
```
http://<RASPBERRY_PI_IP>/docs/
```

## 🔧 Servir les pages

### Option 1: Python HTTP Server

```bash
cd /home/sam/ZeroRange/docs
python3 -m http.server 8000
```

Accès: `http://<RASPBERRY_PI_IP>:8000`

### Option 2: Nginx

```bash
# Installer nginx
sudo apt install nginx

# Copier les fichiers
sudo cp -r /home/sam/ZeroRange/docs/* /var/www/html/

# Démarrer nginx
sudo systemctl start nginx
```

Accès: `http://<RASPBERRY_PI_IP>`

## 📱 Pages détaillées

### Home (Landing Page)

**Sections**:
1. Hero
   - Titre + tagline
2. Main Content
   - Introduction (2 paragraphes)
   - Grille de fonctionnalités (4 cards)
   - LCD live interactif
3. CTA
   - Bouton vers documentation

**JavaScript**:
- Simulation du menu ZeroRange
- Navigation entre menus
- Mise à jour temps réel de l'écran

### Documentation

**Sections** (conservées):
- Introduction
- Navigation générale
- Menu principal
- Module iButton
- Module NFC (à venir)
- Module RFID (à venir)
- Module IR (à venir)
- Paramètres

**Ajout**:
- Menu de navigation en haut

### Contact

**Informations**:
- GitHub (code source + contributions)
- Email (support)
- Discord (communauté)
- Issues (bugs)

**Section contribution**:
- Liste des façons de contribuer
- Liens sociaux

## ✨ Prochaines étapes

### Améliorations possibles

1. **Backend**:
   - API pour afficher l'état réel du LCD du Raspberry Pi
   - WebSocket pour mise à jour temps réel
   - Connexion à la base de données pour afficher le vrai score

2. **Fonctionnalités**:
   - Dashboard avec statistiques
   - Leaderboard
   - Historique des challenges

3. **UX**:
   - Mode sombre
   - Animations supplémentaires
   - Progressive Web App (PWA)

4. **Contenu**:
   - Tutoriels vidéo
   - FAQ
   - Blog avec articles

## 📝 Notes

- Tous les liens sont relatifs (pas besoin de configuration)
- Compatible tous navigateurs modernes
- Pas de dépendances externes (CSS/JS inline)
- SEO-friendly
- Accessible

---

**Status**: ✅ Déployé sur le Raspberry Pi
**Version**: 1.0
**Date**: 13 janvier 2026
