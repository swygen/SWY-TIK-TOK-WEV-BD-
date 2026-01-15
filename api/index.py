from flask import Flask, request, send_file, jsonify, render_template
import yt_dlp
import os
import time
import shutil

app = Flask(__name__, template_folder='../')

# Vercel Temporary Directory
DOWNLOAD_FOLDER = "/tmp"

@app.route('/')
def home():
    return render_template('index.html')

# 1. Video Info Checker API
@app.route('/api/info', methods=['POST'])
def get_info():
    url = request.json.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                "status": "success",
                "title": info.get('title', 'Unknown Video'),
                "thumbnail": info.get('thumbnail', ''),
                "duration": info.get('duration_string', 'N/A'),
                "platform": info.get('extractor_key', 'Unknown')
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# 2. Real Download API (4K & No Watermark)
@app.route('/api/download', methods=['GET'])
def download_video():
    url = request.args.get('url')
    quality = request.args.get('quality', 'normal') # hd, normal, audio
    
    timestamp = int(time.time())
    filename = f"Swygen_{timestamp}"
    save_path = os.path.join(DOWNLOAD_FOLDER, filename)
    
    ydl_opts = {
        'outtmpl': f"{save_path}.%(ext)s",
        'quiet': True,
        'no_warnings': True,
        # TikTok No Watermark Logic
        'format_sort': ['res:1080', 'ext:mp4:m4a'], 
    }

    # Quality Logic
    if quality == "audio":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3',}],
        })
        final_file = f"{save_path}.mp3"
        
    elif quality == "hd":
        # Best Video + Best Audio (Might require FFmpeg on server)
        ydl_opts.update({'format': 'bestvideo+bestaudio/best'})
        final_file = f"{save_path}.mp4"
        
    else: # Normal Quality (Faster, safest for Vercel)
        ydl_opts.update({'format': 'best'}) # TikTok usually gives No WM by default on 'best'
        final_file = f"{save_path}.mp4"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        # Find the actual file (since extension might vary)
        if not os.path.exists(final_file):
            # Fallback check
            for ext in ['.mp4', '.mkv', '.webm', '.mp3']:
                if os.path.exists(save_path + ext):
                    final_file = save_path + ext
                    break

        return send_file(final_file, as_attachment=True, download_name=os.path.basename(final_file))

    except Exception as e:
        return f"Download Error: {str(e)}", 500

# Vercel entry point
app = app
