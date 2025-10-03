import pickle
import numpy as np
import matplotlib.pyplot as plt

def load_and_examine_trajectory(filepath):
    """Load and examine a trajectory file"""
    with open(filepath, 'rb') as f:
        trajectory = pickle.load(f)
    
    print(f"Trajectory length: {len(trajectory)} timesteps")
    print(f"Language instruction: {trajectory[0]['language_instruction']}")
    
    # Examine first timestep
    first_step = trajectory[0]
    print(f"\nFirst timestep data shapes:")
    print(f"Vision: {first_step['vision'].shape}")
    print(f"Joint positions: {first_step['proprioception']['joint_positions'].shape}")
    print(f"Actions: {first_step['action'].shape}")
    
    # Show some images from the trajectory
    fig, axes = plt.subplots(1, 4, figsize=(16, 4))
    indices = [0, len(trajectory)//4, len(trajectory)//2, len(trajectory)-1]
    
    for i, idx in enumerate(indices):
        img = trajectory[idx]['vision']
        axes[i].imshow(img)
        axes[i].set_title(f"Timestep {idx}")
        axes[i].axis('off')
    
    plt.suptitle("Vision trajectory samples")
    plt.tight_layout()
    plt.show()
    
    return trajectory

# Load your trajectory
trajectory_file = "trajectories/trajectory_YYYYMMDD_HHMMSS.pkl"  # Replace with actual filename
trajectory = load_and_examine_trajectory(trajectory_file)