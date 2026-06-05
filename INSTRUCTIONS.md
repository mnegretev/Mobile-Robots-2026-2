# Installation & Workspace Configuration

Target: **ROS 2 Jazzy** on **Ubuntu 24.04**. Repo branch: `dominguez_osio`.

---

## 1. System packages (once)

The course `Setup.sh` already installs the ROS side. Make sure these are present:

```bash
sudo apt install \
  ros-jazzy-ros-gz ros-jazzy-gz-ros2-control ros-jazzy-moveit \
  ros-jazzy-slam-toolbox ros-jazzy-nav2-amcl ros-jazzy-nav2-map-server \
  ros-jazzy-joint-trajectory-controller ros-jazzy-joint-state-broadcaster \
  ros-jazzy-diff-drive-controller ros-jazzy-controller-manager \
  python3-rtree portaudio19-dev          # portaudio19-dev is needed by pyaudio
```

## 2. Ollama + llama3 (local LLM, no cloud)

```bash
curl -fsSL https://ollama.com/install.sh | sh   # installs the daemon
ollama serve &                                  # background server on :11434
ollama pull llama3                              # downloads the model (~4.7 GB)
ollama run llama3 "hello"                       # quick sanity check
```

The orchestrator talks to `http://localhost:11434/api/chat`. Keep `ollama serve`
running whenever you launch the orchestrator.

## 3. Python virtual environment

Create the venv with `--system-site-packages` so ROS 2's `rclpy` and message
modules stay importable inside it:

```bash
python3 -m venv --system-site-packages ~/mr_venv
source ~/mr_venv/bin/activate
pip install --upgrade pip
pip install -r ~/Mobile-Robots-2026-2/ros2_ws/src/final_project/requirements.txt
```

`requirements.txt` installs: `faster-whisper`, `piper-tts`, `pyaudio`,
`ultralytics` (pulls `torch`+`opencv`), `requests`.

> GPU note: `ultralytics` uses CUDA if available. If you have no NVIDIA GPU,
> launch `yolo_detector` with `device:=cpu` (see §6) and it still works.

### Piper voice model
`text2speech/pipertts.py` loads `models/es_MX-claude-high.onnx`. Make sure that
`.onnx` and its `.onnx.json` exist under the installed `text2speech` share dir.
Download Spanish-MX voices from the Piper voices repo if missing.

## 4. Apply the small repo fixes

```bash
cd ~/Mobile-Robots-2026-2/ros2_ws/src

# (a) register the ASR entry point (its console_scripts is empty)
#     edit hri/speech2text/setup.py -> entry_points -> console_scripts:
#         'faster_whisper_asr = speech2text.faster_whisper_asr:main',

# (b) final_project/package.xml: add  <depend>nav_msgs</depend>
#     and change <depend>tf</depend> to <depend>tf2_ros</depend>
```

(Both are one-line edits, detailed in SUMMARY_OF_MODIFICATIONS.md.)

## 5. Build the workspace

```bash
cd ~/Mobile-Robots-2026-2/ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

Build `final_project` alone after edits:
```bash
colcon build --symlink-install --packages-select final_project speech2text
```

## 6. Run (four terminals, each sources the workspace + venv)

```bash
# T1 - simulator (Gazebo)
ros2 launch house_simul house_simul.launch.py

# T2 - map + AMCL + A* + smoothing + pure_pursuit
ros2 launch final_project final_project_utils.launch.py

# T3 - inverse kinematics service (arm)
ros2 run ik_numeric nr

# T4 - the AI layer: speech, TTS, YOLO, orchestrator
source ~/mr_venv/bin/activate
ros2 launch final_project orchestrator.launch.py
```

Optional overrides:
```bash
ros2 run final_project yolo_detector --ros-args -p device:=cpu -p conf:=0.5
```

Then **speak a command** (Spanish, matching the few-shot example), e.g.
*"Tráeme el control remoto de la sala."* Watch T4 logs: it prints the plan,
then steps through move_to → find → grasp → return_to_user → say.

## 7. Test the planner without the robot

```bash
source ~/mr_venv/bin/activate
cd ~/Mobile-Robots-2026-2/ros2_ws/src/final_project/final_project
python3 llm_orchestrator.py "Tráeme el control remoto de la sala"
# prints the numbered list of sub-tasks
```

## 8. Common issues

| Symptom | Fix |
|---------|-----|
| `Ollama request failed` | `ollama serve` not running, or model not pulled (`ollama pull llama3`). |
| `package 'speech2text' executable 'faster_whisper_asr' not found` | Entry point not registered — do §4(a) then rebuild. |
| pyaudio build error | `sudo apt install portaudio19-dev` then reinstall pyaudio. |
| YOLO sees nothing | Confirm camera topic with `ros2 topic echo /camera/image_raw --once`; it must be `/camera/image_raw`, not `/camera/color/image_raw`. |
| robot never reaches goal | Check `/goal_pose` is consumed by `pure_pursuit` and `/navigation/goal_reached` is published. |
| IK call returns empty | Tune the target pose in `SM_GRASP`; pose may be outside the arm workspace. |
| numpy 2.x ABI errors | `pip install "numpy<2.0"` inside the venv. |
