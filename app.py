import os
import re
import uuid
import threading
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = "/tmp/vortexdl"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Track progress per job
progress_store = {}

def clean_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)[:80]

def make_progress_hook(job_id):
    def hook(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 1
            downloaded = d.get('downloaded_bytes', 0)
            speed = d.get('speed', 0) or 0
            pct = min(int(downloaded / total * 90), 90)
            progress_store[job_id] = {
                'status': 'downloading',
                'percent': pct,
                'speed': f"{speed/1024/1024:.1f} MB/s" if speed > 0 else "—",
                'eta': d.get('eta', 0),
            }
        elif d['status'] == 'finished':
            progress_store[job_id] = {
                'status': 'processing',
                'percent': 95,
                'speed': '—',
                'eta': 0,
            }
    return hook

def do_download(job_id, url, fmt, quality):
    try:
        out_template = os.path.join(DOWNLOAD_DIR, f"{job_id}_%(title)s.%(ext)s")

        if fmt == 'mp3':
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': out_template,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': quality,  # '128', '192', '320'
                }],
                'progress_hooks': [make_progress_hook(job_id)],
                'quiet': True,
                'no_warnings': True,
            }
        else:
            # MP4 quality map
            q_map = {
                '480p':  'bestvideo[height<=480]+bestaudio/best[height<=480]',
                '720p':  'bestvideo[height<=720]+bestaudio/best[height<=720]',
                '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
                '4k':    'bestvideo[height<=2160]+bestaudio/best[height<=2160]',
            }
            fmt_str = q_map.get(quality.lower(), q_map['1080p'])
            ydl_opts = {
                'format': fmt_str,
                'outtmpl': out_template,
                'merge_output_format': 'mp4',
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
                'progress_hooks': [make_progress_hook(job_id)],
                'quiet': True,
                'no_warnings': True,
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = clean_filename(info.get('title', 'video'))
            ext = 'mp3' if fmt == 'mp3' else 'mp4'
            duration = info.get('duration', 0)
            mins = duration // 60
            secs = duration % 60

            # Find the output file
            found = None
            for f in os.listdir(DOWNLOAD_DIR):
                if f.startswith(job_id):
                    found = f
                    break

            if found:
                size = os.path.getsize(os.path.join(DOWNLOAD_DIR, found))
                size_str = f"{size/1024/1024:.1f} MB"
                progress_store[job_id] = {
                    'status': 'done',
                    'percent': 100,
                    'speed': '—',
                    'eta': 0,
                    'title': info.get('title', 'Vidéo'),
                    'thumbnail': info.get('thumbnail', ''),
                    'duration': f"{mins}:{secs:02d}",
                    'size': size_str,
                    'filename': found,
                    'ext': ext,
                }
            else:
                raise Exception("Fichier introuvable après téléchargement")

    except Exception as e:
        progress_store[job_id] = {
            'status': 'error',
            'percent': 0,
            'message': str(e),
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/info', methods=['POST'])
def get_info():
    data = request.json
    url = data.get('url', '').strip()
    if not url:
        return jsonify({'error': 'URL manquante'}), 400
    try:
        ydl_opts = {'quiet': True, 'no_warnings': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                'title': info.get('title', ''),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', ''),
                'view_count': info.get('view_count', 0),
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/download', methods=['POST'])
def start_download():
    data = request.json
    url = data.get('url', '').strip()
    fmt = data.get('format', 'mp3')       # 'mp3' or 'mp4'
    quality = data.get('quality', '320' if fmt == 'mp3' else '1080p')

    if not url:
        return jsonify({'error': 'URL manquante'}), 400

    job_id = str(uuid.uuid4())[:8]
    progress_store[job_id] = {'status': 'starting', 'percent': 0}

    thread = threading.Thread(target=do_download, args=(job_id, url, fmt, quality))
    thread.daemon = True
    thread.start()

    return jsonify({'job_id': job_id})

@app.route('/api/progress/<job_id>')
def get_progress(job_id):
    data = progress_store.get(job_id, {'status': 'unknown', 'percent': 0})
    return jsonify(data)

@app.route('/api/file/<job_id>')
def get_file(job_id):
    info = progress_store.get(job_id, {})
    filename = info.get('filename')
    if not filename:
        return jsonify({'error': 'Fichier non trouvé'}), 404
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'Fichier expiré'}), 404

    ext = info.get('ext', 'mp4')
    mime = 'audio/mpeg' if ext == 'mp3' else 'video/mp4'
    download_name = info.get('title', 'video') + '.' + ext
    return send_file(filepath, mimetype=mime, as_attachment=True, download_name=download_name)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
