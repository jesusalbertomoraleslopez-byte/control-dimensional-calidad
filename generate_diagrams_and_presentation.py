# -*- coding: utf-8 -*-
"""
Generador de Arquitectura Dinámica Amigable para SIGRAMA 4.0
Incluye:
1. Presentación Interactiva HTML con Animación de Datos en Tiempo Real y Logos (GitHub, Google Cloud, SIGRAMA, Streamlit).
2. Diagrama de Arquitectura Draw.io con flujo de líneas animadas (flowAnimation=1), logos e iconos integrados.
"""

import os
import shutil

# 1. Leer logos base64
with open("scratch_sigrama_b64.txt", "r", encoding="utf-8") as f:
    sigrama_neg_b64 = f.read().strip()

with open("scratch_sigrama_color_b64.txt", "r", encoding="utf-8") as f:
    sigrama_col_b64 = f.read().strip()

# SVGs oficiales de marcas
svg_gcp = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="28" height="28">
  <path fill="#4285F4" d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z"/>
  <path fill="#EA4335" d="M19.35 10.04C18.67 6.59 15.64 4 12 4c-1.48 0-2.85.45-3.98 1.22l2.16 2.16C10.74 7.15 11.35 7 12 7c2.76 0 5 2.24 5 5 0 .25-.03.49-.07.72l2.42 2.42c.62-.97 1-2.12 1-3.35 0-2.64-2.05-4.78-4.65-4.96z"/>
  <path fill="#FBBC05" d="M5.35 8.04C2.34 8.36 0 10.91 0 14c0 2.21 1.2 4.14 2.97 5.17l2.25-2.25C4.46 16.32 4 15.22 4 14c0-2.21 1.79-4 4-4 .38 0 .74.06 1.09.16l2.16-2.16C10.07 7.37 8.78 7.05 7.42 7.13L5.35 8.04z"/>
  <path fill="#34A853" d="M19 19H6c-.57 0-1.11-.12-1.61-.33l-2.25 2.25C3.37 21.57 4.62 22 6 22h13c3.87 0 7-3.13 7-7 0-1.89-.75-3.6-1.97-4.87l-2.03 2.03C22.61 12.82 23 13.86 23 15c0 2.21-1.79 4-4 4z"/>
</svg>"""

svg_github = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="26" height="26" fill="#f8fafc">
  <path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/>
</svg>"""

svg_streamlit = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <path fill="#FF4B4B" d="M12 2L1 21h22L12 2zm0 4.2L19.5 19h-15L12 6.2z"/>
</svg>"""

# ==========================================
# 2. Generar arquitectura_animada.html
# ==========================================
html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SIGRAMA 4.0 — Arquitectura Ciberfísica Interactiva y Animada</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; }}
    body {{ background: #070b14; color: #f1f5f9; overflow-x: hidden; min-height: 100vh; display: flex; flex-direction: column; }}

    /* Banner Superior Amigable */
    header {{
      background: linear-gradient(135deg, #0b1329 0%, #1e1b4b 50%, #0f172a 100%);
      padding: 1rem 2rem;
      border-bottom: 2px solid #ef4444;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 8px 30px rgba(0,0,0,0.6);
      position: relative;
      z-index: 50;
    }}
    .brand-section {{
      display: flex;
      align-items: center;
      gap: 18px;
    }}
    .logo-sigrama-box {{
      background: rgba(255, 255, 255, 0.08);
      padding: 8px 14px;
      border-radius: 10px;
      border: 1px solid rgba(255, 255, 255, 0.15);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }}
    .logo-sigrama-box img {{
      height: 38px;
      width: auto;
      object-fit: contain;
      filter: drop-shadow(0 2px 8px rgba(255,255,255,0.2));
    }}
    .title-box h1 {{
      font-size: 1.45rem;
      font-weight: 800;
      color: #ffffff;
      letter-spacing: 0.5px;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .title-box p {{
      font-size: 0.82rem;
      color: #94a3b8;
      margin-top: 3px;
    }}
    .badge-bar {{
      display: flex;
      gap: 8px;
      margin-top: 5px;
    }}
    .tech-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 0.72rem;
      font-weight: 700;
      padding: 3px 10px;
      border-radius: 9999px;
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: #e2e8f0;
      text-decoration: none;
    }}
    .tech-pill.gcp {{ border-color: rgba(66, 133, 244, 0.4); background: rgba(66, 133, 244, 0.15); color: #93c5fd; }}
    .tech-pill.github {{ border-color: rgba(255, 255, 255, 0.3); background: rgba(255, 255, 255, 0.12); color: #f8fafc; }}
    .tech-pill.streamlit {{ border-color: rgba(239, 68, 68, 0.4); background: rgba(239, 68, 68, 0.15); color: #fca5a5; }}
    .tech-pill.status {{ border-color: rgba(16, 185, 129, 0.4); background: rgba(16, 185, 129, 0.15); color: #6ee7b7; }}

    /* Controles de Animación */
    .controls {{
      display: flex;
      gap: 10px;
      align-items: center;
      background: rgba(15, 23, 42, 0.8);
      padding: 6px 12px;
      border-radius: 10px;
      border: 1px solid #334155;
    }}
    .btn-ctrl {{
      background: #1e293b;
      border: 1px solid #475569;
      color: #f8fafc;
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s;
    }}
    .btn-ctrl:hover {{ background: #334155; border-color: #38bdf8; transform: translateY(-1px); }}
    .btn-ctrl.active {{ background: #ef4444; border-color: #dc2626; color: #fff; box-shadow: 0 0 12px rgba(239, 68, 68, 0.5); }}

    /* Canvas / Viewport */
    .viewport {{
      position: relative;
      flex: 1;
      width: 100%;
      height: 840px;
      overflow: hidden;
      background: radial-gradient(circle at 50% 50%, #111a30 0%, #050811 100%);
    }}

    svg.network-canvas {{
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      z-index: 10;
      pointer-events: none;
    }}

    /* Cables y conexiones animadas */
    .wire {{
      fill: none;
      stroke-width: 3.5;
      stroke-linecap: round;
      stroke-dasharray: 8 6;
      animation: dashMove 1.4s linear infinite;
      filter: drop-shadow(0 0 4px currentColor);
    }}
    .wire.blue {{ stroke: #38bdf8; color: #38bdf8; }}
    .wire.green {{ stroke: #10b981; color: #10b981; }}
    .wire.orange {{ stroke: #f97316; color: #f97316; }}
    .wire.magenta {{ stroke: #ec4899; color: #ec4899; }}
    .wire.purple {{ stroke: #a855f7; color: #a855f7; }}

    @keyframes dashMove {{
      from {{ stroke-dashoffset: 28; }}
      to {{ stroke-dashoffset: 0; }}
    }}

    /* Paquetes que viajan con texto */
    .packet-bubble {{
      position: absolute;
      z-index: 25;
      padding: 4px 10px;
      border-radius: 20px;
      font-size: 0.72rem;
      font-weight: 800;
      color: #ffffff;
      white-space: nowrap;
      pointer-events: none;
      transform: translate(-50%, -50%);
      box-shadow: 0 0 16px currentColor, 0 4px 10px rgba(0,0,0,0.6);
      display: flex;
      align-items: center;
      gap: 5px;
      transition: opacity 0.2s;
    }}
    .bubble-blue {{ background: #0284c7; border: 1.5px solid #38bdf8; color: #ffffff; }}
    .bubble-green {{ background: #059669; border: 1.5px solid #34d399; color: #ffffff; }}
    .bubble-orange {{ background: #ea580c; border: 1.5px solid #fb923c; color: #ffffff; }}
    .bubble-magenta {{ background: #db2777; border: 1.5px solid #f472b6; color: #ffffff; }}
    .bubble-purple {{ background: #7c3aed; border: 1.5px solid #c084fc; color: #ffffff; }}

    /* Zonas Arquitectónicas */
    .zone {{
      position: absolute;
      border-radius: 16px;
      padding: 18px;
      z-index: 5;
      backdrop-filter: blur(12px);
      transition: all 0.3s;
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    .zone-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 14px;
      padding-bottom: 8px;
      border-bottom: 1px solid rgba(255,255,255,0.1);
    }}
    .zone-title {{
      font-size: 0.95rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .zone-tag {{
      font-size: 0.68rem;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 6px;
      background: rgba(255,255,255,0.1);
    }}

    /* Zona 1: Planta */
    #zone-planta {{
      top: 30px;
      left: 30px;
      width: 330px;
      height: 780px;
      background: rgba(15, 23, 42, 0.8);
      border: 2px dashed #475569;
    }}
    #zone-planta .zone-title {{ color: #cbd5e1; }}

    /* Zona 2: Perímetro de Red */
    #zone-perimeter {{
      top: 30px;
      left: 390px;
      width: 270px;
      height: 780px;
      background: rgba(30, 58, 138, 0.22);
      border: 2px solid #2563eb;
    }}
    #zone-perimeter .zone-title {{ color: #60a5fa; }}

    /* Zona 3: Google Cloud Platform */
    #zone-gcp {{
      top: 30px;
      left: 690px;
      right: 30px;
      height: 780px;
      background: rgba(220, 38, 38, 0.08);
      border: 2px solid #ef4444;
    }}
    #zone-gcp .zone-title {{ color: #f87171; }}

    /* Tarjetas Interactivas */
    .node-card {{
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 10px;
      padding: 12px;
      margin-bottom: 12px;
      cursor: pointer;
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
    }}
    .node-card:hover {{
      transform: translateY(-3px) scale(1.02);
      box-shadow: 0 10px 25px rgba(0,0,0,0.5);
      border-color: #38bdf8;
      background: #273549;
    }}
    .node-card h3 {{ font-size: 0.85rem; font-weight: 700; color: #ffffff; display: flex; align-items: center; justify-content: space-between; }}
    .node-card p {{ font-size: 0.74rem; color: #94a3b8; margin-top: 4px; line-height: 1.35; }}
    .card-footer {{ display: flex; justify-content: space-between; align-items: center; margin-top: 8px; }}
    
    .badge {{
      display: inline-block;
      font-size: 0.65rem;
      font-weight: 800;
      padding: 2px 7px;
      border-radius: 4px;
    }}
    .badge-lan {{ background: #334155; color: #cbd5e1; }}
    .badge-https {{ background: #1e3a8a; color: #93c5fd; }}
    .badge-gcp {{ background: #7f1d1d; color: #fca5a5; }}
    .badge-ai {{ background: #064e3b; color: #6ee7b7; }}
    .badge-gcs {{ background: #78350f; color: #fde68a; }}
    .badge-github {{ background: #3b0764; color: #e9d5ff; }}

    /* Cajas anidadas GCP */
    .gcp-box {{
      background: rgba(15, 23, 42, 0.9);
      border-radius: 12px;
      padding: 14px;
      margin-bottom: 14px;
    }}
    .gcp-box.cloudrun {{ border: 1.5px solid #ef4444; }}
    .gcp-box.gcs {{ border: 1.5px solid #f59e0b; }}
    .gcp-box.cicd {{ border: 1.5px solid #a855f7; }}

    /* Footer / Leyenda Amigable */
    footer {{
      background: #090d16;
      border-top: 1px solid #1e293b;
      padding: 12px 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.82rem;
      color: #94a3b8;
    }}
    .legend {{ display: flex; gap: 20px; align-items: center; flex-wrap: wrap; }}
    .legend-item {{ display: flex; align-items: center; gap: 8px; font-weight: 600; }}
    .legend-dot {{ width: 12px; height: 12px; border-radius: 50%; display: inline-block; box-shadow: 0 0 8px currentColor; }}

    /* Tooltip / Modal Explicativo Amigable */
    #info-modal {{
      position: absolute;
      bottom: 25px;
      right: 25px;
      width: 360px;
      background: rgba(15, 23, 42, 0.96);
      border: 2px solid #38bdf8;
      border-radius: 12px;
      padding: 16px;
      z-index: 100;
      box-shadow: 0 15px 40px rgba(0,0,0,0.8);
      display: none;
      backdrop-filter: blur(10px);
      animation: fadeIn 0.3s ease;
    }}
    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    #info-modal h4 {{ color: #38bdf8; font-size: 0.95rem; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }}
    #info-modal p {{ font-size: 0.82rem; color: #cbd5e1; line-height: 1.45; }}
    #info-modal .modal-close {{ position: absolute; top: 12px; right: 12px; background: none; border: none; color: #94a3b8; font-size: 1.2rem; cursor: pointer; }}
    #info-modal .modal-close:hover {{ color: #fff; }}
  </style>
</head>
<body>

  <!-- ENCABEZADO SUPERIOR CON LOGOS Y TÍTULO -->
  <header>
    <div class="brand-section">
      <div class="logo-sigrama-box" title="SIGRAMA Automatización">
        <img src="data:image/png;base64,{sigrama_neg_b64}" alt="SIGRAMA" />
      </div>
      <div class="title-box">
        <h1>
          <span>⚡ SIGRAMA</span>
          <span style="font-weight: 400; color: #94a3b8;">|</span>
          <span style="color: #38bdf8;">Control Dimensional de Calidad 3D con Visión e IA</span>
        </h1>
        <p>Arquitectura Ciberfísica 4.0: Flujo de Datos, Redes y Conexiones en Tiempo Real</p>
        <div class="badge-bar">
          <span class="tech-pill status"><span style="width: 8px; height: 8px; border-radius: 50%; background: #10b981; display: inline-block;"></span> Sistema En Vivo</span>
          <span class="tech-pill gcp">{svg_gcp} Google Cloud Run & GCS</span>
          <span class="tech-pill github">{svg_github} GitHub CI/CD Automático</span>
          <span class="tech-pill streamlit">{svg_streamlit} Streamlit Reactive WebSockets</span>
        </div>
      </div>
    </div>

    <!-- CONTROLES -->
    <div class="controls">
      <button class="btn-ctrl" id="btn-toggle-play">⏸️ Pausar Flujo</button>
      <button class="btn-ctrl" id="btn-speed">Velocidad: 1x</button>
      <button class="btn-ctrl active" id="btn-filter-all">Todos los Flujos</button>
    </div>
  </header>

  <!-- VIEWPORT DE ARQUITECTURA -->
  <div class="viewport" id="viewport">

    <!-- CANVAS SVG DE CABLES Y FLUJOS -->
    <svg class="network-canvas" id="svg-canvas">
      <!-- 1. Cliente UI hacia GFE (HTTPS :443) -->
      <path id="path-client-gfe" class="wire blue" d="M 360 170 L 390 170 L 390 230 L 410 230" />
      
      <!-- 2. GFE hacia Cloud Run (:8080 interno) -->
      <path id="path-gfe-cr" class="wire green" d="M 640 230 L 690 230 L 690 180 L 720 180" />
      
      <!-- 3. Cloud Run hacia SQLite WAL -->
      <path id="path-cr-sqlite" class="wire green" d="M 980 200 L 980 240" />
      
      <!-- 4. SQLite hacia GCS Backup -->
      <path id="path-sqlite-gcs" class="wire orange" d="M 980 320 L 980 430" />
      
      <!-- 5. Sincronizador de Planta hacia GCS Bucket -->
      <path id="path-sync-gcs" class="wire orange" d="M 360 520 L 525 520 L 525 470 L 720 470" />

      <!-- 6. GCS Bucket hacia Signed URL Proxy -->
      <path id="path-gcs-signed" class="wire magenta" d="M 720 530 L 525 530 L 525 580 L 410 580" />
      
      <!-- 7. Signed URL hacia Visor 3D Cliente -->
      <path id="path-signed-client" class="wire magenta" d="M 410 610 L 390 610 L 390 730 L 360 730" />

      <!-- 8. GitHub CI/CD hacia Cloud Run -->
      <path id="path-cicd-cr" class="wire purple" d="M 980 690 L 980 620 L 1150 620 L 1150 200 L 1080 200" />
    </svg>

    <!-- PAQUETES DE DATOS FLOTANTES CON MOVIMIENTO -->
    <div id="packet-1" class="packet-bubble bubble-blue">⚡ Streamlit UI State (:443)</div>
    <div id="packet-2" class="packet-bubble bubble-green">⚙️ HTTP Proxy (:8080)</div>
    <div id="packet-3" class="packet-bubble bubble-orange">💾 SQLite WAL ⇄ GCS Sync</div>
    <div id="packet-4" class="packet-bubble bubble-orange">📁 Planos SHA-256 Upload</div>
    <div id="packet-5" class="packet-bubble bubble-magenta">🧊 STEP 3D Directo (Signed URL)</div>
    <div id="packet-6" class="packet-bubble bubble-magenta">📐 Mesh WebGL al Navegador</div>
    <div id="packet-7" class="packet-bubble bubble-purple">🔄 Push 'main' Deploy Zero-Downtime</div>

    <!-- ZONA 1: PLANTA INDUSTRIAL SIGRAMA -->
    <div class="zone" id="zone-planta">
      <div class="zone-header">
        <div class="zone-title">🏭 Planta SIGRAMA</div>
        <span class="zone-tag">LAN On-Premises</span>
      </div>

      <div class="node-card" onclick="showInfo('inspector')">
        <h3>👷 Inspector de Calidad <span class="badge badge-lan">Tablet / PC</span></h3>
        <p>Captura de cotas de vernier/micrómetro y dictamen pasa/no-pasa en línea de producción.</p>
        <div class="card-footer">
          <span style="font-size: 0.7rem; color: #38bdf8;">Puerto 443 ➔ WSS</span>
          <span class="badge badge-https">UI Web</span>
        </div>
      </div>

      <div class="node-card" onclick="showInfo('engineer')">
        <h3>📐 Ingeniero de Diseño <span class="badge badge-lan">CAD Workstation</span></h3>
        <p>Exportación de archivos STEP, DXF CNC y gestión de tolerancias de doblado y punzonado.</p>
        <div class="card-footer">
          <span style="font-size: 0.7rem; color: #38bdf8;">SolidWorks / Inventor</span>
          <span class="badge badge-lan">LAN 1 Gbps</span>
        </div>
      </div>

      <div class="node-card" onclick="showInfo('nas')">
        <h3>📁 Repositorio SMB / NAS <span class="badge badge-lan">Z:\\ Planos</span></h3>
        <p>Servidor local de ingeniería con base de datos de productos y planos históricos del cliente.</p>
        <div class="card-footer">
          <span style="font-size: 0.7rem; color: #ca8a04;">Puerto 445 SMB</span>
          <span class="badge badge-lan">On-Premises</span>
        </div>
      </div>

      <div class="node-card" onclick="showInfo('sync')">
        <h3>⚡ Sincronizador Local <span class="badge badge-gcs">Python + GUI</span></h3>
        <p>Escaneo incremental con hash SHA-256 para transferir planos de planta a Cloud Storage sin duplicar.</p>
        <div class="card-footer">
          <span style="font-size: 0.7rem; color: #ea580c;">GCS API :443</span>
          <span class="badge badge-gcs">Multi-Hilo</span>
        </div>
      </div>

      <div class="node-card" onclick="showInfo('edgeai')">
        <h3>🖐️ Edge AI: Gestos 3D <span class="badge badge-ai">MediaPipe</span></h3>
        <p>Tracking de 21 articulaciones en WebAssembly y Three.js. Procesa 60 FPS en el cliente con 0 latencia de red.</p>
        <div class="card-footer">
          <span style="font-size: 0.7rem; color: #10b981;">16ms WebAssembly</span>
          <span class="badge badge-ai">Sin Uso de Red</span>
        </div>
      </div>
    </div>

    <!-- ZONA 2: PERÍMETRO DE RED Y SEGURIDAD -->
    <div class="zone" id="zone-perimeter">
      <div class="zone-header">
        <div class="zone-title">🌐 Perímetro Seguro</div>
        <span class="zone-tag">TLS 1.3 / WAF</span>
      </div>

      <div class="node-card" style="margin-top: 40px;" onclick="showInfo('gfe')">
        <h3>🛡️ Google Front End (GFE) <span class="badge badge-https">:443</span></h3>
        <p>Punto de entrada global de Google con terminación SSL/TLS 1.3, mitigación de ataques DDoS y túneles WebSockets.</p>
        <div class="card-footer">
          <span style="font-size: 0.7rem; color: #38bdf8;">Cloud Load Balancing</span>
          <span class="badge badge-https">Cifrado E2E</span>
        </div>
      </div>

      <div class="node-card" style="margin-top: 140px;" onclick="showInfo('signed')">
        <h3>🔑 Canal Signed URLs <span class="badge badge-gcs">HMAC-SHA256</span></h3>
        <p>Tokens de descarga directa de 15 min. El navegador descarga modelos CAD pesados de GCS sin pasar por Cloud Run.</p>
        <div class="card-footer">
          <span style="font-size: 0.7rem; color: #ec4899;">Descarga Directa :443</span>
          <span class="badge badge-gcs">Ahorro RAM</span>
        </div>
      </div>
    </div>

    <!-- ZONA 3: GOOGLE CLOUD PLATFORM -->
    <div class="zone" id="zone-gcp">
      <div class="zone-header">
        <div class="zone-title" style="display: flex; align-items: center; gap: 8px;">
          {svg_gcp} Google Cloud Platform (us-central1)
        </div>
        <span class="zone-tag" style="background: rgba(239, 68, 68, 0.2); color: #fca5a5;">Serverless & Alta Disponibilidad</span>
      </div>

      <!-- Cloud Run -->
      <div class="gcp-box cloudrun">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
          <h3 style="font-size: 0.9rem; color: #fca5a5; display: flex; align-items: center; gap: 8px;">
            🚀 Cloud Run: 'control-dimensional-calidad' <span class="badge badge-gcp">Puerto Interno :8080</span>
          </h3>
          <span style="font-size: 0.75rem; color: #94a3b8;">Contenedor Docker Linux</span>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
          <div class="node-card" onclick="showInfo('streamlit')">
            <h3>⚡ Servidor Streamlit <span class="badge badge-streamlit">Python 3.11</span></h3>
            <p>Ejecución reactiva del Hub Central, Visor 3D, Módulo de Auditoría y Remisiones.</p>
          </div>
          <div class="node-card" onclick="showInfo('sqlite')">
            <h3>🗄️ SQLite WAL In-Container <span class="badge badge-gcp">ACID Local</span></h3>
            <p>Transacciones con PRAGMA WAL y concurrencia multi-usuario sin costo de Cloud SQL.</p>
          </div>
        </div>
      </div>

      <!-- Cloud Storage -->
      <div class="gcp-box gcs">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
          <h3 style="font-size: 0.9rem; color: #fde68a; display: flex; align-items: center; gap: 8px;">
            🪣 Cloud Storage: gs://sigrama-planos-calidad-2026 <span class="badge badge-gcs">SLA 99.95%</span>
          </h3>
          <span style="font-size: 0.75rem; color: #94a3b8;">Cifrado AES-256 en Reposo</span>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px;">
          <div class="node-card" onclick="showInfo('gcs-models')">
            <h3>🧊 Modelos STEP / DXF</h3>
            <p>Carpetas Auditadas/ y Sin_Auditar/ para visualización y control dimensional.</p>
          </div>
          <div class="node-card" onclick="showInfo('gcs-db')">
            <h3>💾 Backup DB SQLite</h3>
            <p>Ruta system/sigrama_calidad.db restaurada automáticamente al arrancar.</p>
          </div>
          <div class="node-card" onclick="showInfo('gcs-pdf')">
            <h3>📄 Planos PDF y Tolerancias</h3>
            <p>Planos de control y matrices de tolerancia generadas para el taller.</p>
          </div>
        </div>
      </div>

      <!-- GitHub CI/CD -->
      <div class="gcp-box cicd">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <h3 style="font-size: 0.9rem; color: #d8b4fe; display: flex; align-items: center; gap: 8px;">
            {svg_github} Canal CI/CD Continuo: GitHub ➔ Cloud Build ➔ Artifact Registry
          </h3>
          <span class="badge badge-github">Zero Downtime Revisions</span>
        </div>
        <p style="font-size: 0.75rem; color: #cbd5e1; margin-top: 6px;">
          Cada confirmación (push) a la rama <strong>main</strong> dispara automáticamente la construcción de imagen Docker y despliegue continuo sin desconectar a los inspectores de planta.
        </p>
      </div>

    </div>

    <!-- MODAL / TOOLTIP EXPLICATIVO INTERACTIVO -->
    <div id="info-modal">
      <button class="modal-close" onclick="closeInfo()">&times;</button>
      <h4 id="modal-title">Componente</h4>
      <p id="modal-desc">Descripción detallada</p>
    </div>

  </div>

  <!-- PIE DE PÁGINA CON LEYENDA TÉCNICA -->
  <footer>
    <div class="legend">
      <div class="legend-item"><span class="legend-dot" style="background: #38bdf8; color: #38bdf8;"></span> 1. Tráfico UI / WebSockets (:443)</div>
      <div class="legend-item"><span class="legend-dot" style="background: #10b981; color: #10b981;"></span> 2. Proxy Interno Cloud Run (:8080)</div>
      <div class="legend-item"><span class="legend-dot" style="background: #f97316; color: #f97316;"></span> 3. Sincronización Planos y SQLite WAL</div>
      <div class="legend-item"><span class="legend-dot" style="background: #ec4899; color: #ec4899;"></span> 4. Streaming Directo CAD (Signed URLs)</div>
      <div class="legend-item"><span class="legend-dot" style="background: #a855f7; color: #a855f7;"></span> 5. CI/CD GitHub Automático</div>
    </div>
    <div style="font-size: 0.75rem; color: #64748b;">
      SIGRAMA Automatización y Control Dimensional © 2026
    </div>
  </footer>

  <!-- SCRIPT DE ANIMACIÓN DINÁMICA DE PAQUETES -->
  <script>
    let isPlaying = true;
    let speed = 1.0;

    const packets = [
      {{ id: 'packet-1', pathId: 'path-client-gfe', progress: 0.1, speed: 0.0035 }},
      {{ id: 'packet-2', pathId: 'path-gfe-cr', progress: 0.35, speed: 0.004 }},
      {{ id: 'packet-3', pathId: 'path-sqlite-gcs', progress: 0.6, speed: 0.003 }},
      {{ id: 'packet-4', pathId: 'path-sync-gcs', progress: 0.2, speed: 0.0028 }},
      {{ id: 'packet-5', pathId: 'path-gcs-signed', progress: 0.8, speed: 0.0035 }},
      {{ id: 'packet-6', pathId: 'path-signed-client', progress: 0.45, speed: 0.0038 }},
      {{ id: 'packet-7', pathId: 'path-cicd-cr', progress: 0.05, speed: 0.0025 }}
    ];

    function animate() {{
      if (isPlaying) {{
        packets.forEach(p => {{
          const path = document.getElementById(p.pathId);
          if (path) {{
            const totalLen = path.getTotalLength();
            p.progress = (p.progress + p.speed * speed) % 1.0;
            const pt = path.getPointAtLength(p.progress * totalLen);
            const el = document.getElementById(p.id);
            if (el) {{
              el.style.left = pt.x + 'px';
              el.style.top = pt.y + 'px';
            }}
          }}
        }});
      }}
      requestAnimationFrame(animate);
    }}
    requestAnimationFrame(animate);

    // Controles
    const btnPlay = document.getElementById('btn-toggle-play');
    btnPlay.addEventListener('click', () => {{
      isPlaying = !isPlaying;
      btnPlay.innerHTML = isPlaying ? '⏸️ Pausar Flujo' : '▶️ Reanudar';
      btnPlay.classList.toggle('active', !isPlaying);
    }});

    const speeds = [0.5, 1.0, 1.75, 3.0];
    let speedIdx = 1;
    const btnSpeed = document.getElementById('btn-speed');
    btnSpeed.addEventListener('click', () => {{
      speedIdx = (speedIdx + 1) % speeds.length;
      speed = speeds[speedIdx];
      btnSpeed.textContent = `Velocidad: ${{speed}}x`;
    }});

    // Modales Explicativos
    const infoData = {{
      inspector: {{
        title: '👷 Inspector de Calidad en Piso de Planta',
        desc: 'Opera en tablets industriales o PCs con vernier y micrómetro. Se comunica con Cloud Run mediante túnel seguro HTTPS/WSS (puerto 443) para registrar cotas y tolerancias en tiempo real sin requerir instalación de software complejo.'
      }},
      engineer: {{
        title: '📐 Ingeniero de Diseño (SolidWorks / CAD)',
        desc: 'Diseña piezas en SolidWorks e Inventor. Exporta ensambles STEP y DXF a la carpeta de ingeniería compartida en red local (SMB). Usa el sincronizador para subir versiones autorizadas a la nube.'
      }},
      nas: {{
        title: '📁 Repositorio SMB / NAS Local (Puerto 445)',
        desc: 'Unidad de red de ingeniería (Z:\\ 02 - INGENIERIA\\BASE DE DATOS PRODUCTOS). Almacena los archivos maestros en planta. No se expone directamente a Internet por razones estrictas de ciberseguridad.'
      }},
      sync: {{
        title: '⚡ Sincronizador de Prototipos SIGRAMA',
        desc: 'Herramienta de escritorio Python 3.12 con interfaz gráfica amigable y lanzador .bat. Realiza escaneos comparativos con sumas de verificación SHA-256 para transferir únicamente archivos nuevos o modificados a Cloud Storage.'
      }},
      edgeai: {{
        title: '🖐️ Edge AI: Control Gestual y 3D en Navegador',
        desc: 'Utiliza Google MediaPipe Hands para detectar 21 puntos anatómicos de la mano a 60 FPS en el navegador del operador. Al procesarse en el cliente (Edge / WebGL / WebAssembly), no consume ancho de banda de la fábrica ni satura el servidor en la nube.'
      }},
      gfe: {{
        title: '🛡️ Google Front End (GFE) & Cloud Load Balancing',
        desc: 'Infraestructura de borde de Google con IP Anycast. Gestiona el puerto 443, descifra el tráfico TLS 1.3 con certificados gestionados y protege contra ataques de denegación de servicio (DDoS) antes de enrutar a Cloud Run.'
      }},
      signed: {{
        title: '🔑 Descarga Directa con Signed URLs (HMAC-SHA256)',
        desc: 'Cloud Run genera URLs firmadas temporales (15 minutos). El navegador descarga modelos STEP pesados (20 a 100 MB) directamente de Cloud Storage, evitando que el contenedor en Cloud Run sufra cuellos de botella de memoria RAM.'
      }},
      streamlit: {{
        title: '⚡ Servidor Streamlit Reactivo (Puerto 8080)',
        desc: 'Servicio en Google Cloud Run que ejecuta la aplicación web completa (Hub 4.0, Visor 3D, Auditoría y Módulo de Remisión). Procesa peticiones HTTP y flujos bidireccionales WebSocket /_stcore/stream.'
      }},
      sqlite: {{
        title: '🗄️ Motor SQLite WAL In-Container',
        desc: 'Base de datos embebida con registro Write-Ahead Logging (WAL) y temporizador busy_timeout de 60 segundos. Brinda máxima velocidad transaccional a costo cero de servidores SQL dedicados, respaldándose continuamente a GCS.'
      }},
      'gcs-models': {{
        title: '🧊 Almacenamiento de Modelos CAD (GCS Bucket)',
        desc: 'Depósito seguro en la nube con réplica multirregional y cifrado en reposo AES-256. Alberga archivos STEP, DXF, SLDPRT y ensambles organizados en carpetas Auditadas y Sin_Auditar.'
      }},
      'gcs-db': {{
        title: '💾 Respaldo y Restauración de Base de Datos',
        desc: 'Ruta protegida gs://.../system/sigrama_calidad.db. Cuando Cloud Run escala a cero o inicia una nueva instancia, descarga la base de datos más reciente para mantener continuidad absoluta de la información.'
      }},
      'gcs-pdf': {{
        title: '📄 Planos PDF y Especificaciones de Calidad',
        desc: 'Repositorio centralizado de hojas de trabajo, remisiones firmadas y planos de control dimensional para consulta inmediata de supervisores e inspectores.'
      }}
    }};

    function showInfo(key) {{
      const d = infoData[key];
      if (d) {{
        document.getElementById('modal-title').textContent = d.title;
        document.getElementById('modal-desc').textContent = d.desc;
        document.getElementById('info-modal').style.display = 'block';
      }}
    }}

    function closeInfo() {{
      document.getElementById('info-modal').style.display = 'none';
    }}
  </script>
</body>
</html>
"""

with open("docs/arquitectura_animada.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("HTML generado exitosamente en docs/arquitectura_animada.html")


# ==========================================
# 3. Generar arquitectura_sigrama_calidad.drawio
# ==========================================
drawio_xml = f"""<mxfile host="app.diagrams.net" agent="Mozilla/5.0">
  <diagram id="sigrama-arch-2026" name="Arquitectura Cloud Run y Calidad 4.0 - SIGRAMA">
    <mxGraphModel dx="1600" dy="850" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1700" pageHeight="1200" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- BANNER SUPERIOR CON TÍTULO, LOGOS Y BADGES -->
        <mxCell id="header_banner" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#0f172a;strokeColor=#ef4444;strokeWidth=2;shadow=1;" value="" vertex="1">
          <mxGeometry height="90" width="1620" x="40" y="20" as="geometry" />
        </mxCell>
        
        <!-- LOGO SIGRAMA -->
        <mxCell id="logo_sigrama_node" parent="header_banner" style="shape=image;html=1;verticalAlign=top;verticalLabelPosition=bottom;labelBackgroundColor=#ffffff;imageAspect=1;aspect=fixed;image=data:image/png;base64,{sigrama_neg_b64};" value="" vertex="1">
          <mxGeometry height="45" width="220" x="25" y="22" as="geometry" />
        </mxCell>

        <!-- TÍTULO PRINCIPAL DEL PROYECTO -->
        <mxCell id="project_title" parent="header_banner" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;" value="&lt;font color=&#39;#ffffff&#39; style=&#39;font-size: 20px; font-weight: 800;&#39;&gt;⚡ SIGRAMA — SISTEMA DE CONTROL DIMENSIONAL Y CALIDAD 3D&lt;/font&gt;&lt;br&gt;&lt;font color=&#39;#94a3b8&#39; style=&#39;font-size: 13px;&#39;&gt;Arquitectura de Infraestructura, Seguridad Perimetral, Flujo de Datos y Redes | Industria 4.0&lt;/font&gt;" vertex="1">
          <mxGeometry height="60" width="750" x="270" y="15" as="geometry" />
        </mxCell>

        <!-- BADGES GOOGLE CLOUD & GITHUB -->
        <mxCell id="badge_gcp" parent="header_banner" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1e293b;strokeColor=#3b82f6;fontStyle=1;fontSize=11;fontColor=#93c5fd;" value="☁️ Google Cloud Platform&#xa;Cloud Run &amp; Cloud Storage" vertex="1">
          <mxGeometry height="50" width="180" x="1170" y="20" as="geometry" />
        </mxCell>
        <mxCell id="badge_github" parent="header_banner" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1e293b;strokeColor=#a855f7;fontStyle=1;fontSize=11;fontColor=#e9d5ff;" value="🐙 GitHub CI/CD&#xa;Continuous Deployment" vertex="1">
          <mxGeometry height="50" width="170" x="1370" y="20" as="geometry" />
        </mxCell>

        <!-- 1. ZONA PLANTA INDUSTRIAL SIGRAMA -->
        <mxCell id="group_onprem" parent="1" style="swimlane;whiteSpace=wrap;html=1;fontSize=14;fontStyle=1;fillColor=#f8fafc;strokeColor=#64748b;strokeWidth=2;startSize=35;dashed=1;" value="🏭 PLANTA INDUSTRIAL SIGRAMA (ON-PREMISES LAN)" vertex="1">
          <mxGeometry height="960" width="380" x="40" y="130" as="geometry" />
        </mxCell>
        <mxCell id="client_operator" parent="group_onprem" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e2e8f0;strokeColor=#475569;fontSize=11;fontStyle=1;shadow=1;" value="👷 INSPECTOR DE CALIDAD EN PISO&#xa;(Tablet / PC Industrial)&#xa;- Inspección Dimensional (Vernier/CMM)&#xa;- Captura de Cotas / Liberación de Lote" vertex="1">
          <mxGeometry height="70" width="320" x="30" y="60" as="geometry" />
        </mxCell>
        <mxCell id="client_engineer" parent="group_onprem" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e2e8f0;strokeColor=#475569;fontSize=11;fontStyle=1;shadow=1;" value="📐 INGENIERO DE DISEÑO (SolidWorks / CAD)&#xa;(Workstation Local)&#xa;- Exportación DXF, STEP, Planos PDF&#xa;- Sincronización Prototipos a la Nube" vertex="1">
          <mxGeometry height="70" width="320" x="30" y="160" as="geometry" />
        </mxCell>
        <mxCell id="client_admin" parent="group_onprem" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e2e8f0;strokeColor=#475569;fontSize=11;fontStyle=1;shadow=1;" value="🛡️ ADMINISTRADOR DE CALIDAD&#xa;(Oficina Técnica)&#xa;- Auditoría de Planos y Matriz de Faltantes&#xa;- Exportación Excel para Ingeniería / Remisiones" vertex="1">
          <mxGeometry height="70" width="320" x="30" y="260" as="geometry" />
        </mxCell>
        <mxCell id="nas_storage" parent="group_onprem" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;fillColor=#fef08a;strokeColor=#ca8a04;fontStyle=1;fontSize=11;shadow=1;" value="📁 REPOSITORIO LOCAL DE PLANOS (SMB / NAS)&#xa;Z:\02 - INGENIERIA\BASE DE DATOS PRODUCTOS\&#xa;- Planos Originales Cliente, DXF CNC, Modelos SLD" vertex="1">
          <mxGeometry height="80" width="320" x="30" y="440" as="geometry" />
        </mxCell>
        <mxCell id="sync_script" parent="group_onprem" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fed7aa;strokeColor=#ea580c;fontStyle=1;fontSize=11;shadow=1;" value="⚡ SINCRONIZADOR DE PROTOTIPOS SIGRAMA&#xa;(Python 3.12 + Tkinter GUI / .bat Launcher)&#xa;- Escaneo incremental hash SHA-256&#xa;- Subida cifrada multi-hilo a Google Cloud" vertex="1">
          <mxGeometry height="75" width="320" x="30" y="560" as="geometry" />
        </mxCell>
        <mxCell id="edge_ai" parent="group_onprem" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dcfce7;strokeColor=#16a34a;fontStyle=1;fontSize=11;shadow=1;" value="🖐️ EDGE AI: CONTROL GESTUAL 3D&#xa;(Google MediaPipe Hands en Browser)&#xa;- Procesamiento local WebAssembly / WebGL&#xa;- 21 Articulaciones a 30-60 FPS (Sin uso de red)" vertex="1">
          <mxGeometry height="70" width="320" x="30" y="730" as="geometry" />
        </mxCell>
        <mxCell id="flow_nas_sync" edge="1" parent="group_onprem" source="nas_storage" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#ca8a04;strokeWidth=2;dashed=1;flowAnimation=1;fontSize=10;" target="sync_script" value="Lectura Carpetas SMB (:445)">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- 2. ZONA PERÍMETRO Y SEGURIDAD -->
        <mxCell id="group_edge" parent="1" style="swimlane;whiteSpace=wrap;html=1;fontSize=14;fontStyle=1;fillColor=#eff6ff;strokeColor=#2563eb;strokeWidth=2;startSize=35;" value="🌐 SEGURIDAD Y PERÍMETRO DE TRÁFICO (INTERNET / TLS 1.3)" vertex="1">
          <mxGeometry height="960" width="280" x="460" y="130" as="geometry" />
        </mxCell>
        <mxCell id="waf_gfe" parent="group_edge" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#bfdbfe;strokeColor=#1d4ed8;fontStyle=1;fontSize=12;shadow=1;" value="🛡️ GOOGLE FRONT END (GFE)&#xa;&amp; CLOUD LOAD BALANCING&#xa;- Puerto 443 (HTTPS)&#xa;- Terminación TLS 1.3 Cifrada&#xa;- Mitigación DDoS / WAF&#xa;- Enrutamiento WebSockets / HTTP/2" vertex="1">
          <mxGeometry height="110" width="240" x="20" y="152" as="geometry" />
        </mxCell>
        <mxCell id="signed_url_layer" parent="group_edge" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fbcfe8;strokeColor=#db2777;fontStyle=1;fontSize=11;shadow=1;" value="🔑 CANAL DE ACCESO DIRECTO GCS&#xa;(Signed URLs con HMAC SHA-256)&#xa;- Descarga directa de archivos CAD (STEP/DXF)&#xa;- Sin sobrecargar la memoria del servidor&#xa;- Expiración efímera (15 min)" vertex="1">
          <mxGeometry height="90" width="240" x="20" y="550" as="geometry" />
        </mxCell>

        <!-- 3. ZONA GOOGLE CLOUD PLATFORM -->
        <mxCell id="group_gcp" parent="1" style="swimlane;whiteSpace=wrap;html=1;fontSize=14;fontStyle=1;fillColor=#fafafa;strokeColor=#dc2626;strokeWidth=2;startSize=35;" value="☁️ GOOGLE CLOUD PLATFORM (us-central1)" vertex="1">
          <mxGeometry height="960" width="880" x="780" y="130" as="geometry" />
        </mxCell>

        <!-- Cloud Run -->
        <mxCell id="cloud_run" parent="group_gcp" style="swimlane;whiteSpace=wrap;html=1;fontSize=13;fontStyle=1;fillColor=#fee2e2;strokeColor=#dc2626;strokeWidth=2;startSize=30;shadow=1;" value="🚀 GOOGLE CLOUD RUN (Serverless Container)&#xa;Servicio: 'control-dimensional-calidad' | Puerto Interno: 8080" vertex="1">
          <mxGeometry height="420" width="820" x="30" y="60" as="geometry" />
        </mxCell>
        <mxCell id="streamlit_core" parent="cloud_run" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#dc2626;fontStyle=1;fontSize=11;" value="🐍 STREAMLIT REACTIVE APP SERVER (Python 3.11)&#xa;- Gestión de Sesión y Estado UI (SessionState)&#xa;- WebSockets bidireccionales /_stcore/stream&#xa;- Puerto: 8080 (Mapeado desde GFE 443)" vertex="1">
          <mxGeometry height="60" width="760" x="30" y="50" as="geometry" />
        </mxCell>
        <mxCell id="mod_hub" parent="cloud_run" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f1f5f9;strokeColor=#64748b;fontSize=10;fontStyle=1;" value="📊 MÓDULO 0&#xa;Hub Central 4.0&#xa;(v0_hub.py)" vertex="1">
          <mxGeometry height="60" width="135" x="30" y="130" as="geometry" />
        </mxCell>
        <mxCell id="mod_cad" parent="cloud_run" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f1f5f9;strokeColor=#64748b;fontSize=10;fontStyle=1;" value="🧊 MÓDULO 3.1&#xa;Visor 3D Three.js&#xa;(v3_1_cad_viewer.py)" vertex="1">
          <mxGeometry height="60" width="135" x="185" y="130" as="geometry" />
        </mxCell>
        <mxCell id="mod_audit" parent="cloud_run" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f1f5f9;strokeColor=#64748b;fontSize=10;fontStyle=1;" value="📋 MÓDULO 3.2&#xa;Auditoría Técnica&#xa;(v3_2_design.py)" vertex="1">
          <mxGeometry height="60" width="135" x="340" y="130" as="geometry" />
        </mxCell>
        <mxCell id="mod_insp" parent="cloud_run" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f1f5f9;strokeColor=#64748b;fontSize=10;fontStyle=1;" value="📐 MÓDULO 3.3 / 4.2&#xa;Inspección Dimensional&#xa;(v3_3_capture.py)" vertex="1">
          <mxGeometry height="60" width="135" x="495" y="130" as="geometry" />
        </mxCell>
        <mxCell id="mod_rep" parent="cloud_run" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f1f5f9;strokeColor=#64748b;fontSize=10;fontStyle=1;" value="📑 MÓDULO 3.4 / 4.3&#xa;Reportes y Remisión&#xa;(v3_3_remision.py)" vertex="1">
          <mxGeometry height="60" width="135" x="650" y="130" as="geometry" />
        </mxCell>
        <mxCell id="sqlite_local" parent="cloud_run" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;fillColor=#e0f2fe;strokeColor=#0284c7;fontStyle=1;fontSize=11;" value="🗄️ SQLITE3 MOTOR IN-CONTAINER (data/sigrama_calidad.db)&#xa;- PRAGMA journal_mode = WAL (Write-Ahead Logging de alto rendimiento)&#xa;- PRAGMA busy_timeout = 60000 | Concurrencia de lecturas simultáneas&#xa;- Sincronización bidireccional automática con Cloud Storage" vertex="1">
          <mxGeometry height="75" width="760" x="30" y="210" as="geometry" />
        </mxCell>
        <mxCell id="service_gcs" parent="cloud_run" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ede9fe;strokeColor=#7c3aed;fontStyle=1;fontSize=10;" value="🔐 GCS Storage Client (src/services/gcs_storage.py)&#xa;Service Account HMAC Signer / Resolver" vertex="1">
          <mxGeometry height="50" width="370" x="30" y="310" as="geometry" />
        </mxCell>
        <mxCell id="service_excel" parent="cloud_run" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ede9fe;strokeColor=#7c3aed;fontStyle=1;fontSize=10;" value="📊 Generador Excel Multisede (src/audit_excel.py)&#xa;Reporte de Faltantes &amp; Auditoría General" vertex="1">
          <mxGeometry height="50" width="370" x="420" y="310" as="geometry" />
        </mxCell>

        <!-- Cloud Storage -->
        <mxCell id="gcs_bucket" parent="group_gcp" style="swimlane;whiteSpace=wrap;html=1;fontSize=13;fontStyle=1;fillColor=#fef3c7;strokeColor=#d97706;strokeWidth=2;startSize=30;shadow=1;" value="🪣 GOOGLE CLOUD STORAGE BUCKET (gs://sigrama-planos-calidad-2026)&#xa;Almacenamiento Objeto Cifrado AES-256 (Default KMS) | SLA 99.95%" vertex="1">
          <mxGeometry height="240" width="820" x="30" y="514" as="geometry" />
        </mxCell>
        <mxCell id="gcs_db_backup" parent="gcs_bucket" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#d97706;fontStyle=1;fontSize=11;" value="💾 system/sigrama_calidad.db&#xa;(Persistencia de Estado / Transacciones)" vertex="1">
          <mxGeometry height="60" width="360" x="30" y="50" as="geometry" />
        </mxCell>
        <mxCell id="gcs_models" parent="gcs_bucket" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#d97706;fontStyle=1;fontSize=11;" value="🧊 Auditadas/ &amp; Sin_Auditar/&#xa;(Archivos STEP 3D, DXF, SLDPRT, SLDDRW)" vertex="1">
          <mxGeometry height="60" width="370" x="420" y="50" as="geometry" />
        </mxCell>
        <mxCell id="gcs_blueprints" parent="gcs_bucket" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#d97706;fontStyle=1;fontSize=11;" value="📄 Planos_PDF/&#xa;(Planos de Control SIGRAMA y Cliente)" vertex="1">
          <mxGeometry height="60" width="360" x="30" y="140" as="geometry" />
        </mxCell>
        <mxCell id="gcs_specs" parent="gcs_bucket" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#d97706;fontStyle=1;fontSize=11;" value="📊 Especificaciones_Excel/&#xa;(Hojas de Tolerancias de Doblez y Corte)" vertex="1">
          <mxGeometry height="60" width="370" x="420" y="140" as="geometry" />
        </mxCell>

        <!-- CI/CD GitHub & Cloud Build -->
        <mxCell id="cicd_box" parent="group_gcp" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f3e8ff;strokeColor=#9333ea;fontStyle=1;fontSize=11;shadow=1;" value="🔄 CI/CD PIPELINE: GITHUB ➔ GOOGLE CLOUD BUILD ➔ ARTIFACT REGISTRY&#xa;- Trigger automático en push a &#39;main&#39;&#xa;- Construcción multi-stage Dockerfile con optimización de capas de caché&#xa;- Despliegue sin tiempo de inactividad (Zero Downtime Revisions) en Cloud Run" vertex="1">
          <mxGeometry height="70" width="820" x="30" y="800" as="geometry" />
        </mxCell>
        <mxCell id="flow_cicd_deploy" edge="1" parent="group_gcp" source="cicd_box" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#9333ea;strokeWidth=3;dashed=1;flowAnimation=1;fontSize=10;fontStyle=1;" target="cloud_run" value="Zero-Downtime Deployment">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- CONECTORES CON ANIMACIÓN DE FLUJO (flowAnimation=1) -->
        <mxCell id="flow_clients_gfe" edge="1" parent="1" source="client_engineer" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#2563eb;strokeWidth=3;fontSize=11;fontStyle=1;dashed=1;flowAnimation=1;" target="waf_gfe" value="HTTPS :443 (TLS 1.3 / WSS) [Datos UI / WebSockets]">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="flow_gfe_cr" edge="1" parent="1" source="waf_gfe" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#16a34a;strokeWidth=3;fontSize=11;fontStyle=1;dashed=1;flowAnimation=1;" target="streamlit_core" value="HTTP :8080 (VPC Interna) [Tráfico Descifrado]">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="flow_sync_gcs" edge="1" parent="1" source="sync_script" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#ea580c;strokeWidth=3;dashed=1;flowAnimation=1;fontSize=11;fontStyle=1;" target="gcs_bucket" value="GCS REST API :443 (Upload Prototipos Hash SHA-256)">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="430" y="730" />
              <mxPoint x="430" y="690" />
            </Array>
          </mxGeometry>
        </mxCell>
        <mxCell id="flow_db_backup" edge="1" parent="1" source="sqlite_local" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#d97706;strokeWidth=3;dashed=1;flowAnimation=1;fontSize=10;fontStyle=1;" target="gcs_db_backup" value="Sync Bidireccional DB (save_database_to_gcs)">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="flow_signed_url" edge="1" parent="1" source="gcs_bucket" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#db2777;strokeWidth=3;dashed=1;flowAnimation=1;fontSize=11;fontStyle=1;" target="signed_url_layer" value="Descarga Directa Cifrada (Signed URLs GET :443)">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="flow_signed_to_client" edge="1" parent="1" source="signed_url_layer" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#db2777;strokeWidth=3;dashed=1;flowAnimation=1;fontSize=11;fontStyle=1;" target="edge_ai" value="STEP 3D / DXF Streaming al Navegador">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
"""

with open("docs/arquitectura_sigrama_calidad.drawio", "w", encoding="utf-8") as f:
    f.write(drawio_xml)

print("Draw.io XML generado exitosamente en docs/arquitectura_sigrama_calidad.drawio")

# ==========================================
# 4. Copiar a Desktop
# ==========================================
desktop_path = os.path.expanduser(r"~\Desktop")
dest_html = os.path.join(desktop_path, "arquitectura_animada.html")
dest_drawio = os.path.join(desktop_path, "arquitectura_sigrama_calidad.drawio")

shutil.copy2("docs/arquitectura_animada.html", dest_html)
shutil.copy2("docs/arquitectura_sigrama_calidad.drawio", dest_drawio)

print(f"Copiado a Desktop:\n - {dest_html}\n - {dest_drawio}")
