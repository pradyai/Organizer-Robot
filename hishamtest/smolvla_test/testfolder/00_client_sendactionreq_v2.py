import socket
import pickle
import torch
import time
from lerobot.scripts.server.helpers import TimedObservation


HOST = "127.0.0.1"
PORT = 6006

# Dummy batch
batch_size = 1
img_shape = (3, 512, 512)
state_dim = 6

#from here ------

dummy_obs_dict = {
    "observation.images.top": torch.rand(batch_size, *img_shape), #here, put the actual camera observation
    "observation.images.wrist": torch.rand(batch_size, *img_shape),  
    "observation.state": torch.rand(batch_size, state_dim)          
}

# Wrap in TimedObservation
timed_obs = TimedObservation(
    timestamp=time.time(),
    observation=dummy_obs_dict,
    timestep=0,
)

# Connect to server
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))
print("[Client] Connected")

# Serialize and send
msg = pickle.dumps(timed_obs)
sock.sendall(len(msg).to_bytes(4, "big") + msg)

# Receive response
raw_len = sock.recv(4)
if not raw_len:
    raise RuntimeError("Server closed connection")
msg_len = int.from_bytes(raw_len, "big")

data = b""
while len(data) < msg_len:
    chunk = sock.recv(msg_len - len(data))
    if not chunk:
        raise RuntimeError("Server closed connection during data transfer")
    data += chunk

actions = pickle.loads(data)
print("[Client] Received actions:", actions)
print(actions.shape)

sock.close()
