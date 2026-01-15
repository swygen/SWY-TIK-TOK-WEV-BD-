from flask import Flask, request, send_file, jsonify, render_template
import yt_dlp
import os
import time
import random

# Vercel Path Fix (খুবই গুরুত্বপূর্ণ)
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../templates'))
app = Flask(__name__, template_folder=template_dir)

# Vercel এ একমাত্র লেখার অনুমতি আছে /tmp ফোল্ডারে
DOWNLOAD_FOLDER = "/tmp"

@app.route('/')
def home():
    try:
        return render_template('index.html')
    except Exception as e:
        return f"<h1>System Error</h1><p>Template path not found. Error: {str(e)}</p>", 500

# শক্তিশালী হেডার যাতে সার্ভার ব্লক না করে
def get_downloader_options():
    return {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'logtostderr': False,
        'cache_dir': '/tmp/yt_cache', # Vercel Cache Fix
        'socket_timeout': 30,
        'source_address': '0.0.0.0',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        }
    }

@app.route('/api/info', methods=['POST'])
def get_info():
    url = request.json.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        opts = get_downloader_options()
        with yt_dlp.YoutubeDL(opts) as ydl:
            # fast extract
            info = ydl.extract_info(url, download=False)
            
            # টাইটেল ক্লিন করা
            title = info.get('title', 'Swygen Video')
            if len(title) > 50: title = title[:50] + "..."

            return jsonify({
                "status": "success",
                "title": title,
                "thumbnail": info.get('thumbnail', ''),
                "duration": info.get('duration_string', '00:00'),
                "platform": info.get('extractor_key', 'Social Media')
            })
            
    except Exception as e:
        print(f"Info Error: {e}")
        return jsonify({"status": "error", "message": "Link not supported or Private video."}), 400

@app.route('/api/download', methods=['GET'])
def download_video():
    url = request.args.get('url')
    quality = request.args.get('quality', 'normal')
    
    timestamp = int(time.time())
    rand_id = random.randint(1000, 9999)
    filename = f"Swygen_{timestamp}_{rand_id}"
    save_path = os.path.join(DOWNLOAD_FOLDER, filename)
    
    opts = get_downloader_options()
    
    # Vercel এ FFmpeg নেই, তাই মার্জিং বন্ধ রাখতে হবে
    opts.update({
        'outtmpl': f"{save_path}.%(ext)s",
        'format': 'best', # Best single file logic
    })

    if quality == "audio":
        # অডিওর জন্য বেস্ট অডিও ফরম্যাট (কনভার্ট ছাড়া)
        opts['format'] = 'bestaudio/best'

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
            
        # ফাইল খুঁজে বের করা
        final_file = None
        for ext in ['.mp4', '.mkv', '.webm', '.m4a', '.mp3']:
            if os.path.exists(f"{save_path}{ext}"):
                final_file = f"{save_path}{ext}"
                break
        
        if final_file:
            return send_file(final_file, as_attachment=True, download_name=os.path.basename(final_file))
        else:
            return "Error: File download failed on server.", 404

    except Exception as e:
        return f"Server Error: {str(e)}", 500

# Vercel Entry
if __name__ == '__main__':
    app.run()
