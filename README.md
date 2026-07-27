# 🦾 Iron Man - Advanced Repulsor & HUD

<div align="center">

**Transform your webcam into an advanced Iron Man suit interface**

Real-time hand and face tracking with Tony Stark-style glowing effects, tactical HUD, and interactive repulsor weapons.

![Python](https://img.shields.io/badge/Python-3.8+-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![OpenCV](https://img.shields.io/badge/OpenCV-4.0+-5C3EE8?style=for-the-badge&logo=opencv)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Latest-00D4AA?style=for-the-badge)

</div>

---

## ✨ Features

### 🎯 Weapon Systems

| Feature | Control | Description |
|---------|---------|-------------|
| **Advanced Repulsors** | Open Palm | Activate glowing, rotating repulsor aperture |
| **Repulsor Blast** | Fist → Open | Charge and fire energy blast with trails & sparks |
| **Unibeam** | Both Palms Together | Massive continuous energy beam from center |
| **Energy Shield** | Cross Arms (Fists) | Deploy spinning hexagonal energy shield |
| **Flight Mode** | Palms Down | Engage glowing thruster jets |
| **Precision Laser** | Index Finger Point | Fire continuous cutting laser |

### 🎨 Advanced HUD Systems

- **J.A.R.V.I.S. Interface** — Live tactical updates via typewriter subtitles
- **Dynamic Camera Recoil** — HUD shakes when firing heavy weapons
- **Face Targeting** — Auto-locks onto faces with crosshairs & threat telemetry
- **Arc Reactor Display** — Glowing, pulsing power core at bottom center
- **Artificial Horizon** — Real-time pitch and roll stabilization indicators
- **Live Telemetry** — FPS counter, suit power levels, and system time

---

## 📋 Requirements

- **Python** 3.8 or higher
- **Webcam** for real-time tracking
- **4GB RAM** (minimum)

### Dependencies

```bash
pip install opencv-python mediapipe numpy
```

Or install all at once:

```bash
pip install -r requirements.txt
```

---

## 🚀 Quick Start

1. **Clone the repository** (if not already done)
   ```bash
   git clone https://github.com/Abu-Bakar-Rakib/Iron-Man---Advanced-Repulsor-HUD.git
   cd Iron-Man---Advanced-Repulsor-HUD
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python main.py
   ```

4. **Allow webcam access** when prompted by your system

---

## 🎮 Keyboard Controls

| Key | Action |
|-----|--------|
| **`Q`** or **`ESC`** | Exit application |
| **`H`** | Toggle HUD overlay |
| **`C`** | Cycle suit color themes |
| **`G`** | Toggle Glitch/Damage mode |

### Available Suit Colors
- 🔵 Classic Blue (Default)
- 🟡 Gold
- 🟢 Green
- 🟣 Violet

---

## 🎬 How It Works

This application leverages cutting-edge computer vision technology:

1. **Hand Tracking** — MediaPipe detects hand poses and finger positions in real-time
2. **Face Detection** — Identifies and locks onto faces for targeting HUD
3. **Gesture Recognition** — Interprets hand gestures to trigger different weapon systems
4. **Overlay Rendering** — OpenCV applies visual effects and HUD elements to video feed
5. **Performance Optimization** — Efficient frame processing for smooth 30+ FPS playback

---

## 📁 Project Structure

```
Iron-Man---Advanced-Repulsor-HUD/
├── main.py                  # Main application entry point
├── requirements.txt         # Python dependencies
├── README.md               # This file
└── assets/                 # Visual effects and resources (if applicable)
```

---

## ⚙️ Performance Tips

- **Lighting**: Ensure adequate lighting for better hand detection
- **Distance**: Position yourself 0.5-1.5 meters from the camera
- **GPU**: For better performance, consider using a GPU-enabled version of OpenCV
- **Resolution**: Lower webcam resolution if experiencing lag

---

## 🤝 Contributing

Found a bug? Have a feature request? Feel free to:
1. [Report an issue](../../issues)
2. [Submit a pull request](../../pulls)

---

## 📜 License

This project is open source and available under the MIT License.

---

## 🙋 Support

Having issues? Try these steps:
1. Ensure your webcam is working and accessible
2. Check that all dependencies are installed: `pip install -r requirements.txt`
3. Try running with `python -u main.py` for unbuffered output
4. Check your Python version: `python --version` (must be 3.8+)

---

<div align="center">

**"I am Iron Man"** — Enjoy the suit, Tony! 🦾⚡

</div>
