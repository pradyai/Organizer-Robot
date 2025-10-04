# dummy_so100_client_minimal.py
import time
import pickle
import grpc
import numpy as np
from lerobot.scripts.server.helpers import TimedObservation
from lerobot.transport import services_pb2, services_pb2_grpc
from lerobot.transport.utils import send_bytes_in_chunks, grpc_channel_options




def make_dummy_so100_observation(timestep: int = 0) -> TimedObservation:
    """
    Build a minimal TimedObservation with cameras and 6 joint positions.
    """
    raw_observation = {
        "observation.images.top": np.zeros((480, 640, 3), dtype=np.uint8),
        "observation.images.side": np.zeros((480, 640, 3), dtype=np.uint8),
        "observation.state": np.zeros(6, dtype=np.float32),
    }
    
    return TimedObservation(
        timestamp=time.time(),
        observation=raw_observation,
        timestep=timestep,
    )


def main():
    server_address = "127.0.0.1:8080"

    # Connect gRPC channel
    channel = grpc.insecure_channel(server_address, grpc_channel_options(initial_backoff="0.033s"))
    stub = services_pb2_grpc.AsyncInferenceStub(channel)

    # Step 1: Handshake
    print("[CLIENT] Sending Ready()")
    stub.Ready(services_pb2.Empty())


    try:
        
        while True:
            # Step 2: Send dummy observation
            obs = make_dummy_so100_observation(timestep=0)
            obs_bytes = pickle.dumps(obs)
            obs_iterator = send_bytes_in_chunks(obs_bytes, services_pb2.Observation, silent=True)
            stub.SendObservations(obs_iterator)
            print("[CLIENT] Dummy observation sent")

            # Step 3: Request actions
            actions_chunk = stub.GetActions(services_pb2.Empty())
            if len(actions_chunk.data) > 0:
                actions = pickle.loads(actions_chunk.data)
                print(f"[CLIENT] Received {len(actions)} actions:")
                for a in actions:
                    print(f"  Timestep {a.get_timestep()} -> {a.get_action()}")
            else:
                print("[CLIENT] No actions received")
                
            time.sleep(0.2)

    except KeyboardInterrupt:
        channel.close()


if __name__ == "__main__":
    main()
