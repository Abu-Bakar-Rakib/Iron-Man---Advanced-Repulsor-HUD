"""
Iron Man - Repulsor & HUD (Phase 4: Robust Edition)
---------------------------------------------------
Upgraded real-time webcam app with threaded capture, smoothed tracking,
dynamic J.A.R.V.I.S. context, alpha-blended energy effects, and scale-
invariant gesture recognition.
"""

import cv2
import numpy as np
import mediapipe as mp
import math
import time
import random
import threading

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

THEMES = [
    {"core": (255, 255, 255), "primary": (255, 60, 0), "secondary": (255, 200, 80), "name": "MARK III"},
    {"core": (255, 255, 255), "primary": (0, 200, 255), "secondary": (80, 255, 255), "name": "MARK L"},
    {"core": (255, 255, 255), "primary": (0, 255, 100), "secondary": (120, 255, 120), "name": "MARK IV"},
    {"core": (255, 255, 255), "primary": (200, 0, 255), "secondary": (255, 100, 255), "name": "MARK VI"},
]

REPULSOR_MAX_RADIUS = 90
BLAST_SPEED = 1200.0
BLAST_MAX_LIFE = 1.2
FIST_TO_OPEN_COOLDOWN = 0.3
POWER_DRAIN_REPULSOR = 5
POWER_DRAIN_UNIBEAM = 15
POWER_REGEN = 8

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
FACE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# --------------------------------------------------------------------------
# Threaded Camera (For Robust FPS)
# --------------------------------------------------------------------------

class ThreadedCamera:
    def __init__(self, src=0):
        self.cap = cv2.VideoCapture(src)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.ret, self.frame = self.cap.read()
        self.running = True
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self.update, daemon=True)
        self.thread.start()

    def update(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.ret, self.frame = ret, frame
            time.sleep(0.001) # Prevent CPU hogging

    def read(self):
        with self.lock:
            return self.ret, self.frame.copy() if self.ret else (False, None)

    def release(self):
        self.running = False
        self.thread.join()
        self.cap.release()

# --------------------------------------------------------------------------
# Helpers & Math
# --------------------------------------------------------------------------

def dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)

def get_extended_fingers(landmarks):
    """Scale-invariant finger extension check."""
    wrist = landmarks[0]
    palm_size = dist(wrist, landmarks[9]) or 0.0001 
    
    pairs = [(4, 2), (8, 6), (12, 10), (16, 14), (20, 18)]
    ext = []
    for tip_i, pip_i in pairs:
        if tip_i == 4:
            ext.append(dist(wrist, landmarks[tip_i]) > dist(wrist, landmarks[pip_i]) * 1.1)
        else:
            ext.append(landmarks[tip_i].y < landmarks[pip_i].y)
    return ext

def palm_center(landmarks, w, h):
    idxs = [0, 5, 9, 13, 17]
    xs = [landmarks[i].x for i in idxs]
    ys = [landmarks[i].y for i in idxs]
    return int(np.mean(xs) * w), int(np.mean(ys) * h)

def forearm_direction(landmarks, w, h):
    wrist = landmarks[0]
    mid_mcp = landmarks[9]
    dx = (mid_mcp.x - wrist.x) * w
    dy = (mid_mcp.y - wrist.y) * h
    length = math.hypot(dx, dy) or 1.0
    return dx / length, dy / length

def is_pointing_down(landmarks):
    wrist = landmarks[0]
    tips = [8, 12, 16, 20]
    for t in tips:
        if landmarks[t].y < wrist.y + 0.05:
            return False
    return True

def draw_alpha_poly(layer, pts, color, alpha=0.6):
    overlay = layer.copy()
    pts = np.array(pts, np.int32).reshape((-1, 1, 2))
    cv2.fillPoly(overlay, [pts], color)
    cv2.addWeighted(overlay, alpha, layer, 1 - alpha, 0, layer)

def draw_alpha_circle(layer, center, radius, color, alpha=0.8, thickness=-1):
    overlay = layer.copy()
    cv2.circle(overlay, center, radius, color, thickness, cv2.LINE_AA)
    cv2.addWeighted(overlay, alpha, layer, 1 - alpha, 0, layer)

# --------------------------------------------------------------------------
# Visual Effects
# --------------------------------------------------------------------------

def draw_advanced_repulsor(layer, center, radius, colors, t, charge=1.0):
    cx, cy = center
    pulse = 1.0 + 0.1 * math.sin(t * 15)
    r = max(4, int(radius * pulse * charge))
    
    draw_alpha_circle(layer, (cx, cy), int(r * 1.2), colors["primary"], alpha=0.2)
    draw_alpha_circle(layer, (cx, cy), int(r * 0.8), colors["secondary"], alpha=0.4)
    
    for i in range(3):
        a = t * (2 if i % 2 == 0 else -3) + i * math.pi
        p1 = (int(cx + r * math.cos(a)), int(cy + r * math.sin(a)))
        p2 = (int(cx + r * math.cos(a+2.5)), int(cy + r * math.sin(a+2.5)))
        cv2.line(layer, p1, p2, colors["core"], 2, cv2.LINE_AA)
        
    draw_alpha_circle(layer, (cx, cy), int(r * 0.4), colors["core"], alpha=0.9)

def draw_charging_glow(layer, center, colors, t):
    cx, cy = center
    pulse = 0.5 + 0.5 * abs(math.sin(t * 8))
    r = int(20 + pulse * 15)
    draw_alpha_circle(layer, (cx, cy), r, colors["primary"], alpha=0.5 * pulse)
    cv2.circle(layer, (cx, cy), 5, colors["core"], -1, cv2.LINE_AA)

def draw_blast(layer, blast, colors):
    age = time.time() - blast["spawn_time"]
    if age > BLAST_MAX_LIFE: return False
    
    t_frac = age / BLAST_MAX_LIFE
    dist_traveled = BLAST_SPEED * age
    cx = int(blast["origin"][0] + blast["dir"][0] * dist_traveled)
    cy = int(blast["origin"][1] + blast["dir"][1] * dist_traveled)
    
    radius = int(35 + 50 * t_frac)
    alpha = max(0.0, 1.0 - t_frac)
    
    draw_alpha_circle(layer, (cx, cy), radius, colors["primary"], alpha=0.4 * alpha)
    draw_alpha_circle(layer, (cx, cy), int(radius * 0.6), colors["core"], alpha=0.9 * alpha)
    
    for i in range(1, 10):
        td = dist_traveled - i * 35
        if td > 0:
            tx = int(blast["origin"][0] + blast["dir"][0] * td)
            ty = int(blast["origin"][1] + blast["dir"][1] * td)
            tr = max(2, int((radius * 0.5) * (1 - i / 10)))
            draw_alpha_circle(layer, (tx, ty), tr, colors["secondary"], alpha=0.3 * alpha)
    return True

def draw_energy_shield(layer, p1, p2, colors, t):
    cx, cy = (p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2
    dist_h = math.hypot(p1[0]-p2[0], p1[1]-p2[1])
    radius = int(dist_h * 1.2)
    
    overlay = layer.copy()
    for i in range(6):
        a = t * 2 + math.radians(i * 60)
        x1, y1 = cx + radius * math.cos(a), cy + radius * math.sin(a)
        x2, y2 = cx + radius * math.cos(a + math.pi/3), cy + radius * math.sin(a + math.pi/3)
        cv2.line(overlay, (int(x1), int(y1)), (int(x2), int(y2)), colors["secondary"], 5, cv2.LINE_AA)
    cv2.addWeighted(overlay, 0.7, layer, 0.3, 0, layer)
    
    draw_alpha_circle(layer, (cx, cy), radius, colors["primary"], alpha=0.2)
    draw_alpha_circle(layer, (cx, cy), int(radius * 0.8), colors["core"], alpha=0.1)

def draw_unibeam(layer, p1, p2, colors, t, h, w):
    cx, cy = (p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2
    pulse = 1.0 + 0.4 * math.sin(t * 25)
    width = int(100 * pulse)
    
    overlay = layer.copy()
    pts = np.array([[cx - width, cy], [cx + width, cy], [w // 2 + width*4, 0], [w // 2 - width*4, 0]], np.int32)
    cv2.fillPoly(overlay, [pts], colors["primary"])
    cv2.addWeighted(overlay, 0.5, layer, 0.5, 0, layer)
    
    draw_alpha_poly(layer, pts, colors["core"], alpha=0.8)
    draw_alpha_circle(layer, (cx, cy), int(140 * pulse), colors["primary"], alpha=0.6)
    draw_alpha_circle(layer, (cx, cy), int(80 * pulse), colors["core"], alpha=0.9)

def draw_thruster(layer, cx, cy, colors, t, h):
    pulse = 1.0 + 0.3 * math.sin(t * 30)
    length = int(200 * pulse)
    width = 30
    
    overlay = layer.copy()
    pts = np.array([[cx - width, cy], [cx + width, cy], [cx, cy + length]], np.int32)
    cv2.fillPoly(overlay, [pts], colors["primary"])
    cv2.addWeighted(overlay, 0.6, layer, 0.4, 0, layer)
    
    pts_core = np.array([[cx - width//2, cy], [cx + width//2, cy], [cx, cy + int(length*0.7)]], np.int32)
    cv2.fillPoly(layer, [pts_core], colors["core"])

# --------------------------------------------------------------------------
# HUD Elements
# --------------------------------------------------------------------------

def draw_hud(frame, colors, t, fps, power, state_msg, face_box=None):
    h, w = frame.shape[:2]
    primary = colors["primary"]
    secondary = colors["secondary"]
    core = colors["core"]
    
    # 1. Corner Brackets
    m, s = 20, 50
    for x, y, dx, dy in [(m, m, 1, 1), (w-m, m, -1, 1), (m, h-m, 1, -1), (w-m, h-m, -1, -1)]:
        cv2.line(frame, (x, y), (x + dx * s, y), primary, 2, cv2.LINE_AA)
        cv2.line(frame, (x, y), (x, y + dy * s), primary, 2, cv2.LINE_AA)

    # 2. Scan Line
    y_scan = int((math.sin(t * 1.5) * 0.5 + 0.5) * h)
    cv2.line(frame, (0, y_scan), (w, y_scan), secondary, 1, cv2.LINE_AA)

    # 3. Target Box (Smoothed)
    if face_box:
        fx, fy, fw, fh = face_box
        pad = 15
        x0, y0, x1, y1 = int(fx - pad), int(fy - pad), int(fx + fw + pad), int(fy + fh + pad)
        c = 15
        for px, py, dx, dy in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
            cv2.line(frame, (px, py), (px + dx * c, py), primary, 2, cv2.LINE_AA)
            cv2.line(frame, (px, py), (px, py + dy * c), primary, 2, cv2.LINE_AA)
        
        cx, cy = int(fx + fw // 2), int(fy + fh // 2)
        cv2.line(frame, (cx - 10, cy), (cx + 10, cy), primary, 1, cv2.LINE_AA)
        cv2.line(frame, (cx, cy - 10), (cx, cy + 10), primary, 1, cv2.LINE_AA)
        
        cv2.putText(frame, "TARGET: HUMANOID", (x0, y0 - 10), cv2.FONT_HERSHEY_DUPLEX, 0.5, secondary, 1, cv2.LINE_AA)
        cv2.putText(frame, f"DIST: {random.randint(10, 30)}M", (x1 + 10, y0 + 15), cv2.FONT_HERSHEY_DUPLEX, 0.4, secondary, 1, cv2.LINE_AA)

    # 4. Bottom Telemetry & Arc Reactor
    cx_r, cy_r = w // 2, h - 50
    draw_alpha_circle(frame, (cx_r, cy_r), 40, primary, alpha=0.3)
    draw_alpha_circle(frame, (cx_r, cy_r), 25, core, alpha=0.8)
    for i in range(8):
        a = t * 3 + math.radians(i * 45)
        cv2.line(frame, (cx_r + int(30*math.cos(a)), cy_r + int(30*math.sin(a))), 
                       (cx_r + int(38*math.cos(a)), cy_r + int(38*math.sin(a))), core, 2, cv2.LINE_AA)
    
    # 5. JARVIS Subtitles (Dynamic)
    msg = f"> J.A.R.V.I.S: {state_msg}"
    cv2.putText(frame, msg, (30, h - 100), cv2.FONT_HERSHEY_DUPLEX, 0.6, core, 1, cv2.LINE_AA)
    
    # 6. Suit Power Bar
    bar_x, bar_y, bar_w, bar_h = 30, 40, 200, 15
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), primary, 1)
    fill_w = int((power / 100.0) * bar_w)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), secondary, -1)
    cv2.putText(frame, f"PWR: {int(power)}%", (bar_x, bar_y - 8), cv2.FONT_HERSHEY_DUPLEX, 0.5, primary, 1, cv2.LINE_AA)
    
    # 7. Right Telemetry
    info = [f"FPS: {fps:4.1f}", f"SUIT: {colors['name']}", time.strftime("%H:%M:%S")]
    for i, line in enumerate(info):
        cv2.putText(frame, line, (w - 180, 40 + i * 22), cv2.FONT_HERSHEY_DUPLEX, 0.5, primary, 1, cv2.LINE_AA)

    # 8. Artificial Horizon (Top Left)
    cx_h, cy_h = 130, 130
    cv2.circle(frame, (cx_h, cy_h), 50, primary, 1)
    roll = math.sin(t * 0.5) * 0.3
    pitch = math.cos(t * 0.7) * 10
    for i in range(-2, 3):
        # FIX: Explicitly cast all coordinates to int to prevent OpenCV crashes
        y_off = int(cy_h + pitch + i * 15)
        x_off = int(20 * (1 - abs(i) * 0.3))
        cv2.line(frame, (cx_h - x_off, y_off), (cx_h + x_off, y_off), secondary if i == 0 else primary, 1, cv2.LINE_AA)

# --------------------------------------------------------------------------
# Main Application
# --------------------------------------------------------------------------

def main():
    cam = ThreadedCamera(0)
    if not cam.ret:
        print("Could not open webcam.")
        return

    theme_idx = 0
    show_hud = True
    glitch_mode = False
    shake_frames = 0
    blasts = []
    hand_states = {}
    prev_time = time.time()
    fps = 0.0
    suit_power = 100.0
    
    smooth_face = None
    smooth_hands = {} 

    with mp_hands.Hands(
        model_complexity=1,
        max_num_hands=2,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    ) as hands:

        while True:
            ok, frame = cam.read()
            if not ok: break

            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]

            now = time.time()
            dt = now - prev_time
            prev_time = now
            fps = 0.9 * fps + 0.1 * (1.0 / dt) if dt > 0 else fps

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            effect_layer = np.zeros_like(frame)
            colors_theme = THEMES[theme_idx]
            
            active_hands = []
            current_action = "SYSTEMS NOMINAL."
            firing_this_frame = False

            if results.multi_hand_landmarks:
                for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
                    lm = hand_landmarks.landmark
                    raw_cx, raw_cy = palm_center(lm, w, h)
                    
                    if i in smooth_hands:
                        sx, sy = smooth_hands[i]
                        alpha = 0.3 if math.hypot(raw_cx-sx, raw_cy-sy) < 50 else 0.8
                        cx, cy = int(alpha * raw_cx + (1-alpha) * sx), int(alpha * raw_cy + (1-alpha) * sy)
                    else:
                        cx, cy = raw_cx, raw_cy
                    smooth_hands[i] = (cx, cy)

                    ext = get_extended_fingers(lm)
                    n_ext = sum(ext)
                    
                    is_fist = n_ext <= 1
                    is_open = n_ext >= 4
                    is_down = is_pointing_down(lm) and is_open
                    is_laser = ext[1] and not ext[2] and not ext[3] and not ext[4]

                    active_hands.append({"id": i, "cx": cx, "cy": cy, "is_fist": is_fist, "is_open": is_open, "is_down": is_down, "is_laser": is_laser, "lm": lm})

                    state = hand_states.setdefault(i, {"was_fist": False, "last_blast": 0.0})
                    
                    if is_open and not is_down and state["was_fist"] and (now - state["last_blast"]) > FIST_TO_OPEN_COOLDOWN:
                        if suit_power >= POWER_DRAIN_REPULSOR:
                            dx, dy = forearm_direction(lm, w, h)
                            blasts.append({"origin": (cx, cy), "dir": (dx, dy), "spawn_time": now})
                            state["last_blast"] = now
                            firing_this_frame = True
                            suit_power -= POWER_DRAIN_REPULSOR
                            current_action = "REPULSOR BLAST FIRED."
                        
                    state["was_fist"] = is_fist
            
            combo_active = False
            if len(active_hands) == 2:
                h1, h2 = active_hands[0], active_hands[1]
                dist = math.hypot(h1["cx"] - h2["cx"], h1["cy"] - h2["cy"])
                
                if h1["is_open"] and h2["is_open"] and not h1["is_down"] and not h2["is_down"] and dist < 200:
                    if suit_power >= POWER_DRAIN_UNIBEAM:
                        draw_unibeam(effect_layer, (h1["cx"], h1["cy"]), (h2["cx"], h2["cy"]), colors_theme, now, h, w)
                        firing_this_frame = True
                        suit_power -= POWER_DRAIN_UNIBEAM * dt
                        current_action = "UNIBEAM AT MAXIMUM OUTPUT."
                    combo_active = True
                elif h1["is_fist"] and h2["is_fist"] and dist < 250:
                    draw_energy_shield(effect_layer, (h1["cx"], h1["cy"]), (h2["cx"], h2["cy"]), colors_theme, now)
                    current_action = "ENERGY SHIELD DEPLOYED."
                    combo_active = True

            if not combo_active:
                for ah in active_hands:
                    if ah["is_down"]:
                        draw_thruster(effect_layer, ah["cx"], ah["cy"], colors_theme, now, h)
                        current_action = "FLIGHT THRUSTERS ENGAGED."
                    elif ah["is_laser"]:
                        tip = ah["lm"][8]
                        mcp = ah["lm"][5]
                        dx, dy = tip.x - mcp.x, tip.y - mcp.y
                        length = math.hypot(dx, dy) or 1
                        end_x = int(tip.x * w + (dx/length) * w * 2)
                        end_y = int(tip.y * h + (dy/length) * h * 2)
                        cv2.line(effect_layer, (int(tip.x*w), int(tip.y*h)), (end_x, end_y), colors_theme["primary"], 4, cv2.LINE_AA)
                        cv2.line(effect_layer, (int(tip.x*w), int(tip.y*h)), (end_x, end_y), colors_theme["core"], 1, cv2.LINE_AA)
                        current_action = "PRECISION LASER ACTIVE."
                    elif ah["is_open"]:
                        draw_advanced_repulsor(effect_layer, (ah["cx"], ah["cy"]), REPULSOR_MAX_RADIUS, colors_theme, now)
                        current_action = "REPULSORS CHARGED."
                    elif ah["is_fist"]:
                        draw_charging_glow(effect_layer, (ah["cx"], ah["cy"]), colors_theme, now)

            kept_blasts = []
            for b in blasts:
                if draw_blast(effect_layer, b, colors_theme):
                    kept_blasts.append(b)
            blasts = kept_blasts
            
            if firing_this_frame:
                shake_frames = 8

            glow = cv2.GaussianBlur(effect_layer, (31, 31), 0)
            frame = cv2.addWeighted(frame, 1.0, glow, 1.2, 0)
            frame = cv2.add(frame, effect_layer)

            suit_power = min(100.0, suit_power + POWER_REGEN * dt)

            if show_hud:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = FACE_CASCADE.detectMultiScale(gray, 1.3, 5, minSize=(80, 80))
                
                if len(faces) > 0:
                    fx, fy, fw, fh = faces[0]
                    if smooth_face is None:
                        smooth_face = (fx, fy, fw, fh)
                    else:
                        sf = 0.7 
                        smooth_face = (
                            int(sf * smooth_face[0] + (1-sf) * fx),
                            int(sf * smooth_face[1] + (1-sf) * fy),
                            int(sf * smooth_face[2] + (1-sf) * fw),
                            int(sf * smooth_face[3] + (1-sf) * fh)
                        )
                else:
                    smooth_face = None

                draw_hud(frame, colors_theme, now, fps, suit_power, current_action, smooth_face)

            if shake_frames > 0:
                sx = random.randint(-10, 10)
                sy = random.randint(-10, 10)
                M = np.float32([[1, 0, sx], [0, 1, sy]])
                frame = cv2.warpAffine(frame, M, (w, h))
                shake_frames -= 1

            if glitch_mode:
                glitched = frame.copy()
                for _ in range(random.randint(1, 3)):
                    y1 = random.randint(0, h-10)
                    y2 = y1 + random.randint(2, 6)
                    shift = random.randint(-15, 15)
                    if shift > 0:
                        glitched[y1:y2, shift:] = frame[y1:y2, :-shift]
                    elif shift < 0:
                        glitched[y1:y2, :shift] = frame[y1:y2, -shift:]
                frame = glitched

            cv2.putText(frame, "q: quit  h: HUD  c: color  g: glitch", (12, h - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)

            cv2.imshow("Iron Man - Mark IV Suit", frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord('q'), 27): break
            elif key == ord('h'): show_hud = not show_hud
            elif key == ord('c'): 
                theme_idx = (theme_idx + 1) % len(THEMES)
            elif key == ord('g'): glitch_mode = not glitch_mode

    cam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()