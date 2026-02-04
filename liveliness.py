# liveliness.py
import threading
import time
from collections import deque
import numpy as np
import cv2
import mediapipe as mp
import queue
import serial   # <-- ESP32 SUPPORT ADDED HERE

# ---------------------------------------------------
# ESP32 CONFIG
# ---------------------------------------------------
ESP32_PORT = "COM3"          # your port
ESP32_BAUD = 115200          # your baud rate

esp32 = None

def init_esp32():
    """Initialize ESP32 Serial Connection."""
    global esp32
    try:
        esp32 = serial.Serial(ESP32_PORT, ESP32_BAUD, timeout=1)

        # Prevent ESP32-CAM-MB from resetting when Python connects
        esp32.dtr = False
        esp32.rts = False

        print("ESP32 Connected on", ESP32_PORT)
        time.sleep(2)   # allow ESP32 to boot fully
    except Exception as e:
        print("ESP32 NOT FOUND:", e)
        esp32 = None


def send_blink_to_esp32():
    """Send blink signal to ESP32 LED."""
    if esp32:
        try:
            esp32.write(b"B")  # <-- ESP32 receives 'B' to blink
        except:
            pass


# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------
DEFAULT_CAM_INDEX = 0
DEFAULT_WIDTH = 640
DEFAULT_HEIGHT = 480

DEFAULT_EAR_THRESHOLD = 0.21
DEFAULT_BLINK_FRAMES = 2
EAR_SMOOTH_WINDOW = 4
BLINK_COOLDOWN_FRAMES = 10

PUPIL_MOVE_THRESHOLD = 2.0
IRIS_EDGE_THRESHOLD = 0.12

# pupil reaction (new)
REACTION_TEST_DURATION = 0.8
REACTION_SMOOTH = 0.35
REACTION_MIN_RADIUS = 3.0

_running = False
_blink_count = 0
_pupil_moves = 0
_iris_edge_events = 0
_pupil_reaction_value = None


class CameraCapture:
    def __init__(self, index=0, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, qsize=2):
        self.cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.q = queue.Queue(maxsize=qsize)
        self.running = True
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.01)
                continue
            if self.q.full():
                try:
                    self.q.get_nowait()
                except:
                    pass
            try:
                self.q.put_nowait(frame)
            except:
                pass

    def read(self):
        try:
            return self.q.get(timeout=0.1)
        except:
            return None

    def stop(self):
        self.running = False
        try:
            self.cap.release()
        except:
            pass


def _euclid(a, b):
    return np.linalg.norm(a - b)


def _calc_ear(eye_pts):
    if eye_pts is None or len(eye_pts) < 6:
        return None
    A = _euclid(eye_pts[1], eye_pts[5])
    B = _euclid(eye_pts[2], eye_pts[4])
    C = _euclid(eye_pts[0], eye_pts[3])
    if C < 1e-6:
        return None
    return (A + B) / (2.0 * C)


def _iris_radius(pts):
    if pts is None or len(pts) < 3:
        return None
    c = np.mean(pts, axis=0)
    d = np.linalg.norm(pts - c, axis=1)
    return float(np.mean(d))


def _draw_iris(frame, cx, cy, r):
    if cx is None or cy is None or r is None:
        return
    cx, cy = int(cx), int(cy)
    r = max(4, int(r))
    cv2.circle(frame, (cx, cy), r, (0, 255, 0), 2)
    cv2.circle(frame, (cx, cy), max(3, r - 4), (255, 0, 0), 2)


# ---------------------------------------------------
# WORKER LOOP WITH CONTRACTION + DILATION
# ---------------------------------------------------
def _worker_loop(cam, settings, status_label, footer_label):
    global _running, _blink_count, _pupil_moves, _iris_edge_events, _pupil_reaction_value

    ear_threshold = float(settings.get("ear_threshold", DEFAULT_EAR_THRESHOLD))
    blink_required = int(settings.get("blink_frames_required", DEFAULT_BLINK_FRAMES))
    pupil_move_threshold = float(settings.get("pupil_move_threshold", PUPIL_MOVE_THRESHOLD))
    iris_edge_threshold = float(settings.get("iris_edge_threshold", IRIS_EDGE_THRESHOLD))

    face_mesh = mp.solutions.face_mesh.FaceMesh(
        static_image_mode=False, max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    ear_buf = deque(maxlen=EAR_SMOOTH_WINDOW)
    blink_frames = 0
    blink_cooldown = 0

    last_pupil_center = None
    last_left_center = None
    last_right_center = None
    last_left_radius = None
    last_right_radius = None

    test_start_radius = None
    test_start_time = None
    _pupil_reaction_value = None

    frame_i = 0

    LEFT_EYE_IDX = [33, 160, 158, 133, 153, 144]
    RIGHT_EYE_IDX = [263, 387, 385, 362, 380, 373]
    LEFT_IRIS_IDX = [468, 469, 470, 471]
    RIGHT_IRIS_IDX = [473, 474, 475, 476]

    _blink_count = _pupil_moves = _iris_edge_events = 0

    while _running:
        frame = cam.read()
        if frame is None:
            continue

        frame_i += 1
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = face_mesh.process(rgb)

        if not res.multi_face_landmarks:
            cv2.putText(frame, "NO FACE", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.imshow("Iris Liveliness", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break
            continue

        lm = res.multi_face_landmarks[0].landmark
        FL = np.array([(p.x * w, p.y * h) for p in lm], dtype=np.float32)

        def pts(index_list):
            return np.array([FL[i] for i in index_list], dtype=np.float32)

        Leye = pts(LEFT_EYE_IDX)
        Reye = pts(RIGHT_EYE_IDX)
        L_EAR = _calc_ear(Leye)
        R_EAR = _calc_ear(Reye)
        meanEAR = (L_EAR + R_EAR) / 2 if L_EAR and R_EAR else (L_EAR or R_EAR or ear_threshold)

        ear_buf.append(meanEAR)
        EAR_s = sum(ear_buf) / len(ear_buf)

        # ---------------------------------------
        # BLINK LOGIC + ESP32 LED BLINK TRIGGER
        # ---------------------------------------
        if EAR_s < ear_threshold:
            blink_frames += 1
        else:
            if blink_frames >= blink_required and blink_cooldown == 0:
                _blink_count += 1
                blink_cooldown = BLINK_COOLDOWN_FRAMES

                # 🔥 SEND BLINK SIGNAL TO ESP32
                send_blink_to_esp32()

            blink_frames = 0

        if blink_cooldown > 0:
            blink_cooldown -= 1

        # Iris detection section remains unchanged
        left_iris_pts = pts(LEFT_IRIS_IDX)
        right_iris_pts = pts(RIGHT_IRIS_IDX)

        left_center = np.mean(left_iris_pts, axis=0) if left_iris_pts.size else None
        right_center = np.mean(right_iris_pts, axis=0) if right_iris_pts.size else None

        left_radius = _iris_radius(left_iris_pts) if left_iris_pts.size else None
        right_radius = _iris_radius(right_iris_pts) if right_iris_pts.size else None

        if left_center is not None:
            last_left_center = left_center
            last_left_radius = left_radius
        if right_center is not None:
            last_right_center = right_center
            last_right_radius = right_radius

        if left_center is None and last_left_center is not None:
            left_center = last_left_center
            left_radius = last_left_radius
        if right_center is None and last_right_center is not None:
            right_center = last_right_center
            right_radius = last_right_radius

        active_radius = left_radius if left_radius else right_radius

        if active_radius and test_start_radius is None:
            test_start_radius = active_radius
            test_start_time = time.time()

        if test_start_radius and time.time() - test_start_time >= REACTION_TEST_DURATION:
            if active_radius > REACTION_MIN_RADIUS:
                raw_change = (test_start_radius - active_radius) / test_start_radius
                if _pupil_reaction_value is None:
                    _pupil_reaction_value = raw_change
                else:
                    _pupil_reaction_value = (
                        REACTION_SMOOTH * raw_change +
                        (1 - REACTION_SMOOTH) * _pupil_reaction_value
                    )
            test_start_radius = None
            test_start_time = None

        chosen = left_center if left_center is not None else right_center
        if chosen is not None:
            if last_pupil_center is not None:
                if _euclid(chosen, last_pupil_center) > pupil_move_threshold:
                    _pupil_moves += 1
            last_pupil_center = chosen

        def circ(I):
            if I is None or len(I) == 0:
                return 0
            c = np.mean(I, axis=0)
            d = np.linalg.norm(I - c, axis=1)
            return np.std(d) / (np.mean(d) + 1e-8)

        mc = []
        if left_iris_pts.size:
            mc.append(circ(left_iris_pts))
        if right_iris_pts.size:
            mc.append(circ(right_iris_pts))
        if mc and (sum(mc) / len(mc)) > iris_edge_threshold:
            _iris_edge_events += 1

        if left_center is not None:
            _draw_iris(frame, left_center[0], left_center[1], left_radius)
        if right_center is not None:
            _draw_iris(frame, right_center[0], right_center[1], right_radius)

        if _pupil_reaction_value is not None:
            ratio = float(_pupil_reaction_value)
            color = (0, 255, 0) if ratio > 0 else (0, 0, 255)
            cv2.putText(frame, f"Pupil Reaction: {ratio:+.2f}",
                        (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        cv2.putText(frame, f"EAR: {EAR_s:.3f}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 255), 2)

        cv2.putText(frame, f"Blinks: {_blink_count}", (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 255, 200), 2)

        cv2.putText(frame, f"Moves: {_pupil_moves}  Edge: {_iris_edge_events}",
                    (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)

        live_lively = _blink_count > 0 or (
            _pupil_reaction_value is not None and _pupil_reaction_value > 0.08
        ) or _pupil_moves > 0

        if live_lively:
            cv2.putText(frame, "LIVELY", (400, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
        else:
            cv2.putText(frame, "NOT LIVELY", (350, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

        cv2.imshow("Iris Liveliness", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    face_mesh.close()
    cv2.destroyAllWindows()


# ---------------------------------------------------
# PUBLIC API
# ---------------------------------------------------
_camera = None


def start_liveliness(settings=None, status_label=None, footer_label=None, cam_index=DEFAULT_CAM_INDEX):
    global _running, _camera
    if _running:
        return
    _running = True

    init_esp32()   # <-- ESP32 INITIALIZED HERE

    if settings is None:
        settings = {}

    _camera = CameraCapture(index=cam_index)
    threading.Thread(
        target=_worker_loop,
        args=(_camera, settings, status_label, footer_label),
        daemon=True
    ).start()


def stop_liveliness():
    global _running, _camera
    _running = False
    if _camera:
        _camera.stop()


def get_final_stats():
    return {
        "blinks": _blink_count,
        "moves": _pupil_moves,
        "edges": _iris_edge_events,
        "contraction": _pupil_reaction_value
    }
