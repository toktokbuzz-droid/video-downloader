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
            'no_warnings': True,  # Yeh warning suppress karega
            'extractor_args': {
                'youtube': {'player_client': ['android', 'web']},
                'tiktok': {  # TikTok specific
                    'skip': ['hls', 'dash'],  # Fast karega
                    'player_client': ['web'],
                }
            },
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                'title': info.get('title', 'Video'),
                'thumbnail': info.get('thumbnail', '')
            })
    except:
        return jsonify({'error': 'Invalid link or private video'}), 400

@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    url = data.get('url')
    quality = data.get('quality', '1080')

    temp_dir = tempfile.mkdtemp()

    try:
        ydl_opts = {
            'format': 'best[height<=1080]',
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,  # Impersonation warning hide
            'extractor_args': {
                'youtube': {'player_client': ['android', 'web']},
                'tiktok': {  # TikTok fix
                    'player_client': ['web'],
                    'skip': ['hls', 'dash'],
                }
            },
        }

        if quality == 'audio':
            ydl_opts['format'] = 'bestaudio'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        elif quality == '360':
            ydl_opts['format'] = 'best[height<=360]'
        elif quality == '720':
            ydl_opts['format'] = 'best[height<=720]'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        for file in os.listdir(temp_dir):
            if file.endswith(('.mp4', '.mkv', '.webm', '.mp3')):
                filepath = os.path.join(temp_dir, file)
                return send_file(
                    filepath,
                    as_attachment=True,
                    download_name=f"{info.get('title', 'video')}.{ 'mp3' if quality == 'audio' else 'mp4'}"
                )

        return jsonify({'error': 'File not found after download'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

if __name__ == '__main__':
    app.run(debug=True)
