import pickle
import numpy as np
import matplotlib.pyplot as plt
import glob

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
    
    # Print some sample values
    print(f"\nSample values from first timestep:")
    print(f"End-effector position: {first_step['proprioception']['eef_position']}")
    print(f"Action vector (first 5 values): {first_step['action'][:5]}")
    
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

def examine_all_trajectories():
    """Examine all trajectory files in current directory"""
    trajectory_files = glob.glob("trajectory_*.pkl")
    print(f"Found {len(trajectory_files)} trajectory files:")
    
    for i, file in enumerate(trajectory_files):
        print(f"{i+1}. {file}")
    
    # Load the most recent one (last in alphabetical order)
    if trajectory_files:
        latest_file = sorted(trajectory_files)[-1]
        print(f"\nExamining latest trajectory: {latest_file}")
        return load_and_examine_trajectory(latest_file)
    else:
        print("No trajectory files found!")
        return None

if __name__ == "__main__":
    # Automatically find and examine the latest trajectory
    trajectory = examine_all_trajectories()