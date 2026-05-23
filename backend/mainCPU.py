import cv2
import time
from collections import deque

from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort

# =========================
# Main config
# =========================
VIDEO_PATH = "videos/escalator.mp4"

# Target FPS for display/processing
TARGET_FPS = 10

# Display scale to fit screen (no effect on detection)
DISPLAY_SCALE = 0.6

# Default vertical line positions (ratios of frame width)
LINE1_X_RATIO = 0.35  # Linha 1 (Ciano) - esquerda
LINE2_X_RATIO = 0.50  # Linha 2 (Verde) - centro
LINE3_X_RATIO = 0.65  # Linha 3 (Laranja) - direita

# Line heights (ratios of frame height)
LINE12_Y_MIN_RATIO = 0.05
LINE12_Y_MAX_RATIO = 0.99
LINE3_Y_MIN_RATIO = 0.05
LINE3_Y_MAX_RATIO = 0.99

LINE_COLOR_1 = (255, 200, 0)  # cyan-like for Line 1
LINE_COLOR_2 = (0, 255, 0)  # green for Line 2
LINE_COLOR_3 = (0, 165, 255)  # orange for Line 3
LINE_COLOR_FLASH = (0, 255, 0)
FLASH_FRAMES = 8

# YOLO - OTIMIZADO PARA CPU (OpenVINO)
YOLO_MODEL_PATH = "yolov5nu_openvino_model"
PERSON_CLASS_ID = 0
CONF_THRESHOLD = 0.25
IMG_SIZE = 320  # Tamanho reduzido para inferência mais rápida na CPU

# Performance
DETECT_EVERY_N = 1  # 1 = Roda o YOLO em todos os frames (Sem pulo)

# DeepSORT - Configurações padrão para alta precisão
MAX_AGE = 30
N_INIT = 3
NN_BUDGET = 50

# Lock control to avoid double counting at Line 2
LOCK_FRAMES = 30

# Optional debug
DRAW_YOLO_DEBUG = False

# Drag behavior
DRAG_TOLERANCE_PX = 12
L3_MIN_HEIGHT_PX = 40


# =========================
# Utils
# =========================
def get_line_side(pt, line_start, line_end):
    """
    Cross-product sign to check which side of the line the point is on.
    >0 one side, <0 other side, 0 on the line.
    """
    x, y = pt
    x1, y1 = line_start
    x2, y2 = line_end
    return (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)


def compute_centroid(x1, y1, x2, y2):
    # O X continua no meio exato dos ombros
    cx = int((x1 + x2) / 2)

    # O Y vai para 35% de distância a partir do topo (y1)
    # Isso levanta o ponto do cinto para a altura do peito/barriga
    altura = y2 - y1
    cy = int(y1 + (altura * 0.37))

    return cx, cy


def clamp(val, min_v, max_v):
    return max(min_v, min(val, max_v))


def near_line(y, line_y, tol):
    return abs(y - line_y) <= tol


# =========================
# Main pipeline
# =========================
def main():
    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print(f"Erro ao abrir o video: {VIDEO_PATH}")
        return

    # Carrega o modelo otimizado (pasta OpenVINO)
    model = YOLO(YOLO_MODEL_PATH)

    tracker = DeepSort(
        max_age=MAX_AGE,
        n_init=N_INIT,
        nn_budget=NN_BUDGET
    )

    ret, frame = cap.read()
    if not ret:
        print("Erro ao ler o primeiro frame.")
        return

    h, w = frame.shape[:2]

    # Default line positions (ratios)
    line1_x = int(w * LINE1_X_RATIO)
    line2_x = int(w * LINE2_X_RATIO)
    line3_x = int(w * LINE3_X_RATIO)

    line12_y1 = int(h * LINE12_Y_MIN_RATIO)
    line12_y2 = int(h * LINE12_Y_MAX_RATIO)
    line3_y1 = int(h * LINE3_Y_MIN_RATIO)
    line3_y2 = int(h * LINE3_Y_MAX_RATIO)

    lines = [
        ((line1_x, line12_y1), (line1_x, line12_y2)),
        ((line2_x, line12_y1), (line2_x, line12_y2)),
        ((line3_x, line3_y1), (line3_x, line3_y2)),
    ]

    # Setup window
    window_name = "Fluxo Humano - PoC"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    display_w = int(w * DISPLAY_SCALE)
    display_h = int(h * DISPLAY_SCALE)
    cv2.resizeWindow(window_name, display_w, display_h)

    # Drag state
    dragging_line = None
    dragging_mode = None
    drag_start = None

    def to_frame_coords(x, y):
        sx = w / display_w
        sy = h / display_h
        return int(x * sx), int(y * sy)

    def on_mouse(event, x, y, flags, param):
        nonlocal dragging_line, dragging_mode, drag_start
        nonlocal line1_x, line2_x, line3_x, line3_y1, line3_y2

        fx, fy = to_frame_coords(x, y)

        if event == cv2.EVENT_LBUTTONDOWN:
            candidates = [
                (0, line1_x),
                (1, line2_x),
                (2, line3_x),
            ]
            for idx, lx in candidates:
                if near_line(fx, lx, DRAG_TOLERANCE_PX):
                    dragging_line = idx
                    if idx == 2 and (flags & cv2.EVENT_FLAG_SHIFTKEY):
                        dragging_mode = "height"
                        drag_start = fy
                    else:
                        dragging_mode = "x"
                        drag_start = fx
                    return

        if event == cv2.EVENT_MOUSEMOVE and dragging_line is not None:
            if dragging_mode == "x":
                if dragging_line == 0:
                    line1_x = clamp(fx, 0, w - 1)
                elif dragging_line == 1:
                    line2_x = clamp(fx, 0, w - 1)
                elif dragging_line == 2:
                    line3_x = clamp(fx, 0, w - 1)
            elif dragging_mode == "height" and dragging_line == 2:
                center = (line3_y1 + line3_y2) // 2
                half = abs(fy - center)
                half = max(half, L3_MIN_HEIGHT_PX // 2)
                line3_y1 = clamp(center - half, 0, h - 1)
                line3_y2 = clamp(center + half, 0, h - 1)

        if event == cv2.EVENT_LBUTTONUP:
            dragging_line = None
            dragging_mode = None
            drag_start = None

    cv2.setMouseCallback(window_name, on_mouse)

    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    if video_fps is None or video_fps <= 0:
        video_fps = 30.0
    frame_step = max(1, int(round(video_fps / TARGET_FPS)))

    entradas = 0
    saidas = 0

    prev_line_sides = {}
    last_intent = {}
    count_lock = {}

    flash_counters = [0, 0, 0]

    prev_time = time.time()
    fps_window = deque(maxlen=30)

    frame_id = 0
    start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_id += 1

        if frame_step > 1 and (frame_id % frame_step != 0):
            continue

        lines = [
            ((line1_x, line12_y1), (line1_x, line12_y2)),
            ((line2_x, line12_y1), (line2_x, line12_y2)),
            ((line3_x, line3_y1), (line3_x, line3_y2)),
        ]

        now = time.time()
        fps_window.append(1.0 / max(now - prev_time, 1e-6))
        prev_time = now
        fps = sum(fps_window) / len(fps_window)

        run_yolo = (frame_id % DETECT_EVERY_N == 0)
        detections = []

        if run_yolo:
            results = model.predict(
                frame,
                verbose=False,
                conf=CONF_THRESHOLD,
                imgsz=IMG_SIZE,
                classes=[PERSON_CLASS_ID]
            )

            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0])
                    w_box = x2 - x1
                    h_box = y2 - y1
                    detections.append(([x1, y1, w_box, h_box], conf, "person"))

                    if DRAW_YOLO_DEBUG:
                        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 255), 2)
                        cv2.putText(frame, f"YOLO {conf:.2f}", (int(x1), int(y1) - 6),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)

        tracks = tracker.update_tracks(detections, frame=frame)

        for track in tracks:
            if not track.is_confirmed():
                continue

            track_id = track.track_id

            ltrb = track.to_ltrb()
            if ltrb is None:
                continue

            x1, y1, x2, y2 = map(int, ltrb)
            cx, cy = compute_centroid(x1, y1, x2, y2)

            if track_id not in prev_line_sides:
                prev_line_sides[track_id] = [
                    get_line_side((cx, cy), lines[0][0], lines[0][1]),
                    get_line_side((cx, cy), lines[1][0], lines[1][1]),
                    get_line_side((cx, cy), lines[2][0], lines[2][1])
                ]
                last_intent[track_id] = None

            # ==========================================
            # NOVA LÓGICA DE CRUZAMENTO DE LINHAS
            # ==========================================

            # Lê os 3 lados primeiro para o frame atual
            curr_sides = [get_line_side((cx, cy), p, p_end) for p, p_end in lines]

            # 1º PASSO: Verifica intenções ANTES da catraca (Linhas 0 e 2)
            for i in [0, 2]:
                prev_side = prev_line_sides[track_id][i]
                curr_side = curr_sides[i]

                if prev_side == 0:
                    prev_side = curr_side

                if prev_side * curr_side < 0:
                    flash_counters[i] = FLASH_FRAMES
                    last_intent[track_id] = i  # Grava a intenção de onde veio

            # 2º PASSO: Verifica a catraca (Linha 1 - Verde)
            i = 1
            prev_side_gate = prev_line_sides[track_id][i]
            curr_side_gate = curr_sides[i]

            if prev_side_gate == 0:
                prev_side_gate = curr_side_gate

            if prev_side_gate * curr_side_gate < 0:
                flash_counters[i] = FLASH_FRAMES

                # Se cruzou a linha verde, verifica se tem intenção gravada
                if frame_id >= count_lock.get(track_id, 0):
                    intent = last_intent.get(track_id)
                    if intent == 0:
                        entradas += 1
                        count_lock[track_id] = frame_id + LOCK_FRAMES
                        last_intent[track_id] = None
                        timestamp = time.time() - start_time
                        print(f"[{timestamp:.2f}s | Frame {frame_id}] ID {track_id} ENTROU. Saldo: {entradas}")
                    elif intent == 2:
                        saidas += 1
                        count_lock[track_id] = frame_id + LOCK_FRAMES
                        last_intent[track_id] = None
                        timestamp = time.time() - start_time
                        print(f"[{timestamp:.2f}s | Frame {frame_id}] ID {track_id} SAIU. Saldo: {saidas}")

            # Atualiza o histórico para o próximo frame
            prev_line_sides[track_id] = curr_sides

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
            cv2.putText(frame, f"ID: {track_id}", (x1, max(0, y1 - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.circle(frame, (cx, cy), 3, (0, 255, 0), -1)

        # Desenho das linhas e flashes
        line_colors = [LINE_COLOR_1, LINE_COLOR_2, LINE_COLOR_3]
        for i, (p1, p2) in enumerate(lines):
            if flash_counters[i] > 0:
                color = LINE_COLOR_FLASH
                flash_counters[i] -= 1
            else:
                color = line_colors[i]
            cv2.line(frame, p1, p2, color, 2)

        # Textos informativos no ecrã
        cv2.putText(frame, "Arraste L1/L2/L3 para mover | SHIFT+arraste em L3 muda altura",
                    (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Entradas: {entradas}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, f"Saidas: {saidas}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        if DISPLAY_SCALE != 1.0:
            display = cv2.resize(frame, (0, 0), fx=DISPLAY_SCALE, fy=DISPLAY_SCALE)
        else:
            display = frame

        cv2.imshow(window_name, display)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()