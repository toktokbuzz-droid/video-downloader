from flask import Flask, request, send_file, render_template, jsonify, Response
from flask_cors import CORS
import yt_dlp
import os
import tempfile
import shutil

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/privacy.html')
def privacy():
    return render_template('privacy.html')

@app.route('/dmca.html')
def dmca():
    return render_template('dmca.html')

@app.route('/disclaimer.html')
def disclaimer():
    return render_template('disclaimer.html')

@app.route('/info', methods=['POST'])
def get_info():
    url = request.json.get('url')
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                'title': info.get('title', 'Video'),
                'thumbnail': info.get('thumbnail', '')
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    url = data.get('url')
    quality = data.get('quality', '1080')

    temp_dir = tempfile.mkdtemp()
    def generate():
        try:
            ydl_opts = {
                'outtmpl': os.path.join(temp_dir, 'video.%(ext)s'),
                'noplaylist': True,
                'format': 'best[height<=1080]',
            }
            if quality == 'audio':
                ydl_opts['format'] = 'bestaudio'
                ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]
            elif quality == '360':
                ydl_opts['format'] = 'best[height<=360]'
            elif quality == '720':
                ydl_opts['format'] = 'best[height<=720]'

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filepath = ydl.prepare_filename(info)
                if quality == 'audio':
                    filepath = filepath.rsplit('.', 1)[0] + '.mp3'

            with open(filepath, 'rb') as f:
                while chunk := f.read(1024*1024):  # 1MB chunks
                    yield chunk
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    return Response(generate(), mimetype='application/octet-stream',
                    headers={"Content-Disposition": "attachment; filename=video.mp4"})

if __name__ == '__main__':
    app.run(debug=True)