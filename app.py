# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import yaml
from flask import Flask, Response, jsonify

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
CONFIG_PATH = os.path.join(BASE_DIR, "config.yml")

# 内置默认配置（合并完成，无外置文件也可运行）
DEFAULT_CONFIG = {
    "video_folder": "videos",
    "ffmpeg_path": "ffmpeg.exe",
    "host": "0.0.0.0",
    "port": 5000,
    "crf": 30,
    "preset": "ultrafast"
}

# 安全加载 YAML（无注入漏洞）
try:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            CFG = yaml.safe_load(f) or DEFAULT_CONFIG
    else:
        CFG = DEFAULT_CONFIG
except:
    CFG = DEFAULT_CONFIG

VIDEO_FOLDER = os.path.join(BASE_DIR, CFG["video_folder"])
FFMPEG_PATH = os.path.join(BASE_DIR, CFG["ffmpeg_path"])
HOST = CFG["host"]
PORT = CFG["port"]
CRF = CFG["crf"]
PRESET = CFG["preset"]

if not os.path.exists(VIDEO_FOLDER):
    os.makedirs(VIDEO_FOLDER)

def video_stream_generator(video_path):
    command = [
        FFMPEG_PATH, "-i", video_path,
        "-f", "mp4", "-vcodec", "libx264", "-acodec", "aac",
        "-movflags", "frag_keyframe+empty_moov",
        "-preset", PRESET, "-crf", str(CRF), "-y", "-"
    ]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        bufsize=1048576
    )
    while True:
        data = process.stdout.read(1048576)
        if not data:
            break
        yield data

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>XP 视频引擎</title>
<style>
body{background:#111;color:#fff;text-align:center;padding:20px;font-family:Microsoft YaHei}
video{max-width:95%;max-height:700px;border:1px solid #666}
.file-item{padding:8px;background:#222;margin:4px auto;cursor:pointer;width:90%;max-width:600px}
.file-item:hover{background:#333}
</style>
</head>
<body>
<h1>XP 视频引擎</h1>
<video id="player" controls></video>
<div id="fileList"></div>
<script>
function loadVideo(name){player.src='/play/'+encodeURIComponent(name);player.play()}
fetch('/list').then(res=>res.json()).then(data=>{
  data.files.forEach(f=>{
    let div=document.createElement('div');div.className='file-item';div.innerText=f;
    div.onclick=()=>loadVideo(f);document.getElementById('fileList').appendChild(div);
  })
})
</script>
</body>
</html>
'''

@app.route('/list')
def list_videos():
    files = []
    if os.path.exists(VIDEO_FOLDER):
        files = [f for f in os.listdir(VIDEO_FOLDER) if os.path.isfile(os.path.join(VIDEO_FOLDER, f))]
    return jsonify(files=files)

@app.route('/play/<filename>')
def play_video(filename):
    path = os.path.join(VIDEO_FOLDER, filename)
    if not os.path.isfile(path):
        return 'Not Found', 404
    return Response(video_stream_generator(path), mimetype='video/mp4')

if __name__ == '__main__':
    print('========================================')
    print('XP 视频引擎 已启动')
    print(f'视频目录：{VIDEO_FOLDER}')
    print(f'访问地址：http://127.0.0.1:{PORT}')
    print('========================================')
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)