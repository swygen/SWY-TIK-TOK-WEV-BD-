from flask import Flask, request, send_file, jsonify, render_template
import yt_dlp
import os
import time

# Vercel এ টেমপ্লেট ফোল্ডার সঠিকভাবে খুঁজে পাওয়ার জন্য এই লাইনগুলো খুব জরুরি
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../templates'))
app = Flask(__name__, template_folder=template_dir)

# Vercel Temporary Directory
DOWNLOAD_FOLDER = "/tmp"

@app.route('/')
def home():
    try:
        return render_template('index.html')
    except Exception as e:
        return f"Error loading template: {str(e)}", 500

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

@app.route('/api/download', methods=['GET'])
def download_video():
    url = request.args.get('url')
    quality = request.args.get('quality', 'normal')
    
    timestamp = int(time.time())
    filename = f"Swygen_{timestamp}"
    save_path = os.path.join(DOWNLOAD_FOLDER, filename)
    
    # Vercel এ FFmpeg নেই, তাই আমরা সরাসরি ফরম্যাট নামাবো মার্জিং ছাড়া
    ydl_opts = {
        'outtmpl': f"{save_path}.%(ext)s",
        'quiet': True,
        'no_warnings': True,
        'format': 'best', # সেইফ মোড
    }

    if quality == "audio":
        ydl_opts['format'] = 'bestaudio/best'
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        final_file = None
        for ext in ['.mp4', '.mkv', '.webm', '.mp3', '.m4a']:
            if os.path.exists(save_path + ext):
                final_file = save_path + ext
                break
        
        if final_file:
            return send_file(final_file, as_attachment=True, download_name=os.path.basename(final_file))
        else:
            return "File not found after download", 404

    except Exception as e:
        return f"Download Error: {str(e)}", 500

# Vercel এর জন্য এই লাইনটি খুব গুরুত্বপূর্ণ
if __name__ == '__main__':
    app.run()
