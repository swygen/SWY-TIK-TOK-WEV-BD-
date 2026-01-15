from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import os

# টেমপ্লেট পাথ সেটআপ
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../templates'))
app = Flask(__name__, template_folder=template_dir)
CORS(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/process', methods=['POST'])
def process_video():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({"status": "error", "message": "No URL provided"}), 400

    # আমরা Cobalt API ব্যবহার করব যা Vercel এর মতো ব্লকড না
    # এটি ফ্রি এবং শক্তিশালী ওপেন সোর্স API
    api_url = "https://api.cobalt.tools/api/json"
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    payload = {
        "url": url,
        "vCodec": "h264",
        "vQuality": "720",
        "aFormat": "mp3",
        "isAudioOnly": False
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=15)
        result = response.json()

        if response.status_code == 200 and 'url' in result:
            return jsonify({
                "status": "success",
                "download_url": result['url'],
                # Cobalt সরাসরি টাইটেল দেয় না অনেক সময়, তাই আমরা জেনেরিক টাইটেল দেব
                "title": "Swygen Download Ready", 
                "platform": "Social Media"
            })
        elif 'text' in result:
             return jsonify({"status": "error", "message": result['text']}), 400
        else:
            return jsonify({"status": "error", "message": "Video unavailable or private."}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# অডিও ডাউনলোড হ্যান্ডলার
@app.route('/api/process-audio', methods=['POST'])
def process_audio():
    data = request.json
    url = data.get('url')
    
    api_url = "https://api.cobalt.tools/api/json"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    
    payload = {
        "url": url,
        "isAudioOnly": True
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        result = response.json()
        
        if 'url' in result:
            return jsonify({"status": "success", "download_url": result['url']})
        else:
            return jsonify({"status": "error", "message": "Audio conversion failed."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run()
