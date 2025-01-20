from flask import Flask, request, jsonify
import cv2
import os
import base64
import uuid
import shutil


app = Flask(__name__)
 
UPLOAD_FOLDER = "uploads"
FRAMES_FOLDER = "frames"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FRAMES_FOLDER, exist_ok=True)

user_sessions = {}



def get_video_details(video_path: str):
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"El archivo {video_path} no existe.")
    
    video_capture = cv2.VideoCapture(video_path)

    if not video_capture.isOpened():
        print("Error: No se pudo abrir el archivo de video.")
        exit()
    info = {
        "Ancho (pixeles)": video_capture.get(cv2.CAP_PROP_FRAME_WIDTH),
        "Alto (pixeles)": video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT),
        "Cantidad de cuadros (frames)": video_capture.get(cv2.CAP_PROP_FRAME_COUNT),
        "Fotogramas por segundo (FPS)": round(video_capture.get(cv2.CAP_PROP_FPS), 2),
        "Tiempo total (segundos)": round(video_capture.get(cv2.CAP_PROP_FRAME_COUNT) / video_capture.get(cv2.CAP_PROP_FPS),2),
        "Codec (formato)": round(video_capture.get(cv2.CAP_PROP_FOURCC), 2),
    }
    return info



@app.route("/upload", methods=["POST"])
def upload_video():
    """
    Subir un video, extraer frames y asociarlos a un usuario.
    """
    if "video" not in request.files:
        return jsonify({"error": "No se envió ningún archivo"}), 400

    # Validar parámetros de entrada
    start_time = float(request.form.get("start_time", 0))  # Por defecto, inicio en 0 segundos
    end_time = float(request.form.get("end_time", 0))  # Por defecto, procesar todo el video
    frame_count = int(request.form.get("frame_count", 0))  # Por defecto, extraer todos los frames

    if end_time <= start_time:
        return jsonify({"error": "El tiempo final debe ser mayor que el tiempo inicial"}), 400
    if frame_count <= 0:
        return jsonify({"error": "El número de frames debe ser mayor a 0"}), 400

    # Generar un identificador único para la sesión del usuario
    session_id = str(uuid.uuid4())

    # Crear directorios para almacenar los archivos de la sesión
    session_upload_folder = os.path.join(UPLOAD_FOLDER, session_id)
    session_frames_folder = os.path.join(FRAMES_FOLDER, session_id)
    os.makedirs(session_upload_folder, exist_ok=True)
    os.makedirs(session_frames_folder, exist_ok=True)

    # Guardar el archivo de video con un nombre único
    video = request.files["video"]
    file_extension = os.path.splitext(video.filename)[1]
    video_path = os.path.join(session_upload_folder, f"uploaded_video{file_extension}")
    video.save(video_path)

    # Procesar el video y extraer frames
    extract_frames(video_path, session_frames_folder, start_time, end_time, frame_count)

    # Obtener información del video
    info_video = get_video_details(video_path)

    # Limpiar el archivo de video subido
    os.remove(video_path)

    # Guardar la sesión en la estructura global
    user_sessions[session_id] = session_frames_folder
    print(f"session-id: {session_id}")
    return jsonify({
        "message": "Video procesado y frames generados con éxito.",
        "session_id": session_id,
        "video_details": info_video
    })



@app.route("/frames/<session_id>", methods=["GET"])
def get_frames(session_id):
    """
    Retorna los frames asociados a una sesión en Base64 y los elimina.
    """
    if session_id not in user_sessions:
        return jsonify({"error": "SESSIONT NOT FOUND."}), 404

    session_frames_folder = user_sessions[session_id]
    frames_b64 = {}

    # Codificar los frames en Base64
    for frame_filename in os.listdir(session_frames_folder):
        frame_path = os.path.join(session_frames_folder, frame_filename)
        with open(frame_path, "rb") as frame_file:
            frames_b64[frame_filename] = base64.b64encode(frame_file.read()).decode("utf-8")

    # Eliminar los frames y limpiar la sesión
    shutil.rmtree(session_frames_folder)
    del user_sessions[session_id]

    return jsonify({"frames": frames_b64})


def extract_frames(video_path, output_folder, start_time, end_time, frame_count):
    """
    Extraer un número específico de frames en un rango de tiempo dado.
    """
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)  # Obtener los frames por segundo del video
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps  # Duración total del video en segundos

    if end_time > duration:
        end_time = duration  # Ajustar el tiempo final si es mayor a la duración del video

    # Calcular los índices de los frames a extraer
    start_frame = int(start_time * fps)
    end_frame = int(end_time * fps)
    step = max((end_frame - start_frame) // frame_count, 1)  # Espaciado entre frames

    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)  # Comenzar desde el frame inicial
    extracted = 0

    for frame_idx in range(start_frame, end_frame + 1, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            break

        # Generar un nombre único para el frame
        frame_uuid = uuid.uuid4().hex
        frame_filename = f"frame_{frame_uuid}.jpg"
        frame_path = os.path.join(output_folder, frame_filename)

        # Guardar el frame como archivo de imagen
        cv2.imwrite(frame_path, frame)
        extracted += 1

        # Detener si alcanzamos el número de frames deseados
        if extracted >= frame_count:
            break

    cap.release()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)

