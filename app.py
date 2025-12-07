from flask import Flask, request, render_template, jsonify, Response
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

# Info lene ke liye (thumbnail + title)
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
    except Exception as e:
        return jsonify({'error': 'Invalid or private video'}), 400

# Download ke liye
@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    url = data.get('url')
    quality = data.get('quality', '1080')

    temp_dir = tempfile.mkdtemp()

    def generate():
        try:
            ydl_opts = {
                'format': 'best[height<=1080]',
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web'],   # Yeh line magic hai 2025 mein
                        'skip': ['dash', 'hls']
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
                filename = ydl.prepare_filename(info)
                if quality == 'audio':
                    filename = filename.rsplit('.', 1)[0] + '.mp3'

            # File bhejna streaming mein
            with open(filename, 'rb') as f:
                while chunk := f.read(1024 * 1024):  # 1MB chunks
                    yield chunk
        except Exception as e:
            yield f"Error: {str(e)}".encode()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    return Response(
        generate(),
        mimetype='application/octet-stream',
        headers={"Content-Disposition": f"attachment; filename=video.mp4"}
    )

if __name__ == '__main__':
    app.run(debug=True)
