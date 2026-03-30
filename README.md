# VortexDL 🎬🎵
Téléchargeur vidéo MP3 / MP4 HD — propulsé par yt-dlp & FFmpeg

## Déploiement gratuit sur Railway (recommandé)

### 1. Crée un compte Railway
→ https://railway.app (gratuit, pas de CB requise)

### 2. Déploie en 3 clics
1. Va sur https://railway.app/new
2. Clique **"Deploy from GitHub repo"**
3. Upload ce dossier ou connecte ton GitHub

### Ou depuis GitHub :
```bash
# 1. Crée un repo GitHub et upload tous ces fichiers
# 2. Sur Railway → New Project → Deploy from GitHub → sélectionne ton repo
# 3. Railway détecte nixpacks.toml et installe Python + FFmpeg automatiquement
# 4. Ton site est live en ~2 minutes sur une URL https://xxx.railway.app
```

## Déploiement sur Render (alternative gratuite)
1. Va sur https://render.com
2. New → Web Service → connecte GitHub
3. Build Command : `pip install -r requirements.txt`
4. Start Command : `python app.py`
5. Add environment variable : `PYTHON_VERSION=3.11`
6. ⚠️ Sur Render, installe FFmpeg via : Shell → `apt-get install ffmpeg`
   Ou ajoute dans requirements.txt : `imageio[ffmpeg]`

## Test local
```bash
# Installe les dépendances
pip install -r requirements.txt

# Installe FFmpeg (macOS)
brew install ffmpeg

# Installe FFmpeg (Ubuntu/Debian)
sudo apt-get install ffmpeg

# Lance le serveur
python app.py
# → Ouvre http://localhost:5000
```

## Structure des fichiers
```
vortexdl/
├── app.py              ← Backend Flask + yt-dlp
├── requirements.txt    ← Dépendances Python
├── Procfile            ← Pour Railway/Heroku
├── nixpacks.toml       ← Config Railway (Python + FFmpeg)
├── README.md           ← Ce fichier
└── templates/
    └── index.html      ← Frontend complet
```

## Plateformes supportées
YouTube, Instagram, TikTok, Twitter/X, Facebook, Twitch, Dailymotion, Vimeo, et +1000 autres via yt-dlp.

## Formats
- **MP3** : 128 / 192 / 320 kbps
- **MP4** : 480p / 720p / 1080p Full HD / 4K Ultra HD

⚖️ Usage légal uniquement. Respectez les droits d'auteur.
