# Steps to Run Simulation

## Prerequisites

Since the Docker file is still under development, please create a virtual environment for testing. Follow the installation guide from the [robosuite documentation](https://robosuite.ai/docs/installation.html).

## Installation Steps

### 1. Build from Source
Follow the "build from source" option from the robosuite documentation, but **clone this repository instead of the official robosuite repository**.

### 2. Install Dependencies
Install the required packages using the provided requirements files:

```bash
pip install -r requirements.txt
pip install -r requirements-extra.txt
```

### 3. Troubleshooting Installation
If you encounter any errors during installation, try upgrading pip first:

```bash
pip install --upgrade pip
```

Then retry the installation commands above.

## Configuration

### Robot Controller Configuration
To change the robot controller settings, modify the configuration file:

**File:** `Organizer-Robot/robosuite/controllers/config/robots/default_so100.json`

Change the controller from `OSC_POSE` to other available options as needed.

### Initial Joint Positions
To modify the robot arm's initial joint positions, update the initial joint variables in:

**File:** `Organizer-Robot/robosuite/models/robots/manipulators/so101_robot.py`

## Running the Simulation

### Demo Simulation
To test the demo simulation, run:

**File:** `Organizer-Robot/robosuite/demos/demo_device_control_so101.py`

**Arguments:**
- **Environment:** Stack
- **Robot:** SO101 arm

## Testing and Experimentation

Feel free to test and experiment with the robot simulation as much as possible. The setup is designed to be flexible for various testing scenarios.

---

**Note:** Make sure your virtual environment is activated before running any commands or simulations.