# Iron Man - Advanced Repulsor & HUD

Turn your webcam into an advanced Iron Man suit interface! This Python application uses MediaPipe and OpenCV to track your hand and face movements in real-time, overlaying Tony Stark-style glowing repulsors, energy shields, and a complex Heads-Up Display (HUD).

## Features

- **Advanced Repulsors**: Open your palm to activate a glowing, rotating repulsor aperture.
- **Repulsor Blast**: Make a fist to charge the repulsor, then quickly open your palm to fire an energy blast that travels across the screen with trails and sparks.
- **Unibeam (Two-Handed)**: Bring both open palms close together to fire a massive, continuous energy beam from the center of the screen.
- **Energy Shield (Two-Handed)**: Cross your arms by bringing two fists close together to deploy a spinning, hexagonal energy shield.
- **Flight Mode**: Point your open palms downwards to engage glowing thruster jets.
- **Precision Laser**: Point with just your index finger to fire a continuous cutting laser.
- **Advanced HUD**:
  - **J.A.R.V.I.S. Interface**: An AI assistant provides live tactical updates via typewriter subtitles.
  - **Camera Recoil**: The HUD and camera feed dynamically shake when firing heavy weapons.
  - **Face Targeting**: Automatically locks onto faces in the camera feed with crosshairs and dynamic threat telemetry.
  - **Arc Reactor**: A glowing, pulsing Arc Reactor display at the bottom center.
  - **Artificial Horizon**: Real-time simulated pitch and roll stabilization indicators in the center.
  - **Telemetry**: Displays current FPS, suit power levels, and system time.

## Requirements

Ensure you have Python installed. Install the required dependencies using:

```bash
pip install opencv-python mediapipe numpy
```
(Or simply run `pip install -r requirement.txt`)

## How to Run

Navigate to the project directory in your terminal and run:

```bash
python main.py
```

## Controls

While the application is running, you can use the following keyboard controls:
- **`q`** or **`ESC`**: Quit the application.
- **`h`**: Toggle the HUD overlay (Arc Reactor, Targeting, Horizon, etc.) on or off.
- **`c`**: Cycle through different suit color themes (Classic Blue, Gold, Green, Violet).
- **`g`**: Toggle Glitch/Damage mode (simulates a damaged suit interface).

Enjoy the suit, Tony!
