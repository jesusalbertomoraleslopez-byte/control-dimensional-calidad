# -*- coding: utf-8 -*-
"""
Generador de Arquitectura Dinámica Amigable para SIGRAMA 4.0
Incluye:
1. Las 2 Redes VPC en us-central1 (vpc-sigrama-vm y vpc-sigrama-cloudrun) con VPC Peering y los 2 Cloud Run.
2. La distinción entre Cuentas de Usuario, Cuentas de Servicio y el Rol Personalizado (sigrama_calidad_operador) para jesus_aml@hotmail.com.
3. El Balanceador de Cargas Global (IP 136.81.184.225) y Google Front End.
4. Animación interactiva en HTML y soporte nativo flowAnimation=1 en Draw.io.
"""

import os
import shutil
import base64

# 1. Leer logos base64 directamente
with open("logo_sigrama_negative.png", "rb") as f:
    sigrama_neg_b64 = base64.b64encode(f.read()).decode("utf-8")

with open("logo_sigrama.png", "rb") as f:
    sigrama_col_b64 = base64.b64encode(f.read()).decode("utf-8")

# SVGs oficiales
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
  <title>SIGRAMA 4.0 — Arquitectura Ciberfísica con Doble Red VPC y Roles IAM</title>
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
    .brand-section {{ display: flex; align-items: center; gap: 18px; }}
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
    .logo-sigrama-box img {{ height: 38px; width: auto; object-fit: contain; filter: drop-shadow(0 2px 8px rgba(255,255,255,0.2)); }}
    .title-box h1 {{
      font-size: 1.4rem;
      font-weight: 800;
      color: #ffffff;
      letter-spacing: 0.5px;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .title-box p {{ font-size: 0.82rem; color: #94a3b8; margin-top: 3px; }}
    .badge-bar {{ display: flex; gap: 8px; margin-top: 5px; flex-wrap: wrap; }}
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
    .tech-pill.iam {{ border-color: rgba(234, 179, 8, 0.4); background: rgba(234, 179, 8, 0.15); color: #fde047; }}
    .tech-pill.vpc {{ border-color: rgba(56, 189, 248, 0.4); background: rgba(56, 189, 248, 0.15); color: #7dd3fc; }}
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
      height: 940px;
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
    .wire.cyan {{ stroke: #06b6d4; color: #06b6d4; }}
    .wire.yellow {{ stroke: #eab308; color: #eab308; }}

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
    .bubble-blue {{ background: #0284c7; border: 1.5px solid #38bdf8; }}
    .bubble-green {{ background: #059669; border: 1.5px solid #34d399; }}
    .bubble-orange {{ background: #ea580c; border: 1.5px solid #fb923c; }}
    .bubble-magenta {{ background: #db2777; border: 1.5px solid #f472b6; }}
    .bubble-purple {{ background: #7c3aed; border: 1.5px solid #c084fc; }}
    .bubble-cyan {{ background: #0891b2; border: 1.5px solid #22d3ee; }}
    .bubble-yellow {{ background: #ca8a04; border: 1.5px solid #fde047; }}

    /* Zonas Arquitectónicas */
    .zone {{
      position: absolute;
      border-radius: 16px;
      padding: 16px;
      z-index: 5;
      backdrop-filter: blur(12px);
      transition: all 0.3s;
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    .zone-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      padding-bottom: 6px;
      border-bottom: 1px solid rgba(255,255,255,0.1);
    }}
    .zone-title {{
      font-size: 0.92rem;
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
      top: 20px;
      left: 20px;
      width: 310px;
      height: 890px;
      background: rgba(15, 23, 42, 0.8);
      border: 2px dashed #475569;
    }}
    #zone-planta .zone-title {{ color: #cbd5e1; }}

    /* Zona 2: Perímetro de Red */
    #zone-perimeter {{
      top: 20px;
      left: 350px;
      width: 250px;
      height: 890px;
      background: rgba(30, 58, 138, 0.22);
      border: 2px solid #2563eb;
    }}
    #zone-perimeter .zone-title {{ color: #60a5fa; }}

    /* Zona 3: Google Cloud Platform */
    #zone-gcp {{
      top: 20px;
      left: 620px;
      right: 20px;
      height: 890px;
      background: rgba(220, 38, 38, 0.06);
      border: 2px solid #ef4444;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}
    #zone-gcp .zone-title {{ color: #f87171; }}

    /* Tarjetas Interactivas */
    .node-card {{
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 10px;
      padding: 10px 12px;
      margin-bottom: 10px;
      cursor: pointer;
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
    }}
    .node-card:hover {{
      transform: translateY(-2px) scale(1.015);
      box-shadow: 0 10px 25px rgba(0,0,0,0.5);
      border-color: #38bdf8;
      background: #273549;
    }}
    .node-card h3 {{ font-size: 0.83rem; font-weight: 700; color: #ffffff; display: flex; align-items: center; justify-content: space-between; }}
    .node-card p {{ font-size: 0.72rem; color: #94a3b8; margin-top: 3px; line-height: 1.35; }}
    .card-footer {{ display: flex; justify-content: space-between; align-items: center; margin-top: 6px; }}
    
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
    .badge-vpc {{ background: #083344; color: #67e8f9; }}
    .badge-iam {{ background: #713f12; color: #fef08a; }}

    /* Cajas anidadas GCP */
    .gcp-row {{ display: grid; grid-template-columns: 1.4fr 1fr; gap: 12px; }}
    .gcp-box {{
      background: rgba(15, 23, 42, 0.92);
      border-radius: 12px;
      padding: 12px 14px;
    }}
    .gcp-box.vpc1 {{ border: 1.5px solid #0284c7; }}
    .gcp-box.vpc2 {{ border: 1.5px solid #ef4444; }}
    .gcp-box.iam {{ border: 1.5px solid #eab308; }}
    .gcp-box.storage {{ border: 1.5px solid #f59e0b; }}

    /* Footer / Leyenda Amigable */
    footer {{
      background: #090d16;
      border-top: 1px solid #1e293b;
      padding: 10px 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.78rem;
      color: #94a3b8;
    }}
    .legend {{ display: flex; gap: 18px; align-items: center; flex-wrap: wrap; }}
    .legend-item {{ display: flex; align-items: center; gap: 7px; font-weight: 600; }}
    .legend-dot {{ width: 11px; height: 11px; border-radius: 50%; display: inline-block; box-shadow: 0 0 8px currentColor; }}

    /* Modal / Tooltip */
    #info-modal {{
      position: absolute;
      bottom: 25px;
      right: 25px;
      width: 380px;
      background: rgba(15, 23, 42, 0.97);
      border: 2px solid #38bdf8;
      border-radius: 12px;
      padding: 16px;
      z-index: 100;
      box-shadow: 0 15px 40px rgba(0,0,0,0.85);
      display: none;
      backdrop-filter: blur(10px);
      animation: fadeIn 0.3s ease;
    }}
    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    #info-modal h4 {{ color: #38bdf8; font-size: 0.95rem; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }}
    #info-modal p {{ font-size: 0.81rem; color: #cbd5e1; line-height: 1.45; }}
    #info-modal .modal-close {{ position: absolute; top: 10px; right: 12px; background: none; border: none; color: #94a3b8; font-size: 1.3rem; cursor: pointer; }}
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
        <p>Infraestructura Ciberfísica 4.0: Doble Red VPC, 2 Servicios Cloud Run, Balanceador de Carga y Roles Personalizados IAM</p>
        <div class="badge-bar">
          <span class="tech-pill status"><span style="width: 8px; height: 8px; border-radius: 50%; background: #10b981; display: inline-block;"></span> Sistema En Vivo</span>
          <span class="tech-pill vpc">🌐 2 Redes VPC Peered (VM ⇄ Cloud Run)</span>
          <span class="tech-pill gcp">{svg_gcp} 2 Servicios Cloud Run & GFE (IP: 136.81.184.225)</span>
          <span class="tech-pill iam">🛡️ Rol Personalizado: jesus_aml@hotmail.com</span>
        </div>
      </div>
    </div>

    <!-- CONTROLES -->
    <div class="controls">
      <button class="btn-ctrl" id="btn-toggle-play">⏸️ Pausar Flujo</button>
      <button class="btn-ctrl" id="btn-speed">Velocidad: 1x</button>
    </div>
  </header>

  <!-- VIEWPORT DE ARQUITECTURA -->
  <div class="viewport" id="viewport">

    <!-- CANVAS SVG DE CABLES Y FLUJOS -->
    <svg class="network-canvas" id="svg-canvas">
      <!-- 1. Cliente UI hacia GFE (HTTPS :443 / LB IP 136.81.184.225) -->
      <path id="path-client-gfe" class="wire blue" d="M 330 160 L 370 160 L 370 210 L 390 210" />
      
      <!-- 2. GFE hacia Cloud Run 1 en VPC 2 (:8080) -->
      <path id="path-gfe-cr1" class="wire green" d="M 570 210 L 630 210 L 630 140 L 660 140" />

      <!-- 3. GFE hacia Cloud Run 2 (Prototipos) -->
      <path id="path-gfe-cr2" class="wire green" d="M 570 250 L 610 250 L 610 280 L 660 280" />
      
      <!-- 4. VPC Peering: Cloud Run (VPC 2) ⇄ VM (VPC 1) -->
      <path id="path-vpc-peering" class="wire cyan" d="M 970 210 L 1020 210 L 1020 180 L 1050 180" />

      <!-- 5. Cloud Run hacia SQLite WAL / GCS Sync -->
      <path id="path-cr-storage" class="wire orange" d="M 850 330 L 850 490 L 1050 490" />
      
      <!-- 6. Sincronizador de Planta hacia GCS Bucket -->
      <path id="path-sync-gcs" class="wire orange" d="M 330 540 L 580 540 L 580 520 L 1050 520" />

      <!-- 7. GCS Bucket hacia Signed URL Proxy -->
      <path id="path-gcs-signed" class="wire magenta" d="M 1050 550 L 580 550 L 580 610 L 570 610" />
      
      <!-- 8. Signed URL hacia Visor 3D Cliente -->
      <path id="path-signed-client" class="wire magenta" d="M 390 610 L 360 610 L 360 740 L 330 740" />

      <!-- 9. Asignación de Permisos IAM a Cloud Run -->
      <path id="path-iam-role" class="wire yellow" d="M 1050 710 L 850 710 L 850 330" />
    </svg>

    <!-- PAQUETES DE DATOS FLOTANTES CON MOVIMIENTO -->
    <div id="packet-1" class="packet-bubble bubble-blue">⚡ Tráfico UI ➔ LB (136.81.184.225)</div>
    <div id="packet-2" class="packet-bubble bubble-green">🚀 Cloud Run 1: sigrama-calidad-app</div>
    <div id="packet-3" class="packet-bubble bubble-green">🧊 Cloud Run 2: sigrama-calidad-prototipos</div>
    <div id="packet-4" class="packet-bubble bubble-cyan">🔗 VPC Peering Privado (10.20.0.0 ⇄ 10.10.0.0)</div>
    <div id="packet-5" class="packet-bubble bubble-orange">💾 Persistencia GCS gs://sigrama-planos</div>
    <div id="packet-6" class="packet-bubble bubble-magenta">🔑 STEP 3D Directo (Signed URL :443)</div>
    <div id="packet-7" class="packet-bubble bubble-yellow">🛡️ IAM: jesus_aml@hotmail.com (Custom Role)</div>

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
        <span class="zone-tag">GFE & Balanceador</span>
      </div>

      <div class="node-card" style="margin-top: 30px;" onclick="showInfo('lb')">
        <h3>⚖️ Balanceador de Carga Global <span class="badge badge-https">IP Externa</span></h3>
        <p><strong>IP: 136.81.184.225</strong> (Puerto 80). Enruta tráfico HTTP/WSS al Serverless NEG de Cloud Run con esquema EXTERNAL_MANAGED.</p>
        <div class="card-footer">
          <span style="font-size: 0.7rem; color: #10b981;">● Activo (200 OK)</span>
          <span class="badge badge-https">lb-sigrama</span>
        </div>
      </div>

      <div class="node-card" style="margin-top: 20px;" onclick="showInfo('gfe')">
        <h3>🛡️ Google Front End (GFE) <span class="badge badge-https">:443 / :80</span></h3>
        <p>Punto de presencia Anycast con mitigación de ataques DDoS y túneles WebSockets bidireccionales permanentes.</p>
        <div class="card-footer">
          <span style="font-size: 0.7rem; color: #38bdf8;">Cloud Load Balancing</span>
          <span class="badge badge-https">Cifrado E2E</span>
        </div>
      </div>

      <div class="node-card" style="margin-top: 180px;" onclick="showInfo('signed')">
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
          {svg_gcp} Google Cloud Platform (us-central1) — sigrama-cloud-calidad
        </div>
        <span class="zone-tag" style="background: rgba(239, 68, 68, 0.2); color: #fca5a5;">2 Redes VPC + 2 Cloud Run + IAM Custom Roles</span>
      </div>

      <!-- FILA SUPERIOR: LAS DOS REDES VPC PEERED -->
      <div class="gcp-row">
        
        <!-- VPC 2: vpc-sigrama-cloudrun (CON LOS 2 SERVICIOS CLOUD RUN) -->
        <div class="gcp-box vpc2">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <h3 style="font-size: 0.88rem; color: #fca5a5; display: flex; align-items: center; gap: 6px;">
              🚀 VPC 2: <code>vpc-sigrama-cloudrun</code>
            </h3>
            <span class="badge badge-vpc">Subred: 10.20.0.0/24 (us-central1)</span>
          </div>

          <!-- Cloud Run 1 -->
          <div class="node-card" onclick="showInfo('cr1')">
            <h3>⚡ Cloud Run 1: 'sigrama-calidad-app' <span class="badge badge-gcp">:8080</span></h3>
            <p>App principal Streamlit: Hub Central 4.0, captura de tolerancias de vernier, auditoría y remisiones de calidad.</p>
            <div class="card-footer">
              <span style="font-size: 0.68rem; color: #38bdf8;">Serverless NEG: neg-sigrama-app</span>
              <span class="badge badge-gcp">Producción</span>
            </div>
          </div>

          <!-- Cloud Run 2 -->
          <div class="node-card" onclick="showInfo('cr2')">
            <h3>🧊 Cloud Run 2: 'sigrama-calidad-prototipos' <span class="badge badge-gcp">:8080</span></h3>
            <p>Microservicio CAD: procesamiento de geometrías STEP 3D, exportación CNC DXF y visor de prototipos industriales.</p>
            <div class="card-footer">
              <span style="font-size: 0.68rem; color: #f87171;">Servicio Autónomo CAD</span>
              <span class="badge badge-gcp">Prototipos</span>
            </div>
          </div>

          <!-- SQLite In-Container WAL -->
          <div class="node-card" onclick="showInfo('sqlite')">
            <h3>🗄️ SQLite WAL In-Container (data/sigrama_calidad.db)</h3>
            <p>Motor transaccional ultrarrápido con PRAGMA WAL y concurrencia sin costo de Cloud SQL.</p>
          </div>
        </div>

        <!-- VPC 1: vpc-sigrama-vm (CON LA MÁQUINA VIRTUAL) -->
        <div class="gcp-box vpc1">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <h3 style="font-size: 0.88rem; color: #7dd3fc; display: flex; align-items: center; gap: 6px;">
              🖥️ VPC 1: <code>vpc-sigrama-vm</code>
            </h3>
            <span class="badge badge-vpc">Subred: 10.10.0.0/24</span>
          </div>

          <!-- VM Compute Engine -->
          <div class="node-card" onclick="showInfo('vm')">
            <h3>💻 VM Compute Engine: 'vm-sigrama-backend'</h3>
            <p>Máquina Virtual dedicada a servicios internos de planta: Servidor de base de datos relacional y respaldo SMB.</p>
            <div class="card-footer">
              <span style="font-size: 0.68rem; color: #38bdf8;">IP Privada: 10.10.0.5</span>
              <span class="badge badge-lan">e2-medium</span>
            </div>
          </div>

          <!-- Peering Box -->
          <div class="node-card" style="border: 1.5px dashed #06b6d4; background: rgba(6, 182, 212, 0.1);" onclick="showInfo('peering')">
            <h3>🔗 VPC Network Peering <span class="badge badge-ai">ACTIVE</span></h3>
            <p><code>peer-vm-to-cloudrun</code> ⇄ <code>peer-cloudrun-to-vm</code>: Conexión privada directa sin pasar por Internet.</p>
          </div>
        </div>

      </div>

      <!-- FILA INFERIOR: CLOUD STORAGE + IAM ROLES PERSONALIZADOS -->
      <div class="gcp-row">
        
        <!-- Cloud Storage Bucket -->
        <div class="gcp-box storage">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <h3 style="font-size: 0.85rem; color: #fde68a; display: flex; align-items: center; gap: 6px;">
              🪣 Cloud Storage: gs://sigrama-planos-calidad-2026
            </h3>
            <span class="badge badge-gcs">SLA 99.95% | AES-256</span>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
            <div class="node-card" onclick="showInfo('gcs-models')">
              <h3>🧊 Modelos STEP / DXF</h3>
              <p>Carpetas Auditadas/ y Sin_Auditar/ para visualización y cotas.</p>
            </div>
            <div class="node-card" onclick="showInfo('gcs-db')">
              <h3>💾 Backup DB SQLite</h3>
              <p>system/sigrama_calidad.db restaurada automáticamente.</p>
            </div>
          </div>
        </div>

        <!-- SECCIÓN IAM: CUENTAS DE USUARIO VS SERVICIO VS ROL PERSONALIZADO -->
        <div class="gcp-box iam">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <h3 style="font-size: 0.85rem; color: #fef08a; display: flex; align-items: center; gap: 6px;">
              🛡️ IAM: Gestión de Identidades y Roles
            </h3>
            <span class="badge badge-iam">Principio de Menor Privilegio</span>
          </div>

          <!-- Rol Personalizado -->
          <div class="node-card" style="border: 1.5px solid #eab308; background: rgba(234, 179, 8, 0.15);" onclick="showInfo('custom-role')">
            <h3>⭐ Rol Personalizado: 'sigrama_calidad_operador'</h3>
            <p><strong>Usuario Asignado:</strong> <code>user:jesus_aml@hotmail.com</code></p>
            <p style="color: #fef08a; font-size: 0.68rem; margin-top: 4px;">
              Permisos: run.services.get/list, storage.objects.get/create, compute.networks.get. Sin privilegios destructivos.
            </p>
          </div>

          <!-- Comparación Cuentas -->
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px;">
            <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid #334155; border-radius: 6px; padding: 6px;">
              <span style="font-size: 0.68rem; font-weight: 800; color: #93c5fd;">👤 Cuentas de Usuario:</span>
              <p style="font-size: 0.65rem; color: #cbd5e1;">jesus_aml@hotmail.com<br>jesus.alberto...@gmail.com</p>
            </div>
            <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid #334155; border-radius: 6px; padding: 6px;">
              <span style="font-size: 0.68rem; font-weight: 800; color: #c084fc;">🤖 Cuentas de Servicio:</span>
              <p style="font-size: 0.65rem; color: #cbd5e1;">streamlit-app-acceso@...<br>500497...-compute@...</p>
            </div>
          </div>
        </div>

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
      <div class="legend-item"><span class="legend-dot" style="background: #38bdf8; color: #38bdf8;"></span> 1. Tráfico UI ➔ Balanceador GFE (136.81.184.225:80)</div>
      <div class="legend-item"><span class="legend-dot" style="background: #10b981; color: #10b981;"></span> 2. Enrutamiento a Cloud Run 1 y 2 (VPC 2)</div>
      <div class="legend-item"><span class="legend-dot" style="background: #06b6d4; color: #06b6d4;"></span> 3. VPC Peering Privado (VPC 2 ⇄ VPC 1)</div>
      <div class="legend-item"><span class="legend-dot" style="background: #f97316; color: #f97316;"></span> 4. Persistencia Cloud Storage gs://</div>
      <div class="legend-item"><span class="legend-dot" style="background: #ec4899; color: #ec4899;"></span> 5. Signed URLs Directas CAD</div>
      <div class="legend-item"><span class="legend-dot" style="background: #eab308; color: #eab308;"></span> 6. Rol Personalizado IAM (jesus_aml@hotmail.com)</div>
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
      {{ id: 'packet-2', pathId: 'path-gfe-cr1', progress: 0.35, speed: 0.004 }},
      {{ id: 'packet-3', pathId: 'path-gfe-cr2', progress: 0.25, speed: 0.0038 }},
      {{ id: 'packet-4', pathId: 'path-vpc-peering', progress: 0.5, speed: 0.003 }},
      {{ id: 'packet-5', pathId: 'path-sync-gcs', progress: 0.2, speed: 0.0028 }},
      {{ id: 'packet-6', pathId: 'path-gcs-signed', progress: 0.75, speed: 0.0035 }},
      {{ id: 'packet-7', pathId: 'path-iam-role', progress: 0.6, speed: 0.0032 }}
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
      lb: {{
        title: '⚖️ Balanceador de Carga Global (IP 136.81.184.225)',
        desc: 'Balanceador de aplicaciones externo global de Google Cloud (Cloud Load Balancing). Posee la regla de reenvío lb-sigrama-forwarding-rule en el puerto 80 apuntando a los servidores perimetrales GFE y al backend de Cloud Run.'
      }},
      gfe: {{
        title: '🛡️ Google Front End (GFE) & Proxy de Capa 7',
        desc: 'Punto de entrada de alta disponibilidad de Google. Termina la conexión del usuario, mitiga ataques DDoS y transmite WebSockets hacia los dos servicios Cloud Run en la VPC 2.'
      }},
      cr1: {{
        title: '🚀 Cloud Run 1: sigrama-calidad-app',
        desc: 'Servicio en vpc-sigrama-cloudrun (10.20.0.0/24). Aloja el frontend Streamlit principal, sistema de cotas de vernier, dictamen dimensional de piezas y remisiones de calidad.'
      }},
      cr2: {{
        title: '🧊 Cloud Run 2: sigrama-calidad-prototipos',
        desc: 'Segundo microservicio en vpc-sigrama-cloudrun. Dedicado exclusivamente al procesamiento y validación de prototipos CAD 3D (STEP/DXF) para no interferir con la app principal de piso.'
      }},
      vm: {{
        title: '💻 Máquina Virtual en VPC 1 (vpc-sigrama-vm)',
        desc: 'Instancia Compute Engine en la subred 10.10.0.0/24. Cumple la función de servidor de base de datos relacional y repositorio de archivos maestro en la nube, aislada de la red pública.'
      }},
      peering: {{
        title: '🔗 VPC Network Peering (Conexión Privada entre Redes)',
        desc: 'Emparejamiento activo entre vpc-sigrama-vm y vpc-sigrama-cloudrun. Permite que los contenedores de Cloud Run se comuniquen con la Máquina Virtual a través de la red interna de Google (SDN Andromeda) con latencia mínima y cero exposición pública.'
      }},
      'custom-role': {{
        title: '⭐ Rol Personalizado IAM: sigrama_calidad_operador',
        desc: 'Asignado a jesus_aml@hotmail.com. Otorga permisos granulares: run.services.get, run.services.list, storage.objects.get, storage.objects.create y compute.networks.get. No es un rol genérico (Owner/Editor); sigue estrictamente el Principio de Menor Privilegio (PoLP).'
      }},
      inspector: {{
        title: '👷 Inspector de Calidad en Piso de Planta',
        desc: 'Opera en tablets industriales o PCs con vernier y micrómetro. Se comunica con el Balanceador mediante túnel seguro (puerto 80/443) para registrar cotas y tolerancias en tiempo real.'
      }},
      nas: {{
        title: '📁 Repositorio SMB / NAS Local (Puerto 445)',
        desc: 'Unidad de red de ingeniería (Z:\\ 02 - INGENIERIA\\BASE DE DATOS PRODUCTOS). Almacena los planos maestros en planta de forma protegida.'
      }},
      sync: {{
        title: '⚡ Sincronizador de Prototipos SIGRAMA',
        desc: 'Herramienta de escritorio Python 3.12 con interfaz gráfica amigable. Realiza escaneos comparativos SHA-256 para transferir únicamente planos nuevos o modificados a Cloud Storage.'
      }},
      edgeai: {{
        title: '🖐️ Edge AI: Control Gestual en Navegador',
        desc: 'Google MediaPipe Hands en WebAssembly a 60 FPS. Detecta 21 articulaciones de la mano para rotar e inspeccionar modelos 3D sin tocar la pantalla con las manos sucias de taller.'
      }},
      signed: {{
        title: '🔑 Descarga Directa con Signed URLs (HMAC-SHA256)',
        desc: 'El navegador descarga modelos STEP pesados (20-100 MB) directamente de Cloud Storage, evitando saturar la memoria RAM de los contenedores de Cloud Run.'
      }},
      'gcs-models': {{
        title: '🧊 Modelos CAD en Cloud Storage',
        desc: 'Depósito seguro en gs://sigrama-planos-calidad-2026 organizado en carpetas Auditadas/ y Sin_Auditar/ con cifrado AES-256.'
      }},
      'gcs-db': {{
        title: '💾 Respaldo y Restauración de Base de Datos',
        desc: 'system/sigrama_calidad.db se sincroniza tras cada liberación de lote para mantener continuidad total de datos ante reinicios o escalado a cero.'
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
  <diagram id="sigrama-arch-2026" name="Arquitectura Cloud Run, 2 VPCs y Calidad 4.0 - SIGRAMA">
    <mxGraphModel dx="1800" dy="1000" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1850" pageHeight="1300" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- BANNER SUPERIOR CON TÍTULO, LOGOS Y BADGES -->
        <mxCell id="header_banner" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#0f172a;strokeColor=#ef4444;strokeWidth=2;shadow=1;" value="" vertex="1">
          <mxGeometry height="95" width="1770" x="40" y="20" as="geometry" />
        </mxCell>
        
        <!-- LOGO SIGRAMA -->
        <mxCell id="logo_sigrama_node" parent="header_banner" style="shape=image;html=1;verticalAlign=top;verticalLabelPosition=bottom;labelBackgroundColor=#ffffff;imageAspect=1;aspect=fixed;image=data:image/png;base64,{sigrama_neg_b64};" value="" vertex="1">
          <mxGeometry height="45" width="220" x="25" y="25" as="geometry" />
        </mxCell>

        <!-- TÍTULO PRINCIPAL DEL PROYECTO -->
        <mxCell id="project_title" parent="header_banner" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;" value="&lt;font color=&#39;#ffffff&#39; style=&#39;font-size: 19px; font-weight: 800;&#39;&gt;⚡ SIGRAMA — CONTROL DIMENSIONAL Y CALIDAD 3D (ARQUITECTURA CLOUD RUN 4.0)&lt;/font&gt;&lt;br&gt;&lt;font color=&#39;#94a3b8&#39; style=&#39;font-size: 12px;&#39;&gt;Infraestructura con Doble Red VPC (VM ⇄ 2 Cloud Run), Balanceador Global (136.81.184.225) y Roles Personalizados IAM&lt;/font&gt;" vertex="1">
          <mxGeometry height="60" width="850" x="270" y="18" as="geometry" />
        </mxCell>

        <!-- BADGES GOOGLE CLOUD & IAM -->
        <mxCell id="badge_gcp" parent="header_banner" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1e293b;strokeColor=#3b82f6;fontStyle=1;fontSize=10;fontColor=#93c5fd;" value="☁️ Google Cloud Platform&#xa;Balanceador Global :80&#xa;IP: 136.81.184.225" vertex="1">
          <mxGeometry height="60" width="180" x="1190" y="18" as="geometry" />
        </mxCell>
        <mxCell id="badge_iam" parent="header_banner" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1e293b;strokeColor=#eab308;fontStyle=1;fontSize=10;fontColor=#fef08a;" value="🛡️ Rol Personalizado IAM&#xa;jesus_aml@hotmail.com&#xa;sigrama_calidad_operador" vertex="1">
          <mxGeometry height="60" width="190" x="1390" y="18" as="geometry" />
        </mxCell>
        <mxCell id="badge_github" parent="header_banner" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1e293b;strokeColor=#a855f7;fontStyle=1;fontSize=10;fontColor=#e9d5ff;" value="🐙 GitHub CI/CD&#xa;Cloud Build Trigger" vertex="1">
          <mxGeometry height="60" width="140" x="1600" y="18" as="geometry" />
        </mxCell>

        <!-- 1. ZONA PLANTA INDUSTRIAL SIGRAMA -->
        <mxCell id="group_onprem" parent="1" style="swimlane;whiteSpace=wrap;html=1;fontSize=14;fontStyle=1;fillColor=#f8fafc;strokeColor=#64748b;strokeWidth=2;startSize=35;dashed=1;" value="🏭 PLANTA INDUSTRIAL SIGRAMA (ON-PREMISES LAN)" vertex="1">
          <mxGeometry height="1060" width="360" x="40" y="140" as="geometry" />
        </mxCell>
        <mxCell id="client_operator" parent="group_onprem" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e2e8f0;strokeColor=#475569;fontSize=11;fontStyle=1;shadow=1;" value="👷 INSPECTOR DE CALIDAD EN PISO&#xa;(Tablet / PC Industrial)&#xa;- Inspección Dimensional (Vernier/CMM)&#xa;- Captura de Cotas / Liberación de Lote" vertex="1">
          <mxGeometry height="70" width="300" x="30" y="60" as="geometry" />
        </mxCell>
        <mxCell id="client_engineer" parent="group_onprem" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e2e8f0;strokeColor=#475569;fontSize=11;fontStyle=1;shadow=1;" value="📐 INGENIERO DE DISEÑO (SolidWorks / CAD)&#xa;(Workstation Local)&#xa;- Exportación DXF, STEP, Planos PDF&#xa;- Sincronización Prototipos a la Nube" vertex="1">
          <mxGeometry height="70" width="300" x="30" y="160" as="geometry" />
        </mxCell>
        <mxCell id="client_admin" parent="group_onprem" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#e2e8f0;strokeColor=#475569;fontSize=11;fontStyle=1;shadow=1;" value="🛡️ ADMINISTRADOR DE CALIDAD&#xa;(Oficina Técnica)&#xa;- Auditoría de Planos y Matriz de Faltantes&#xa;- Exportación Excel para Ingeniería / Remisiones" vertex="1">
          <mxGeometry height="70" width="300" x="30" y="260" as="geometry" />
        </mxCell>
        <mxCell id="nas_storage" parent="group_onprem" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;fillColor=#fef08a;strokeColor=#ca8a04;fontStyle=1;fontSize=11;shadow=1;" value="📁 REPOSITORIO LOCAL DE PLANOS (SMB / NAS)&#xa;Z:\02 - INGENIERIA\BASE DE DATOS PRODUCTOS\&#xa;- Planos Originales Cliente, DXF CNC, Modelos SLD" vertex="1">
          <mxGeometry height="80" width="300" x="30" y="440" as="geometry" />
        </mxCell>
        <mxCell id="sync_script" parent="group_onprem" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fed7aa;strokeColor=#ea580c;fontStyle=1;fontSize=11;shadow=1;" value="⚡ SINCRONIZADOR DE PROTOTIPOS SIGRAMA&#xa;(Python 3.12 + Tkinter GUI / .bat Launcher)&#xa;- Escaneo incremental hash SHA-256&#xa;- Subida cifrada multi-hilo a Google Cloud" vertex="1">
          <mxGeometry height="75" width="300" x="30" y="560" as="geometry" />
        </mxCell>
        <mxCell id="edge_ai" parent="group_onprem" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dcfce7;strokeColor=#16a34a;fontStyle=1;fontSize=11;shadow=1;" value="🖐️ EDGE AI: CONTROL GESTUAL 3D&#xa;(Google MediaPipe Hands en Browser)&#xa;- Procesamiento local WebAssembly / WebGL&#xa;- 21 Articulaciones a 30-60 FPS (Sin uso de red)" vertex="1">
          <mxGeometry height="70" width="300" x="30" y="730" as="geometry" />
        </mxCell>
        <mxCell id="flow_nas_sync" edge="1" parent="group_onprem" source="nas_storage" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#ca8a04;strokeWidth=2;dashed=1;flowAnimation=1;fontSize=10;" target="sync_script" value="Lectura SMB (:445)">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>

        <!-- 2. ZONA PERÍMETRO Y BALANCEADOR DE CARGA -->
        <mxCell id="group_edge" parent="1" style="swimlane;whiteSpace=wrap;html=1;fontSize=14;fontStyle=1;fillColor=#eff6ff;strokeColor=#2563eb;strokeWidth=2;startSize=35;" value="🌐 PERÍMETRO DE RED &amp; BALANCEADOR GLOBAL" vertex="1">
          <mxGeometry height="1060" width="280" x="430" y="140" as="geometry" />
        </mxCell>
        <mxCell id="lb_box" parent="group_edge" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#bfdbfe;strokeColor=#1d4ed8;fontStyle=1;fontSize=11;shadow=1;" value="⚖️ CLOUD LOAD BALANCER (GFE)&#xa;- Regla: lb-sigrama-forwarding-rule&#xa;- IP Pública: 136.81.184.225 (Puerto 80)&#xa;- Target Proxy: lb-sigrama-http-proxy&#xa;- URL Map: lb-sigrama-calidad&#xa;- Serverless NEG: neg-sigrama-app" vertex="1">
          <mxGeometry height="110" width="240" x="20" y="60" as="geometry" />
        </mxCell>
        <mxCell id="waf_gfe" parent="group_edge" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dbeafe;strokeColor=#2563eb;fontStyle=1;fontSize=11;shadow=1;" value="🛡️ SEGURIDAD GOOGLE FRONT END&#xa;- Terminación HTTP/2 y WSS&#xa;- Protección DDoS Google Cloud Armor&#xa;- Enrutamiento Anycast Global" vertex="1">
          <mxGeometry height="75" width="240" x="20" y="195" as="geometry" />
        </mxCell>
        <mxCell id="signed_url_layer" parent="group_edge" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fbcfe8;strokeColor=#db2777;fontStyle=1;fontSize=11;shadow=1;" value="🔑 CANAL DE ACCESO DIRECTO GCS&#xa;(Signed URLs con HMAC SHA-256)&#xa;- Descarga directa de modelos STEP/DXF&#xa;- Sin sobrecargar la memoria del servidor&#xa;- Expiración efímera (15 min)" vertex="1">
          <mxGeometry height="90" width="240" x="20" y="550" as="geometry" />
        </mxCell>

        <!-- 3. ZONA GOOGLE CLOUD PLATFORM -->
        <mxCell id="group_gcp" parent="1" style="swimlane;whiteSpace=wrap;html=1;fontSize=14;fontStyle=1;fillColor=#fafafa;strokeColor=#dc2626;strokeWidth=2;startSize=35;" value="☁️ GOOGLE CLOUD PLATFORM (us-central1) — Proyecto: sigrama-cloud-calidad" vertex="1">
          <mxGeometry height="1060" width="1070" x="740" y="140" as="geometry" />
        </mxCell>

        <!-- SUB-CONTENEDOR VPC 2: vpc-sigrama-cloudrun -->
        <mxCell id="vpc2_box" parent="group_gcp" style="swimlane;whiteSpace=wrap;html=1;fontSize=12;fontStyle=1;fillColor=#fee2e2;strokeColor=#dc2626;strokeWidth=2;startSize=28;shadow=1;" value="🚀 VPC 2: 'vpc-sigrama-cloudrun' (Subred: 10.20.0.0/24 — us-central1)" vertex="1">
          <mxGeometry height="430" width="560" x="30" y="50" as="geometry" />
        </mxCell>
        <!-- Cloud Run 1 -->
        <mxCell id="cloud_run_1" parent="vpc2_box" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#dc2626;fontStyle=1;fontSize=11;" value="⚡ CLOUD RUN 1: 'sigrama-calidad-app' (Puerto :8080)&#xa;- Frontend Streamlit Reactivo (Hub 4.0, Inspección, Cotas Vernier)&#xa;- WebSocket bidireccional /_stcore/stream&#xa;- Identidad: streamlit-app-acceso@sigrama-cloud-calidad.iam.gserviceaccount.com" vertex="1">
          <mxGeometry height="75" width="510" x="25" y="40" as="geometry" />
        </mxCell>
        <!-- Cloud Run 2 -->
        <mxCell id="cloud_run_2" parent="vpc2_box" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#dc2626;fontStyle=1;fontSize=11;" value="🧊 CLOUD RUN 2: 'sigrama-calidad-prototipos' (Puerto :8080)&#xa;- Microservicio de Geometría CAD 3D y Conversión STEP/DXF&#xa;- Visor Autónomo de Prototipos de Ingeniería y Auditoría de Tolerancias&#xa;- Identidad: 500497385665-compute@developer.gserviceaccount.com" vertex="1">
          <mxGeometry height="75" width="510" x="25" y="130" as="geometry" />
        </mxCell>
        <!-- SQLite In-Container -->
        <mxCell id="sqlite_local" parent="vpc2_box" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;fillColor=#e0f2fe;strokeColor=#0284c7;fontStyle=1;fontSize=11;" value="🗄️ SQLITE3 MOTOR IN-CONTAINER (data/sigrama_calidad.db)&#xa;- PRAGMA journal_mode = WAL (Write-Ahead Logging de alto rendimiento)&#xa;- PRAGMA busy_timeout = 60000 | Concurrencia de lecturas simultáneas&#xa;- Sincronización bidireccional automática con Cloud Storage" vertex="1">
          <mxGeometry height="75" width="510" x="25" y="225" as="geometry" />
        </mxCell>
        <mxCell id="connector_vpc" parent="vpc2_box" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ede9fe;strokeColor=#7c3aed;fontStyle=1;fontSize=10;" value="🔌 Serverless VPC Access Connector / Direct VPC Egress (10.20.0.0/24)" vertex="1">
          <mxGeometry height="40" width="510" x="25" y="320" as="geometry" />
        </mxCell>

        <!-- SUB-CONTENEDOR VPC 1: vpc-sigrama-vm -->
        <mxCell id="vpc1_box" parent="group_gcp" style="swimlane;whiteSpace=wrap;html=1;fontSize=12;fontStyle=1;fillColor=#e0f2fe;strokeColor=#0284c7;strokeWidth=2;startSize=28;shadow=1;" value="🖥️ VPC 1: 'vpc-sigrama-vm' (Subred: 10.10.0.0/24 — us-central1)" vertex="1">
          <mxGeometry height="430" width="430" x="610" y="50" as="geometry" />
        </mxCell>
        <mxCell id="vm_instance" parent="vpc1_box" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#0284c7;fontStyle=1;fontSize=11;" value="💻 MÁQUINA VIRTUAL COMPUTE ENGINE&#xa;Nombre: 'vm-sigrama-backend' (e2-medium)&#xa;- IP Privada: 10.10.0.5 (Sin IP externa obligatoria)&#xa;- Servidor de Base de Datos Interna / Archivo Maestro&#xa;- Regla Firewall: allow-internal (SSH :22, SMB :445, ICMP)&#xa;- Resguardo de planos de ingeniería de respaldo" vertex="1">
          <mxGeometry height="110" width="380" x="25" y="50" as="geometry" />
        </mxCell>
        <!-- Peering Box en VPC 1 -->
        <mxCell id="peering_node" parent="vpc1_box" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#cffafe;strokeColor=#0891b2;fontStyle=1;fontSize=11;" value="🔗 VPC NETWORK PEERING (SDN Andromeda)&#xa;- peer-vm-to-cloudrun ⇄ peer-cloudrun-to-vm&#xa;- Estado: ACTIVE (Connected)&#xa;- Rutas automáticas entre 10.10.0.0/24 y 10.20.0.0/24&#xa;- Tráfico 100% privado interno (Cero salida a Internet)" vertex="1">
          <mxGeometry height="100" width="380" x="25" y="190" as="geometry" />
        </mxCell>

        <!-- SUB-CONTENEDOR CLOUD STORAGE -->
        <mxCell id="gcs_bucket" parent="group_gcp" style="swimlane;whiteSpace=wrap;html=1;fontSize=12;fontStyle=1;fillColor=#fef3c7;strokeColor=#d97706;strokeWidth=2;startSize=28;shadow=1;" value="🪣 CLOUD STORAGE BUCKET: gs://sigrama-planos-calidad-2026 (Cifrado AES-256)" vertex="1">
          <mxGeometry height="220" width="560" x="30" y="510" as="geometry" />
        </mxCell>
        <mxCell id="gcs_db_backup" parent="gcs_bucket" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#d97706;fontStyle=1;fontSize=10;" value="💾 system/sigrama_calidad.db&#xa;(Persistencia de Estado / Transacciones)" vertex="1">
          <mxGeometry height="60" width="240" x="20" y="45" as="geometry" />
        </mxCell>
        <mxCell id="gcs_models" parent="gcs_bucket" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#d97706;fontStyle=1;fontSize=10;" value="🧊 Auditadas/ &amp; Sin_Auditar/&#xa;(STEP 3D, DXF, SLDPRT, SLDDRW)" vertex="1">
          <mxGeometry height="60" width="250" x="280" y="45" as="geometry" />
        </mxCell>
        <mxCell id="gcs_blueprints" parent="gcs_bucket" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#d97706;fontStyle=1;fontSize=10;" value="📄 Planos_PDF/ y Tolerancias Excel" vertex="1">
          <mxGeometry height="50" width="510" x="20" y="125" as="geometry" />
        </mxCell>

        <!-- SUB-CONTENEDOR IAM: GESTIÓN DE ROLES Y CUENTAS -->
        <mxCell id="iam_box" parent="group_gcp" style="swimlane;whiteSpace=wrap;html=1;fontSize=12;fontStyle=1;fillColor=#fef9c3;strokeColor=#ca8a04;strokeWidth=2;startSize=28;shadow=1;" value="🛡️ IAM &amp; SEGURIDAD DE IDENTIDAD: ROLES PERSONALIZADOS (CUSTOM ROLES)" vertex="1">
          <mxGeometry height="220" width="430" x="610" y="510" as="geometry" />
        </mxCell>
        <mxCell id="custom_role_card" parent="iam_box" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fef08a;strokeColor=#ca8a04;fontStyle=1;fontSize=10;" value="⭐ ROL PERSONALIZADO: sigrama_calidad_operador&#xa;Usuario Asignado: user:jesus_aml@hotmail.com&#xa;- run.services.get, run.services.list&#xa;- storage.buckets.get, storage.objects.get, storage.objects.create&#xa;- compute.networks.get, compute.instances.get&#xa;* Cumple Principio de Menor Privilegio (PoLP)" vertex="1">
          <mxGeometry height="95" width="380" x="25" y="40" as="geometry" />
        </mxCell>
        <mxCell id="sa_comparison_card" parent="iam_box" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#ca8a04;fontSize=9;" value="👤 Cuentas de Usuario: jesus_aml@hotmail.com | jesus.alberto...@gmail.com&#xa;🤖 Cuentas de Servicio: streamlit-app-acceso@... (Storage Admin)&#xa;  500497385665-compute@developer.gserviceaccount.com (Run Admin)" vertex="1">
          <mxGeometry height="50" width="380" x="25" y="145" as="geometry" />
        </mxCell>

        <!-- CI/CD GitHub & Cloud Build -->
        <mxCell id="cicd_box" parent="group_gcp" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f3e8ff;strokeColor=#9333ea;fontStyle=1;fontSize=11;shadow=1;" value="🔄 CI/CD PIPELINE: GITHUB ➔ GOOGLE CLOUD BUILD ➔ ARTIFACT REGISTRY&#xa;- Trigger automático en push a &#39;main&#39; con despliegue Zero-Downtime a Cloud Run 1 y Cloud Run 2" vertex="1">
          <mxGeometry height="60" width="1010" x="30" y="750" as="geometry" />
        </mxCell>

        <!-- CONECTORES CON ANIMACIÓN DE FLUJO (flowAnimation=1) -->
        <mxCell id="flow_clients_lb" edge="1" parent="1" source="client_engineer" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#2563eb;strokeWidth=3;fontSize=11;fontStyle=1;dashed=1;flowAnimation=1;" target="lb_box" value="HTTP :80 (IP: 136.81.184.225) [Tráfico UI WebSockets]">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="flow_lb_cr1" edge="1" parent="1" source="lb_box" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#16a34a;strokeWidth=3;fontSize=10;fontStyle=1;dashed=1;flowAnimation=1;" target="cloud_run_1" value="Serverless NEG :8080 (Cloud Run 1: App)">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="flow_lb_cr2" edge="1" parent="1" source="lb_box" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#16a34a;strokeWidth=2;fontSize=10;dashed=1;flowAnimation=1;" target="cloud_run_2" value="Ruta /prototipos (Cloud Run 2)">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="flow_peering" edge="1" parent="1" source="connector_vpc" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#0891b2;strokeWidth=3;dashed=1;flowAnimation=1;fontSize=10;fontStyle=1;" target="peering_node" value="VPC Peering (10.20.0.0/24 ⇄ 10.10.0.0/24)">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="flow_sync_gcs" edge="1" parent="1" source="sync_script" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#ea580c;strokeWidth=3;dashed=1;flowAnimation=1;fontSize=10;fontStyle=1;" target="gcs_bucket" value="GCS REST API :443 (Upload Hash SHA-256)">
          <mxGeometry relative="1" as="geometry">
            <Array as="points">
              <mxPoint x="400" y="730" />
              <mxPoint x="400" y="700" />
              <mxPoint x="720" y="700" />
            </Array>
          </mxGeometry>
        </mxCell>
        <mxCell id="flow_db_backup" edge="1" parent="1" source="sqlite_local" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#d97706;strokeWidth=3;dashed=1;flowAnimation=1;fontSize=10;fontStyle=1;" target="gcs_db_backup" value="Sync WAL DB">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="flow_signed_url" edge="1" parent="1" source="gcs_bucket" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#db2777;strokeWidth=3;dashed=1;flowAnimation=1;fontSize=10;fontStyle=1;" target="signed_url_layer" value="Signed URLs GET :443">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
        <mxCell id="flow_signed_to_client" edge="1" parent="1" source="signed_url_layer" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#db2777;strokeWidth=3;dashed=1;flowAnimation=1;fontSize=10;fontStyle=1;" target="edge_ai" value="STEP 3D Streaming al Navegador">
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
