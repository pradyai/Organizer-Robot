# Organizer-Robot 🤖

A robotics project featuring **smolVLA** (Small Vision-Language-Action model) integration with **Robosuite** and **MuJoCo** physics simulation environment.  This repository demonstrates a complete setup for vision-language-based robotic manipulation tasks.

## 🎯 What We've Built

✅ **smolVLA Integration** - Vision-Language-Action model for robotic control  
✅ **Robosuite Environment** - Comprehensive robotic manipulation suite  
✅ **MuJoCo Physics** - High-performance physics simulation engine  
✅ **Docker Environment** - Fully containerized development setup  

## 🚀 Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- GPU support (recommended for smolVLA inference)

### Installation

1. **Clone the Repository**
```bash
git clone https://github.com/pradyai/Organizer-Robot.git
cd Organizer-Robot
```

2. **Build the Docker Image**
```bash
docker build -t organizer-robot-env .
```

3. **Run the Container**

**Linux/macOS:**
```bash
docker run -d --name robot-container \
  -v "$(pwd)/Mounted_Repo:/app/Mounted_Repo" \
  organizer-robot-env
```

**Windows (PowerShell):**
```powershell
docker run -d --name robot-container -v "${pwd}/Mounted_Repo:/app/Mounted_Repo" organizer-robot-env
```

4. **Access the Container**
```bash
docker exec -it robot-container bash
```

## 🔬 Testing the Setup

### Verify MuJoCo Installation

```python
import mujoco
import gymnasium as gym

# Test basic MuJoCo functionality
env = gym.make('HalfCheetah-v4')
obs, info = env.reset()
print("✅ MuJoCo setup successful!")
```

### Test Robosuite Environment

```python
import robosuite as suite
from robosuite.controllers import load_controller_config

# Create a Robosuite environment
controller_config = load_controller_config(default_controller="OSC_POSE")
env = suite.make(
    env_name="Lift",
    robots="Panda",
    controller_configs=controller_config,
    has_renderer=False,
    has_offscreen_renderer=True,
    use_camera_obs=True,
)

# Reset and test
obs = env.reset()
print("✅ Robosuite environment ready!")
```

### Run smolVLA Model

```python
# Example smolVLA integration
from smolvla import SmolVLA

# Initialize model
model = SmolVLA. from_pretrained("smolvla-base")

# Process vision-language commands
action = model.predict(
    image=obs['camera_image'],
    instruction="Pick up the red cube"
)
print("✅ smolVLA inference successful!")
```

## 🛠️ Development Workflow

### Project Structure

```
Organizer-Robot/
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── src/
│   └── __init__.py
├── tests/
├── Mounted_Repo/          # Volume-mounted workspace
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

### Using Docker Compose

For advanced workflows, use the provided `docker-compose.yml`:

```bash
# Development environment
docker-compose -f docker/docker-compose.yml up dev

# Jupyter Lab (accessible at http://localhost:8888)
docker-compose -f docker/docker-compose.yml up jupyter
```

## 📦 Dependencies

### Core Libraries
- **MuJoCo** >= 2.3.0 - Physics simulation
- **Gymnasium** >= 0.28.0 - RL environment interface
- **Robosuite** - Robot manipulation environments
- **smolVLA** - Vision-Language-Action model
- **NumPy** >= 1.21.0
- **Matplotlib** >= 3.5.0
- **SciPy** >= 1.8.0

See `requirements.txt` for complete list.

## 🎨 Rendering Options

The environment supports multiple rendering modes:

### Headless Rendering (Default)
```bash
export MUJOCO_GL=osmesa
```

### GUI Rendering (with X11)
```bash
docker run -it --rm \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -e DISPLAY=$DISPLAY \
  organizer-robot-env
```

### VNC for Remote Access
For remote development, consider setting up VNC inside the container for GUI access.

## 🧪 Running Tests

```bash
# Inside the container
pytest tests/

# With coverage
pytest tests/ --cov=src --cov-report=html
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

1. Install pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

2. Make your changes and ensure tests pass
3. Submit a pull request

## 📝 Usage Examples

### Example 1: Basic Robosuite Task

```python
import robosuite as suite

env = suite.make(
    "Stack",
    robots="Panda",
    has_renderer=True,
    use_camera_obs=True,
)

for episode in range(10):
    obs = env.reset()
    for step in range(200):
        action = env.action_space.sample()
        obs, reward, done, info = env.step(action)
        if done:
            break
```

### Example 2: Vision-Language Control

```python
from smolvla import SmolVLA
import robosuite as suite

# Initialize environment and model
env = suite.make("PickPlace", robots="Panda", use_camera_obs=True)
model = SmolVLA.from_pretrained("smolvla-base")

# Execute natural language command
obs = env.reset()
action = model.predict(
    image=obs['frontview_image'],
    instruction="Place the blue block in the bin"
)
env.step(action)
```

## 📊 Performance Notes

- **MuJoCo**: High-performance physics at 500+ FPS
- **Robosuite**: Realistic manipulation tasks with diverse robots
- **smolVLA**:  Efficient vision-language-action inference (~10 Hz)

## 🐛 Troubleshooting

### MuJoCo Rendering Issues
```bash
# Try different rendering backends
export MUJOCO_GL=glfw  # or egl, osmesa
```

### Container Access Issues
```bash
# Stop and remove existing container
docker stop robot-container
docker rm robot-container

# Rebuild image
docker build -t organizer-robot-env .  --no-cache
```

## 📄 License

This project is open-source.  Please check individual component licenses: 
- MuJoCo: Apache 2.0
- Robosuite: MIT
- smolVLA: Check model license

## 🙏 Acknowledgments

- **MuJoCo** - DeepMind for open-sourcing the physics engine
- **Robosuite** - Stanford Vision and Learning Lab
- **smolVLA** - Vision-Language-Action research community

## 📧 Contact

For questions or collaboration, please open an issue or reach out to the maintainers.

---

**Status**: ✅ MuJoCo Running | ✅ Robosuite Configured | ✅ smolVLA Integrated
