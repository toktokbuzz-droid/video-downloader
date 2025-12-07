from flask import Flask, request, render_template, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import tempfile
import shutil
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/privacy.html')
def privacy(): return render_template('privacy.html')
@app.route('/dmca.html')
def dmca(): return render_template('dmca.html')
@app.route('/disclaimer.html')
def disclaimer(): return render_template('disclaimer.html')

@app.route('/info', methods=['POST'])
def get_info():
    url = request.json.get('url')
    try:
        ydl_opts = {
            'quiet': True,
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                'title': info.get('title', 'Video'),
                'thumbnail': info.get('thumbnail', '')
            })
    except:
        return jsonify({'error': 'Invalid or private video'}), 400

@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    url = data.get('url')
    quality = data.get('quality', 'best')  # 1080, 720, 360, audio

    temp_dir = tempfile.mkdtemp()

    try:
        # Yeh wahi magic format string jo tu diya tha — 100% single .mp4
        format_selector = (
            'bestvideo[ext=mp4]+bestaudio[ext=m4a]/'
            'bestvideo+bestaudio/'
            'best[ext=mp4]/best'
        )

        ydl_opts = {
            'format': format_selector,
            'merge_output_format': 'mp4',           # ← Force single mp4
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'concurrent_fragment_downloads': 5,
            'retries': 10,
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {
                'youtube': {'player_client': ['android', 'web']},
                'tiktok': {'player_client': ['web']},
            },
        }

        # Quality override
        if quality == 'audio' in quality.lower():
            ydl_opts['format'] = 'bestaudio'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        elif quality == '360':
            ydl_opts['format'] = f"best[height<=360][ext=mp4]+bestaudio/best[height<=360]"
        elif quality == '720':
            ydl_opts['format'] = f"best[height<=720][ext=mp4]+bestaudio/best[height<=720]"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        # Find the actual downloaded file
        downloaded_file = None
        for file in os.listdir(temp_dir):
            if file.endswith(('.mp4', '.mkv', '.webm', '.mp3')):
                downloaded_file = os.path.join(temp_dir, file)
                break

        if not downloaded_file or not os.path.exists(downloaded_file):
            return jsonify({'error': 'Download failed or file not found'}), 500

        # 500

        # Send file
        return send_file(
            downloaded_file,
            as_attachment=True,
            download_name=f"{info.get('title', 'video').replace('/', '_')}.{'mp3' if 'audio' in quality.lower() else 'mp4'}"
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

if __name__ == '__main__':
    app.run(debug=True)
