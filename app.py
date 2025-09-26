import subprocess
import time
import os
import sys
import signal 

# ----------------------------------------------------------------------
# PASO 1: CONFIGURACIÓN
# ----------------------------------------------------------------------
YOUTUBE_STREAM_KEY = "clave" 
YOUTUBE_RTMP_URL = f"rtmp://a.rtmp.youtube.com/live2/{YOUTUBE_STREAM_KEY}"

ffmpeg_process = None

# ----------------------------------------------------------------------
# FUNCIÓN DINÁMICA: Carga los videos de la carpeta
# ----------------------------------------------------------------------
def obtener_archivos_video():
    """Busca archivos .mp4 en el directorio actual y los devuelve ordenados."""
    todos_los_archivos = os.listdir('.')
    lista_videos = [f for f in todos_los_archivos if f.lower().endswith('.mp4')]
    lista_videos.sort() 
    return lista_videos

# ----------------------------------------------------------------------
# FUNCIÓN DE LIMPIEZA
# ----------------------------------------------------------------------
def detener_ffmpeg(sig, frame):
    """Maneja la señal Ctrl+C (SIGINT) para detener FFmpeg y salir."""
    global ffmpeg_process
    print("\n\n🚨 Recibida señal de interrupción (Ctrl+C). Deteniendo la transmisión...")
    if ffmpeg_process:
        ffmpeg_process.terminate()
        try:
            ffmpeg_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            ffmpeg_process.kill()
            print("FFmpeg fue forzado a detenerse.")
    
    print("👋 Script finalizado. ¡Adiós!")
    sys.exit(0)

# ----------------------------------------------------------------------
# PROGRAMA PRINCIPAL
# ----------------------------------------------------------------------

# Asignar la función al evento Ctrl+C
signal.signal(signal.SIGINT, detener_ffmpeg)

print("Iniciando el script de transmisión en bucle dinámico.")
print("Presiona Ctrl+C para detener.")

while True:
    
    # Recarga la lista de videos dinámicamente al inicio de cada ciclo
    video_files = obtener_archivos_video()
    
    if not video_files:
        print("\n⚠️ Advertencia: No se encontraron archivos .mp4 en la carpeta. Volviendo a buscar en 30 segundos.")
        time.sleep(30)
        continue

    for video_file in video_files:
        
        if not os.path.exists(video_file):
            print(f"\n⚠️ Advertencia: Archivo no encontrado: {video_file}. Saltando.")
            continue

        print(f"\n▶️ Reproduciendo video: {video_file}")
        
        # -----------------------------------------------------------
        # COMANDO FFmpeg: AJUSTADO PARA MÍNIMO USO DE RAM Y CPU/GPU
        # -----------------------------------------------------------
        ffmpeg_command = [
            'ffmpeg',
            '-re',
            '-i', video_file,
            
            # Limpieza y Metadatos
            '-loglevel', 'error', 
            '-metadata', f'title={video_file}', 
            
            # Codificación por hardware (GPU)
            '-c:v', 'h264_nvenc', 
            '-preset', 'p5', 
            '-tune', 'hq', 
            
            # Control de RAM/Bitrate
            '-maxrate', '3000k', 
            '-bufsize', '3200k', 
            '-pix_fmt', 'yuv420p',
            '-g', '50',
            
            # Configuraciones de audio 
            '-c:a', 'aac',
            '-b:a', '128k',
            '-ar', '44100',
            
            '-f', 'flv',
            YOUTUBE_RTMP_URL
        ]

        try:
            # Ejecución limpia (no necesitamos los pipes para control de teclado)
            ffmpeg_process = subprocess.Popen(ffmpeg_command)
            
            # El script espera aquí hasta que el video termine o se presione Ctrl+C
            ffmpeg_process.wait()
            
            if ffmpeg_process.returncode == 0:
                print(f"✅ Finalizado: {video_file}")
            elif ffmpeg_process.returncode != -signal.SIGINT:
                # Si terminó con un error y no fue por interrupción de usuario
                print(f"\n🛑 La transmisión de {video_file} finalizó con un ERROR (código {ffmpeg_process.returncode}).")

        except FileNotFoundError:
            print("\n🚨 Error: FFmpeg no encontrado. Asegúrate de que esté instalado.")
            sys.exit(1)
        
        ffmpeg_process = None

    print("\n--- Ciclo completado. Recargando la lista de videos y reiniciando en 5 segundos... ---")
    time.sleep(5)