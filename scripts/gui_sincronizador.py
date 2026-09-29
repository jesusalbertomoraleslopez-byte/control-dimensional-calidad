# -*- coding: utf-8 -*-
"""
INDUSTRIA SIGRAMA S.A. DE C.V.
Aplicación Gráfica de Sincronización Automática de Prototipos a Google Cloud
Control Dimensional y Calidad Industrial 4.0
"""

import os
import sys
import time
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# Asegurar encoding UTF-8 en Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

NETWORK_PATH = r"Z:\02 - INGENIERIA\BASE DE DATOS PRODUCTOS"
CLOUD_RUN_URL = "https://sigrama-calidad-prototipos-500497385665.us-central1.run.app"

class SigramaSyncApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SIGRAMA METALES — Sincronizador de Prototipos a Google Cloud")
        self.root.geometry("740x620")
        self.root.minsize(700, 560)
        self.root.configure(bg="#0F172A")

        self.is_running = False

        self._build_ui()
        self._refresh_status()

    def _build_ui(self):
        # ── CABECERA CORPORATIVA ──
        header_frame = tk.Frame(self.root, bg="#1E293B", height=80)
        header_frame.pack(fill="x", side="top")

        # Barra roja de acento
        red_bar = tk.Frame(header_frame, bg="#EC2024", width=6)
        red_bar.pack(side="left", fill="y")

        title_container = tk.Frame(header_frame, bg="#1E293B", padx=16, pady=12)
        title_container.pack(side="left", fill="both", expand=True)

        lbl_company = tk.Label(
            title_container,
            text="INDUSTRIA SIGRAMA S.A. DE C.V.",
            font=("Montserrat", 13, "bold"),
            fg="#EC2024",
            bg="#1E293B"
        )
        lbl_company.pack(anchor="w")

        lbl_subtitle = tk.Label(
            title_container,
            text="Sincronizador Automático de Carpetas de Prototipos a Google Cloud Storage",
            font=("Segoe UI", 10),
            fg="#94A3B8",
            bg="#1E293B"
        )
        lbl_subtitle.pack(anchor="w")

        # ── TARJETA DE ESTADO Y RUTAS ──
        info_card = tk.LabelFrame(
            self.root,
            text="  Estado de Almacenamiento y Conexión  ",
            font=("Segoe UI", 9, "bold"),
            fg="#F8FAFC",
            bg="#1E293B",
            padx=14,
            pady=10,
            relief="groove"
        )
        info_card.pack(fill="x", padx=18, pady=12)

        # Fila 1: Ruta Red
        row1 = tk.Frame(info_card, bg="#1E293B")
        row1.pack(fill="x", pady=2)
        tk.Label(row1, text="📁 Ruta de Red:", font=("Segoe UI", 9, "bold"), fg="#94A3B8", bg="#1E293B", width=18, anchor="w").pack(side="left")
        self.lbl_network_path = tk.Label(row1, text=NETWORK_PATH, font=("Consolas", 9), fg="#38BDF8", bg="#1E293B")
        self.lbl_network_path.pack(side="left")

        # Fila 2: Bucket
        row2 = tk.Frame(info_card, bg="#1E293B")
        row2.pack(fill="x", pady=2)
        tk.Label(row2, text="☁️ Bucket Destino:", font=("Segoe UI", 9, "bold"), fg="#94A3B8", bg="#1E293B", width=18, anchor="w").pack(side="left")
        tk.Label(row2, text="gs://sigrama-planos-calidad-2026/Sin_Auditar/", font=("Consolas", 9), fg="#34D399", bg="#1E293B").pack(side="left")

        # Fila 3: Conteo en vivo
        row3 = tk.Frame(info_card, bg="#1E293B")
        row3.pack(fill="x", pady=4)
        tk.Label(row3, text="📊 Detección:", font=("Segoe UI", 9, "bold"), fg="#94A3B8", bg="#1E293B", width=18, anchor="w").pack(side="left")
        self.lbl_counter = tk.Label(row3, text="Consultando carpetas...", font=("Segoe UI", 9, "bold"), fg="#FCD34D", bg="#1E293B")
        self.lbl_counter.pack(side="left")

        btn_refresh = tk.Button(
            row3,
            text="🔄 Refrescar",
            font=("Segoe UI", 8),
            bg="#334155",
            fg="#FFFFFF",
            relief="flat",
            command=self._refresh_status,
            padx=8,
            pady=1
        )
        btn_refresh.pack(side="right")

        # ── BOTONES DE ACCIÓN PRINCIPALES ──
        actions_frame = tk.Frame(self.root, bg="#0F172A", padx=18, pady=4)
        actions_frame.pack(fill="x")

        self.btn_sync = tk.Button(
            actions_frame,
            text="⚡ SUBIR PROTOTIPOS A GOOGLE CLOUD",
            font=("Montserrat", 11, "bold"),
            bg="#EC2024",
            fg="#FFFFFF",
            activebackground="#C62828",
            activeforeground="#FFFFFF",
            relief="flat",
            padx=20,
            pady=12,
            cursor="hand2",
            command=self._start_sync_thread
        )
        self.btn_sync.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn_open_web = tk.Button(
            actions_frame,
            text="🌐 Abrir App en la Nube ↗",
            font=("Segoe UI", 10, "bold"),
            bg="#2563EB",
            fg="#FFFFFF",
            activebackground="#1D4ED8",
            activeforeground="#FFFFFF",
            relief="flat",
            padx=16,
            pady=12,
            cursor="hand2",
            command=lambda: webbrowser.open(CLOUD_RUN_URL)
        )
        btn_open_web.pack(side="right")

        # ── BARRA DE PROGRESO ──
        prog_frame = tk.Frame(self.root, bg="#0F172A", padx=18, pady=6)
        prog_frame.pack(fill="x")

        self.lbl_progress_status = tk.Label(
            prog_frame,
            text="Listo para sincronizar.",
            font=("Segoe UI", 9),
            fg="#94A3B8",
            bg="#0F172A"
        )
        self.lbl_progress_status.pack(anchor="w", pady=(0, 4))

        self.progress_bar = ttk.Progressbar(prog_frame, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill="x")

        # ── TERMINAL DE EVENTOS / LOG ──
        log_frame = tk.LabelFrame(
            self.root,
            text="  Consola de Actividad y Transferencia  ",
            font=("Segoe UI", 9, "bold"),
            fg="#94A3B8",
            bg="#0B132B",
            padx=6,
            pady=6,
            relief="groove"
        )
        log_frame.pack(fill="both", expand=True, padx=18, pady=(4, 16))

        self.txt_log = scrolledtext.ScrolledText(
            log_frame,
            bg="#050C1A",
            fg="#38BDF8",
            insertbackground="#FFFFFF",
            font=("Consolas", 9),
            relief="flat",
            wrap="word"
        )
        self.txt_log.pack(fill="both", expand=True)

    def _log(self, msg, color=None):
        self.txt_log.insert(tk.END, msg + "\n")
        self.txt_log.see(tk.END)
        self.root.update_idletasks()

    def _refresh_status(self):
        def _task():
            if not os.path.exists(NETWORK_PATH):
                self.lbl_counter.config(text="❌ Ruta de red Z:\\ inaccesible", fg="#EF4444")
                return

            all_dirs = [d for d in os.listdir(NETWORK_PATH) if os.path.isdir(os.path.join(NETWORK_PATH, d)) and d.upper().startswith("ING")]
            
            try:
                from src.database import get_connection
                conn = get_connection()
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM piezas")
                total_db = c.fetchone()[0]
                c.execute("SELECT consecutivo_ing FROM piezas")
                existing_ings = {r[0] for r in c.fetchall() if r[0]}
                conn.close()

                new_count = sum(1 for d in all_dirs if d.split("-")[0].strip() not in existing_ings)

                status_txt = f"{len(all_dirs)} carpetas en Z:\\ | {total_db} piezas en Nube | {new_count} carpetas NUEVAS"
                color = "#34D399" if new_count == 0 else "#F59E0B"
                self.lbl_counter.config(text=status_txt, fg=color)
                self._log(f"[INFO] Estado actualizado: {len(all_dirs)} en red Z:\\, {new_count} pendientes de subir.")
            except Exception as e:
                self.lbl_counter.config(text=f"Carpetas en red: {len(all_dirs)} (Error DB: {e})", fg="#FCD34D")

        threading.Thread(target=_task, daemon=True).start()

    def _start_sync_thread(self):
        if self.is_running:
            return

        if not os.path.exists(NETWORK_PATH):
            messagebox.showerror("Error de Red", f"No se pudo acceder a la ruta:\n{NETWORK_PATH}\n\nVerifique la conexión al servidor NAS.")
            return

        self.is_running = True
        self.btn_sync.config(state="disabled", bg="#64748B", text="⏳ SINCRONIZANDO CON LA NUBE...")
        self.progress_bar["value"] = 0
        self.lbl_progress_status.config(text="Iniciando transferencia a Google Cloud Storage...", fg="#38BDF8")

        thread = threading.Thread(target=self._run_sync, daemon=True)
        thread.start()

    def _run_sync(self):
        try:
            self._log("=" * 65)
            self._log(f"🚀 INICIANDO SINCRONIZACIÓN DE PROTOTIPOS: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            self._log(f"Origen: {NETWORK_PATH}")
            self._log("Destino: gs://sigrama-planos-calidad-2026/Sin_Auditar/")
            self._log("=" * 65)

            from scripts.inyectar_red_a_bucket import inyectar_carpetas_red
            from scripts.subir_db_a_gcs import DB_PATH, GCS_DB_BLOB
            from src.services.gcs_storage import get_bucket, DEFAULT_BUCKET_NAME

            self.lbl_progress_status.config(text="Transfiriendo archivos de prototipos hacia el Bucket...", fg="#38BDF8")
            self.progress_bar["value"] = 25

            # 1. Inyectar carpetas
            inyectar_carpetas_red()

            self.progress_bar["value"] = 80
            self.lbl_progress_status.config(text="Persistiendo base de datos actualizada en Google Cloud...", fg="#34D399")
            self._log("☁️ Subiendo base de datos actualizada hacia Google Cloud Storage...")

            # 2. Persistir base de datos
            bucket = get_bucket()
            if bucket and os.path.exists(DB_PATH):
                blob = bucket.blob(GCS_DB_BLOB)
                blob.upload_from_filename(DB_PATH, content_type="application/octet-stream")
                self._log(f"✅ Base de datos sincronizada: gs://{DEFAULT_BUCKET_NAME}/{GCS_DB_BLOB}")

            self.progress_bar["value"] = 100
            self.lbl_progress_status.config(text="¡Sincronización completada con éxito!", fg="#34D399")
            self._log("🎉 ¡PROCESO FINALIZADO CON ÉXITO!")
            self._log("Todas las piezas nuevas ya están disponibles en la App de Google Cloud.")
            self._log("=" * 65)

            self._refresh_status()

            messagebox.showinfo(
                "Sincronización Exitosa",
                "¡Todas las carpetas de prototipos han sido subidas a Google Cloud Storage y registradas en el sistema!\n\n"
                "Ya están disponibles en la Aplicación de Calidad."
            )

        except Exception as e:
            self._log(f"❌ ERROR DURANTE LA SINCRONIZACIÓN: {str(e)}")
            self.lbl_progress_status.config(text=f"Error: {str(e)}", fg="#EF4444")
            messagebox.showerror("Error", f"Ocurrió un error al sincronizar:\n{str(e)}")
        finally:
            self.is_running = False
            self.btn_sync.config(state="normal", bg="#EC2024", text="⚡ SUBIR PROTOTIPOS A GOOGLE CLOUD")

def main():
    root = tk.Tk()
    app = SigramaSyncApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
