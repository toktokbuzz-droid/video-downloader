from flask import Flask, request, render_template, send_file, jsonify
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

@app.route('/download', methods=['POST'])
def download_video():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    temp_dir = tempfile.mkdtemp()

    try:
        # Best single .mp4 guaranteed (tu jo code diya tha wahi magic)
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {
                'youtube': {'player_client': ['android', 'web']},
            },
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        # Find the downloaded file
        for file in os.listdir(temp_dir):
            if file.endswith(('.mp4', '.mkv', '.webm')):
                filepath = os.path.join(temp_dir, file)
                return send_file(
                    filepath,
                    as_attachment=True,
                    download_name=f"{info.get('title', 'video')}.mp4"
                )

        return jsonify({'error': 'Download failed'}), 500

    except Exception as e:
        return jsonify({'error': 'Invalid or private video'}), 500
    finally:
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

if __name__ == '__main__':
    app.run(debug=True)
