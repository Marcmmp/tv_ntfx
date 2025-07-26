import os
import json
import mimetypes
import socket
from pathlib import Path
from flask import Flask, render_template_string, send_file, jsonify, request, Response
from flask_cors import CORS
import cv2
from PIL import Image
import io
import hashlib
import subprocess
import random
from datetime import datetime
import threading
import time

class StreamFlix:
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Configuración
        self.host = self.get_local_ip()
        self.port = 8888
        
        # Carpetas de contenido
        self.movies_folder = os.path.join(os.path.expanduser("~"), "StreamFlix", "Movies")
        self.series_folder = os.path.join(os.path.expanduser("~"), "StreamFlix", "Series")
        self.thumbnails_folder = os.path.join(os.path.expanduser("~"), "StreamFlix", ".thumbnails")
        
        # Crear carpetas
        for folder in [self.movies_folder, self.series_folder, self.thumbnails_folder]:
            os.makedirs(folder, exist_ok=True)
        
        # Base de datos de contenido
        self.content_db = {
            'movies': [],
            'series': [],
            'continue_watching': [],
            'categories': {
                'trending': [],
                'new_releases': [],
                'action': [],
                'comedy': [],
                'drama': [],
                'scifi': [],
                'horror': []
            }
        }
        
        # Escanear contenido
        self.scan_content()
        
        # Configurar rutas
        self.setup_routes()
    
    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def generate_thumbnail(self, video_path, output_path):
        """Genera miniatura del video"""
        try:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Capturar frame al 10% del video
            frame_pos = int(total_frames * 0.1)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            
            ret, frame = cap.read()
            if ret:
                # Redimensionar a 16:9
                height = 200
                width = int(height * 16 / 9)
                frame = cv2.resize(frame, (width, height))
                
                # Guardar
                cv2.imwrite(output_path, frame)
            
            cap.release()
            return True
        except:
            return False
    
    def get_video_duration(self, video_path):
        """Obtiene duración del video"""
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            duration = frame_count / fps
            cap.release()
            
            # Formatear duración
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            
            if hours > 0:
                return f"{hours}h {minutes}min"
            else:
                return f"{minutes} min"
        except:
            return "Unknown"
    
    def scan_content(self):
        """Escanea las carpetas de contenido"""
        print("🔍 Escaneando contenido...")
        print(f"📁 Buscando en: {self.movies_folder}")
        
        # Escanear películas
        self.content_db['movies'] = []
        video_extensions = ('.mp4', '.mkv', '.avi', '.mov', '.webm', '.MP4', '.MKV', '.AVI', '.MOV')
        
        # Debug: mostrar archivos encontrados
        all_files = os.listdir(self.movies_folder)
        print(f"📄 Archivos en Movies: {all_files}")
        
        for file in all_files:
            if file.endswith(video_extensions):
                video_path = os.path.join(self.movies_folder, file)
                video_id = hashlib.md5(file.encode()).hexdigest()[:8]
                
                print(f"✅ Video encontrado: {file}")
                
                # Generar thumbnail si no existe
                thumb_path = os.path.join(self.thumbnails_folder, f"{video_id}.jpg")
                if not os.path.exists(thumb_path):
                    print(f"🎨 Generando thumbnail para: {file}")
                    self.generate_thumbnail(video_path, thumb_path)
                
                movie = {
                    'id': video_id,
                    'title': os.path.splitext(file)[0].replace('_', ' ').title(),
                    'file': file,
                    'path': video_path,
                    'thumbnail': f"/thumbnail/{video_id}.jpg",
                    'duration': self.get_video_duration(video_path),
                    'year': random.randint(2018, 2024),
                    'rating': round(random.uniform(7.0, 9.5), 1),
                    'match': random.randint(85, 99)
                }
                
                self.content_db['movies'].append(movie)
        
        # Asignar a categorías aleatorias (simulación)
        if self.content_db['movies']:
            random.shuffle(self.content_db['movies'])
            self.content_db['categories']['trending'] = self.content_db['movies'][:5]
            self.content_db['categories']['new_releases'] = self.content_db['movies'][:3]
        
        print(f"✅ Encontradas {len(self.content_db['movies'])} películas")
    
    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template_string('''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="color-scheme" content="dark">
    <meta name="theme-color" content="#141414">
    <title>StreamFlix</title>
    <style>
        /* Forzar modo oscuro para TVs */
        :root {
            color-scheme: dark;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        html {
            background-color: #141414 !important;
            background: #141414 !important;
        }
        
        body {
            font-family: 'Netflix Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: #141414 !important;
            background: #141414 !important;
            color: #ffffff !important;
            overflow-x: hidden;
            user-select: none;
            min-height: 100vh;
            -webkit-text-size-adjust: 100%;
            -webkit-font-smoothing: antialiased;
        }
        
        /* Forzar fondo oscuro en todos los elementos */
        div, section, header, nav, article, aside, footer {
            background-color: transparent !important;
            color: #ffffff !important;
        }
        
        /* Prevenir fondos blancos en TVs */
        input, textarea, select, button {
            background-color: rgba(0,0,0,0.8) !important;
            color: #ffffff !important;
            border: 1px solid #333 !important;
        }
        
        /* Estilos adicionales para forzar modo oscuro en TVs */
        @media screen {
            html, body {
                background: #141414 !important;
                background-color: #141414 !important;
            }
        }
        
        /* Para TVs con WebKit antiguo */
        @media screen and (-webkit-min-device-pixel-ratio:0) {
            body {
                background: #141414 !important;
                -webkit-background-size: 100% 100%;
            }
        }
        
        /* Prevenir flash blanco al cargar */
        html:not(.loaded) * {
            animation-duration: 0s !important;
            transition: none !important;
        }
        
        /* Scrollbar personalizada */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #141414;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #555;
            border-radius: 4px;
        }
        
        /* Header */
        .header {
            position: fixed;
            top: 0;
            width: 100%;
            padding: 20px 50px;
            background: linear-gradient(to bottom, rgba(0,0,0,0.9) 0%, transparent 100%);
            z-index: 1000;
            transition: all 0.3s ease;
        }
        
        .header.scrolled {
            background: #141414;
            padding: 15px 50px;
        }
        
        .nav {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .logo {
            font-size: 32px;
            font-weight: bold;
            color: #e50914;
            text-transform: uppercase;
            letter-spacing: 2px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
        
        .nav-links {
            display: flex;
            gap: 30px;
            list-style: none;
        }
        
        .nav-links a {
            color: #e5e5e5;
            text-decoration: none;
            font-size: 14px;
            transition: color 0.3s;
        }
        
        .nav-links a:hover {
            color: #fff;
        }
        
        /* Hero Section */
        .hero {
            position: relative;
            height: 80vh;
            min-height: 600px;
            display: flex;
            align-items: center;
            overflow: hidden;
        }
        
        .hero-bg {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
        }
        
        .hero-bg img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            filter: brightness(0.5);
        }
        
        .hero-gradient {
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 50%;
            background: linear-gradient(to top, #141414 0%, transparent 100%);
        }
        
        .hero-content {
            padding: 0 50px;
            max-width: 600px;
            z-index: 1;
        }
        
        .hero-title {
            font-size: 64px;
            font-weight: bold;
            margin-bottom: 20px;
            text-shadow: 3px 3px 6px rgba(0,0,0,0.8);
            animation: fadeInUp 0.8s ease;
        }
        
        .hero-description {
            font-size: 20px;
            line-height: 1.6;
            margin-bottom: 30px;
            color: #e5e5e5;
            animation: fadeInUp 0.8s ease 0.2s both;
        }
        
        .hero-buttons {
            display: flex;
            gap: 15px;
            animation: fadeInUp 0.8s ease 0.4s both;
        }
        
        .btn {
            padding: 12px 30px;
            border: none;
            border-radius: 4px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 10px;
            text-decoration: none;
        }
        
        .btn-primary {
            background: #fff;
            color: #000;
        }
        
        .btn-primary:hover {
            background: #e5e5e5;
            transform: scale(1.05);
        }
        
        .btn-secondary {
            background: rgba(109, 109, 110, 0.7);
            color: #fff;
            backdrop-filter: blur(4px);
        }
        
        .btn-secondary:hover {
            background: rgba(109, 109, 110, 0.9);
            transform: scale(1.05);
        }
        
        /* Content Sections */
        .content-section {
            padding: 0 50px;
            margin-bottom: 50px;
        }
        
        .section-title {
            font-size: 24px;
            margin-bottom: 20px;
            font-weight: 600;
        }
        
        /* Carousel */
        .carousel-container {
            position: relative;
            margin: 0 -50px;
            padding: 0 50px;
            overflow: hidden;
        }
        
        .carousel {
            display: flex;
            gap: 8px;
            overflow-x: auto;
            scroll-behavior: smooth;
            scrollbar-width: none;
            -ms-overflow-style: none;
            padding-bottom: 10px;
        }
        
        .carousel::-webkit-scrollbar {
            display: none;
        }
        
        .carousel-item {
            flex: 0 0 auto;
            width: 250px;
            cursor: pointer;
            transition: transform 0.3s ease;
            position: relative;
            border-radius: 4px;
            overflow: hidden;
        }
        
        .carousel-item:hover {
            transform: scale(1.3);
            z-index: 10;
        }
        
        .carousel-item:hover .item-info {
            opacity: 1;
        }
        
        .carousel-item img {
            width: 100%;
            height: 140px;
            object-fit: cover;
            border-radius: 4px;
        }
        
        .item-info {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            padding: 20px 15px 15px;
            background: linear-gradient(to top, rgba(0,0,0,0.9) 0%, transparent 100%);
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        
        .item-title {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 5px;
        }
        
        .item-meta {
            display: flex;
            gap: 10px;
            font-size: 12px;
            color: #46d369;
        }
        
        .item-controls {
            display: flex;
            gap: 8px;
            margin-top: 10px;
        }
        
        .control-btn {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            border: 2px solid rgba(255,255,255,0.7);
            background: rgba(0,0,0,0.5);
            color: #fff;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .control-btn:hover {
            background: #fff;
            color: #000;
            border-color: #fff;
        }
        
        /* Video Player Overlay */
        .video-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: #000;
            z-index: 2000;
            display: none;
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        
        .video-overlay.active {
            display: flex;
            opacity: 1;
        }
        
        .video-container {
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }
        
        video {
            width: 100%;
            height: 100%;
            max-width: 100%;
            max-height: 100%;
        }
        
        .video-controls {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            padding: 20px;
            background: linear-gradient(to top, rgba(0,0,0,0.8) 0%, transparent 100%);
            display: flex;
            align-items: center;
            gap: 20px;
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        
        .video-container:hover .video-controls {
            opacity: 1;
        }
        
        .close-video {
            position: absolute;
            top: 20px;
            right: 20px;
            width: 40px;
            height: 40px;
            background: rgba(0,0,0,0.7);
            border: none;
            border-radius: 50%;
            color: #fff;
            font-size: 24px;
            cursor: pointer;
            transition: all 0.3s ease;
            z-index: 10;
        }
        
        .close-video:hover {
            background: #e50914;
            transform: scale(1.1);
        }
        
        /* Loading Animation */
        .loading {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            display: none;
        }
        
        .loading.active {
            display: block;
        }
        
        .spinner {
            width: 60px;
            height: 60px;
            border: 3px solid rgba(255,255,255,0.3);
            border-top-color: #e50914;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .header, .content-section {
                padding: 15px 20px;
            }
            
            .hero-title {
                font-size: 36px;
            }
            
            .hero-description {
                font-size: 16px;
            }
            
            .carousel-item {
                width: 150px;
            }
            
            .carousel-item img {
                height: 85px;
            }
            
            .nav-links {
                display: none;
            }
        }
    </style>
    <script>
        // Marcar cuando esté cargado
        window.addEventListener('load', () => {
            document.documentElement.classList.add('loaded');
        });
    </script>
</head>
<body>
    <!-- Header -->
    <header class="header" id="header">
        <nav class="nav">
            <div class="logo">StreamFlix</div>
            <ul class="nav-links">
                <li><a href="#home">Inicio</a></li>
                <li><a href="#movies">Películas</a></li>
                <li><a href="#series">Series</a></li>
                <li><a href="#mylist">Mi Lista</a></li>
            </ul>
        </nav>
    </header>
    
    <!-- Hero Section -->
    <section class="hero">
        <div class="hero-bg">
            <img src="https://source.unsplash.com/1600x900/?movie,cinema" alt="Hero">
        </div>
        <div class="hero-gradient"></div>
        <div class="hero-content">
            <h1 class="hero-title">Bienvenido a StreamFlix</h1>
            <p class="hero-description">Tu biblioteca personal de streaming. Disfruta de todas tus películas y series favoritas en cualquier dispositivo.</p>
            <div class="hero-buttons">
                <button class="btn btn-primary" onclick="playRandom()">
                    <span>▶</span> Reproducir
                </button>
                <button class="btn btn-secondary" onclick="showInfo()">
                    <span>ⓘ</span> Más información
                </button>
            </div>
        </div>
    </section>
    
    <!-- Content Sections -->
    <div id="content-wrapper">
        <!-- Se llenará dinámicamente -->
    </div>
    
    <!-- Video Player Overlay -->
    <div class="video-overlay" id="videoOverlay">
        <div class="video-container">
            <button class="close-video" onclick="closeVideo()">×</button>
            <video id="videoPlayer" controls></video>
            <div class="video-controls">
                <!-- Controles personalizados aquí si quieres -->
            </div>
        </div>
    </div>
    
    <!-- Loading -->
    <div class="loading" id="loading">
        <div class="spinner"></div>
    </div>
    
    <script>
        let contentData = {};
        
        // Detectar scroll para header
        window.addEventListener('scroll', () => {
            const header = document.getElementById('header');
            if (window.scrollY > 50) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        });
        
        // Cargar contenido
        async function loadContent() {
            try {
                const response = await fetch('/api/content');
                contentData = await response.json();
                renderContent();
            } catch (error) {
                console.error('Error loading content:', error);
            }
        }
        
        // Renderizar contenido
        function renderContent() {
            const wrapper = document.getElementById('content-wrapper');
            let html = '';
            
            // Trending
            if (contentData.categories.trending.length > 0) {
                html += createSection('Tendencias', contentData.categories.trending);
            }
            
            // All Movies
            if (contentData.movies.length > 0) {
                html += createSection('Todas las Películas', contentData.movies);
            }
            
            // New Releases
            if (contentData.categories.new_releases.length > 0) {
                html += createSection('Nuevos Lanzamientos', contentData.categories.new_releases);
            }
            
            wrapper.innerHTML = html;
        }
        
        // Crear sección
        function createSection(title, items) {
            let html = `
                <section class="content-section">
                    <h2 class="section-title">${title}</h2>
                    <div class="carousel-container">
                        <div class="carousel">
            `;
            
            items.forEach(item => {
                html += `
                    <div class="carousel-item" onclick="playVideo('${item.id}')">
                        <img src="${item.thumbnail}" alt="${item.title}" onerror="this.src='https://via.placeholder.com/250x140/222/666?text=${encodeURIComponent(item.title)}'">
                        <div class="item-info">
                            <h3 class="item-title">${item.title}</h3>
                            <div class="item-meta">
                                <span>${item.match}% coincidencia</span>
                                <span>${item.year}</span>
                                <span>${item.duration}</span>
                            </div>
                            <div class="item-controls">
                                <div class="control-btn" onclick="event.stopPropagation(); playVideo('${item.id}')">▶</div>
                                <div class="control-btn" onclick="event.stopPropagation(); addToList('${item.id}')">+</div>
                                <div class="control-btn" onclick="event.stopPropagation(); likeVideo('${item.id}')">👍</div>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += `
                        </div>
                    </div>
                </section>
            `;
            
            return html;
        }
        
        // Reproducir video
        async function playVideo(videoId) {
            const loading = document.getElementById('loading');
            loading.classList.add('active');
            
            try {
                const response = await fetch(`/api/play/${videoId}`);
                const data = await response.json();
                
                const overlay = document.getElementById('videoOverlay');
                const player = document.getElementById('videoPlayer');
                
                // Configurar player para TVs
                player.setAttribute('playsinline', '');
                player.setAttribute('webkit-playsinline', '');
                player.setAttribute('x-webkit-airplay', 'allow');
                
                // Detectar si es TV y ajustar
                const isTV = /tv|smart|tizen|webos|roku|hbbtv/i.test(navigator.userAgent);
                if (isTV) {
                    player.setAttribute('controls', 'controls');
                    // Algunos TVs necesitan un delay
                    setTimeout(() => {
                        player.src = data.url;
                        player.load();
                        player.play().catch(e => {
                            console.log('Autoplay bloqueado, reproducir manualmente');
                        });
                    }, 100);
                } else {
                    player.src = data.url;
                    player.play();
                }
                
                overlay.classList.add('active');
            } catch (error) {
                console.error('Error playing video:', error);
                alert('Error al reproducir el video');
            } finally {
                loading.classList.remove('active');
            }
        }
        
        // Cerrar video
        function closeVideo() {
            const overlay = document.getElementById('videoOverlay');
            const player = document.getElementById('videoPlayer');
            
            player.pause();
            player.src = '';
            overlay.classList.remove('active');
        }
        
        // Reproducir aleatorio
        function playRandom() {
            if (contentData.movies && contentData.movies.length > 0) {
                const random = contentData.movies[Math.floor(Math.random() * contentData.movies.length)];
                playVideo(random.id);
            }
        }
        
        // Funciones placeholder
        function showInfo() {
            alert('StreamFlix - Tu streaming personal\\n\\nColoca tus videos en las carpetas Movies y Series');
        }
        
        function addToList(videoId) {
            console.log('Añadido a la lista:', videoId);
        }
        
        function likeVideo(videoId) {
            console.log('Like:', videoId);
        }
        
        // Cargar al inicio
        loadContent();
    </script>
</body>
</html>
            ''')
        
        @self.app.route('/api/content')
        def get_content():
            return jsonify(self.content_db)
        
        @self.app.route('/api/play/<video_id>')
        def get_video_url(video_id):
            # Detectar si es un TV por el user agent
            user_agent = request.headers.get('User-Agent', '').lower()
            is_tv = any(tv in user_agent for tv in ['tv', 'smart', 'tizen', 'webos', 'roku', 'hbbtv'])
            
            # Buscar video por ID
            for movie in self.content_db['movies']:
                if movie['id'] == video_id:
                    # Usar streaming normal para mejor rendimiento
                    stream_url = f'/stream/{video_id}'
                    return jsonify({
                        'url': stream_url,
                        'title': movie['title'],
                        'is_tv': is_tv
                    })
            
            return jsonify({'error': 'Video not found'}), 404
        
        @self.app.route('/stream/<video_id>')
        def stream_video(video_id):
            # Buscar video
            video_path = None
            for movie in self.content_db['movies']:
                if movie['id'] == video_id:
                    video_path = movie['path']
                    break
            
            if not video_path or not os.path.exists(video_path):
                return "Video not found", 404
            
            # Detectar si es un TV
            user_agent = request.headers.get('User-Agent', '').lower()
            is_tv = any(tv in user_agent for tv in ['tv', 'smart', 'tizen', 'webos', 'roku', 'hbbtv'])
            
            # Si no hay rango especificado y es TV, devolver todo el archivo
            range_header = request.headers.get('range', None)
            if not range_header and is_tv:
                # Devolver archivo completo para TVs que no soporten streaming parcial
                return send_file(video_path, mimetype='video/mp4')
            
            # Streaming con soporte para seek
            byte_start = 0
            byte_end = None
            
            if range_header:
                match = re.search(r'bytes=(\d+)-(\d*)', range_header)
                if match:
                    byte_start = int(match.group(1))
                    if match.group(2):
                        byte_end = int(match.group(2))
            
            file_size = os.path.getsize(video_path)
            
            # Chunks más pequeños para TVs (mejor compatibilidad)
            chunk_size = 524288 if is_tv else 1048576  # 512KB para TVs, 1MB para otros
            
            if byte_end is None:
                byte_end = min(byte_start + chunk_size, file_size - 1)
            
            content_length = byte_end - byte_start + 1
            
            def generate():
                with open(video_path, 'rb') as f:
                    f.seek(byte_start)
                    remaining = content_length
                    while remaining:
                        to_read = min(65536, remaining)
                        data = f.read(to_read)
                        if not data:
                            break
                        remaining -= len(data)
                        yield data
            
            # Headers optimizados para TVs
            response = Response(
                generate(),
                status=206,
                mimetype='video/mp4',  # Forzar MP4 para mayor compatibilidad
                headers={
                    'Content-Range': f'bytes {byte_start}-{byte_end}/{file_size}',
                    'Accept-Ranges': 'bytes',
                    'Content-Length': str(content_length),
                    'Content-Type': 'video/mp4',
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
                    'Access-Control-Allow-Headers': 'Range, Content-Type',
                    'Access-Control-Expose-Headers': 'Content-Length, Content-Range'
                }
            )
            
            return response
        
        @self.app.route('/stream/<video_id>/compat')
        def stream_compatible_video(video_id):
            """Streaming con conversión en tiempo real para TVs"""
            # Buscar video
            video_path = None
            for movie in self.content_db['movies']:
                if movie['id'] == video_id:
                    video_path = movie['path']
                    break
            
            if not video_path or not os.path.exists(video_path):
                return "Video not found", 404
            
            # Usar ffmpeg para transcodificar en tiempo real (opcional)
            # Esto requiere tener ffmpeg instalado
            try:
                command = [
                    'ffmpeg',
                    '-i', video_path,
                    '-c:v', 'libx264',      # Codec H.264 (más compatible)
                    '-preset', 'ultrafast',  # Conversión rápida
                    '-crf', '23',           # Calidad
                    '-c:a', 'aac',          # Audio AAC
                    '-b:a', '128k',
                    '-movflags', 'frag_keyframe+empty_moov+faststart',
                    '-f', 'mp4',            # Formato MP4
                    'pipe:1'                # Salida a stdout
                ]
                
                def generate():
                    try:
                        process = subprocess.Popen(
                            command,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL,
                            bufsize=65536
                        )
                        
                        while True:
                            chunk = process.stdout.read(65536)
                            if not chunk:
                                break
                            yield chunk
                    finally:
                        try:
                            process.terminate()
                            process.wait()
                        except:
                            pass
                
                return Response(
                    generate(),
                    mimetype='video/mp4',
                    headers={
                        'Cache-Control': 'no-cache',
                        'Access-Control-Allow-Origin': '*'
                    }
                )
            except:
                # Si ffmpeg no está disponible, usar streaming normal
                return send_file(video_path, mimetype='video/mp4')
        
        @self.app.route('/thumbnail/<video_id>.jpg')
        def get_thumbnail(video_id):
            thumb_path = os.path.join(self.thumbnails_folder, f"{video_id}.jpg")
            if os.path.exists(thumb_path):
                return send_file(thumb_path, mimetype='image/jpeg')
            else:
                # Generar placeholder
                return '', 404
    
    def run(self):
        import webbrowser
        import re
        
        url = f"http://{self.host}:{self.port}"
        
        print("\n" + "="*60)
        print("🎬 StreamFlix - Tu Netflix Personal")
        print("="*60)
        print(f"\n📱 Accede desde cualquier dispositivo:")
        print(f"   {url}")
        print(f"\n📁 Carpetas de contenido:")
        print(f"   • Películas → {self.movies_folder}")
        print(f"   • Series → {self.series_folder}")
        print(f"\n💡 Coloca tus videos MP4/MKV/AVI en las carpetas")
        print("\n🔄 Ctrl+C para detener")
        print("="*60 + "\n")
        
        # Abrir carpetas
        for folder in [self.movies_folder, self.series_folder]:
            try:
                os.startfile(folder)  # Windows
            except:
                try:
                    os.system(f'open "{folder}"')  # macOS
                except:
                    os.system(f'xdg-open "{folder}"')  # Linux
        
        # Abrir navegador
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
        
        # Ejecutar servidor
        self.app.run(host='0.0.0.0', port=self.port, debug=False, threaded=True)

if __name__ == "__main__":
    import re  # Importar re para el streaming
    
    netflix = StreamFlix()
    try:
        netflix.run()
    except KeyboardInterrupt:
        print("\n\n🎬 ¡Hasta la próxima!")
