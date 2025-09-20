import mujoco
import mujoco.viewer

# Load your robot MJCF/XML
xml_path = "/so100/Simulation/SO100/so100_mjcf/so100.xml"
m = mujoco.MjModel.from_xml_path(xml_path)
d = mujoco.MjData(m)

def key_callback(viewer, key, scancode, action, mods):
    if key == 256:  # ESC
        viewer.close()

with mujoco.viewer.launch_passive(m, d, key_callback=key_callback) as viewer:
    while viewer.is_running():
        # Step physics
        mujoco.mj_step(m, d)
        # Render automatically includes the robot
        viewer.sync()
