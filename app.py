import os
import sys


os.system(f"pip install flask requests bs4")

from flask import Flask, request, render_template_string, redirect, send_file, after_this_request
import requests, re, os, uuid
from bs4 import BeautifulSoup
from urllib.parse import unquote
import tempfile

app = Flask(__name__)


TEMP_DIR = tempfile.mkdtemp()

HTML = '''
<!DOCTYPE html>
<html lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مشغل و تحميل فيديو Kwai</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        body {
            direction: rtl;
            text-align: center;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        .container {
            max-width: 800px;
            margin: 20px auto;
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }
        .logo {
            margin-bottom: 20px;
            color: #3498db;
            font-size: 2.5rem;
        }
        h1, h2, h3 {
            color: #2c3e50;
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 25px;
        }
        input[type="text"] {
            width: 100%;
            padding: 15px;
            margin: 10px 0;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            transition: border 0.3s;
        }
        input[type="text"]:focus {
            border-color: #3498db;
            outline: none;
        }
        button {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 16px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: bold;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }
        button:hover {
            background-color: #2980b9;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }
        button i {
            margin-left: 8px;
        }
        .video-container {
            margin: 30px 0;
            background: #000;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.2);
        }
        video {
            width: 100%;
            max-height: 450px;
        }
        .download-btn {
            margin-top: 20px;
            background-color: #27ae60;
        }
        .download-btn:hover {
            background-color: #219955;
        }
        .success-message {
            color: #27ae60;
            margin-top: 20px;
            font-weight: bold;
            font-size: 18px;
        }
        .error-message {
            color: #e74c3c;
            margin-top: 20px;
            font-weight: bold;
        }
        .features {
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            margin: 30px 0;
        }
        .feature {
            flex: 1;
            min-width: 200px;
            margin: 10px;
            padding: 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05);
        }
        .feature i {
            font-size: 2rem;
            color: #3498db;
            margin-bottom: 15px;
        }
        footer {
            margin-top: 40px;
            color: #7f8c8d;
            font-size: 14px;
        }
        .loading {
            display: none;
            margin: 20px 0;
        }
        .spinner {
            border: 5px solid #f3f3f3;
            border-top: 5px solid #3498db;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <i class="fas fa-video"></i>
        </div>
        <h1>تحميل فيديو Kwai بجودة عالية</h1>
        <p>أدخل رابط الفيديو من Kwai وسنقوم بتحميله لك مباشرة</p>
        
        <form method="post" id="videoForm">
            <div class="form-group">
                <input type="text" name="url" placeholder="https://www.kwai.com/video/..." required>
            </div>
            <button type="submit" id="submitBtn">
                <i class="fas fa-play"></i> عرض الفيديو
            </button>
        </form>

        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>جاري معالجة الفيديو...</p>
        </div>

        {% if video_url %}
        <div class="video-container">
            <video controls autoplay>
                <source src="{{ video_url }}" type="video/mp4">
                متصفحك لا يدعم تشغيل الفيديو.
            </video>
        </div>
        

        {% endif %}

        {% if error %}
        <p class="error-message">{{ error }}</p>
        {% endif %}

        <div class="features">
            <div class="feature">
                <i class="fas fa-bolt"></i>
                <h3>سريع وسهل</h3>
                <p>تحميل الفيديوهات بضغطة واحدة دون انتظار</p>
            </div>
            <div class="feature">
                <i class="fas fa-lock"></i>
                <h3>آمن ومضمون</h3>
                <p>لا نحتفظ بفيديوهاتك بعد التحميل</p>
            </div>
            <div class="feature">
                <i class="fas fa-highlighter"></i>
                <h3>جودة عالية</h3>
                <p>نحافظ على الجودة الأصلية للفيديو</p>
            </div>
        </div>
    </div>

    <footer>
        <p>© 2023 جميع الحقوق محفوظة | خدمة تحميل فيديو Kwai</p>
    </footer>

    <script>
        document.getElementById('videoForm').addEventListener('submit', function() {
            document.getElementById('loading').style.display = 'block';
            document.getElementById('submitBtn').style.display = 'none';
        });
    </script>
</body>
</html>
'''

def download_video(url):
    """تحميل الفيديو وحفظه بمعرف فريد"""
    try:
        # إنشاء اسم فريد للفيديو
        video_id = str(uuid.uuid4())
        filename = f"kwai_video_{video_id}.mp4"
        filepath = os.path.join(TEMP_DIR, filename)
        
        # تحميل الفيديو
        response = requests.get(url, stream=True)
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        
        return filepath, filename
    except Exception as e:
        raise Exception(f"فشل في تحميل الفيديو: {str(e)}")

@app.route('/', methods=['GET', 'POST'])
def index():
    video_url = None
    download_url = None
    error = None

    if request.method == 'POST':
        try:
            u = request.form['url']
            r = requests.get(u)
            s = BeautifulSoup(r.text, 'html.parser')
            
            # البحث عن رابط الفيديو
            video_url = None
            for t in s.find_all('script', type='application/ld+json'):
                if 'VideoObject' in t.text:
                    m = re.search(r'"contentUrl":"(https:[^"]+\.mp4[^"]*)"', t.text)
                    if m:
                        video_url = m.group(1).replace('\\', '')
                        break
            
            if not video_url:
                error = "لم يتم العثور على رابط الفيديو في الصفحة"
            else:
                # إنشاء رابط تحميل مع معرف فريد
                download_url = f"/download?url={video_url}"
                
        except Exception as e:
            error = f"حدث خطأ: {str(e)}"

    return render_template_string(HTML, video_url=video_url, download_url=download_url, error=error)

@app.route('/download')
def download():
    try:
        video_url = request.args.get('url')
        if not video_url:
            return "رابط الفيديو غير صحيح", 400
        
        filepath, filename = download_video(video_url)
        
        @after_this_request
        def remove_file(response):
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                app.logger.error(f"Error removing file {filepath}: {str(e)}")
            return response
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='video/mp4'
        )
        
    except Exception as e:
        return f"حدث خطأ أثناء التحميل: {str(e)}", 500

if __name__ == '__main__':
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
    
    app.run(debug=True, host='0.0.0.0')

#حسو ال علي
