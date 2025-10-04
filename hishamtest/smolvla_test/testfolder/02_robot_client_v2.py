# Copyright 2025 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Example command:
```shell
python src/lerobot/scripts/server/robot_client.py \
    --robot.type=so100_follower \
    --robot.port=/dev/tty.usbmodem58760431541 \ #NOOOOO
    --robot.cameras="{ front: {type: opencv, index_or_path: 0, width: 1920, height: 1080, fps: 30}}" \
    --robot.id=black \
    --task="dummy" \
    --server_address=127.0.0.1:8080 \
    --policy_type=act \
    --pretrained_name_or_path=user/model \
    --policy_device=mps \
    --actions_per_chunk=50 \
    --chunk_size_threshold=0.5 \
    --aggregate_fn_name=weighted_average \
    --debug_visualize_queue_size=True
```
"""

import logging
import pickle  # nosec
import threading
import time
from collections.abc import Callable
from dataclasses import asdict
from pprint import pformat
from queue import Queue
from typing import Any
import numpy as np

import draccus
import grpc
import torch

from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig  # noqa: F401
from lerobot.cameras.realsense.configuration_realsense import RealSenseCameraConfig  # noqa: F401
from lerobot.configs.policies import PreTrainedConfig
from lerobot.robots import (  # noqa: F401
    Robot,
    RobotConfig,
    koch_follower,
    make_robot_from_config,
    so100_follower,
    so101_follower,
)
from lerobot.scripts.server.configs import RobotClientConfig
from lerobot.scripts.server.constants import SUPPORTED_ROBOTS
from lerobot.scripts.server.helpers import (
    Action,
    FPSTracker,
    Observation,
    RawObservation,
    RemotePolicyConfig,
    TimedAction,
    TimedObservation,
    get_logger,
    map_robot_keys_to_lerobot_features,
    validate_robot_cameras_for_policy,
    visualize_action_queue_size,
)
from lerobot.transport import (
    services_pb2,  # type: ignore
    services_pb2_grpc,  # type: ignore
)
from lerobot.transport.utils import grpc_channel_options, send_bytes_in_chunks


class RobotClient:
    logger = get_logger("robot_client")

    def __init__(self, config: RobotClientConfig):
        self.config = config
        self.robot = make_robot_from_config(config.robot)

        # Map robot features for policy
        features = map_robot_keys_to_lerobot_features(self.robot)
        self.policy_config = RemotePolicyConfig(
            config.policy_type, "", features, config.actions_per_chunk, "cpu"
        )

        # gRPC client setup
        self.channel = grpc.insecure_channel(
            config.server_address,
            grpc_channel_options(initial_backoff=f"{config.environment_dt:.4f}s"),
        )
        self.stub = services_pb2_grpc.AsyncInferenceStub(self.channel)

        self.shutdown_event = threading.Event()
        self.action_queue = Queue()
        self.action_lock = threading.Lock()

    @property
    def running(self):
        return not self.shutdown_event.is_set()

    def start(self):
        """Connect to the server and send policy configuration"""
        try:
            self.stub.Ready(services_pb2.Empty())
            policy_bytes = pickle.dumps(self.policy_config)
            self.stub.SendPolicyInstructions(services_pb2.PolicySetup(data=policy_bytes))
            self.shutdown_event.clear()
            return True
        except grpc.RpcError as e:
            self.logger.error(f"Failed to connect: {e}")
            return False

    def stop(self):
        self.shutdown_event.set()
        self.channel.close()

    def send_observation(self, obs: TimedObservation):
        """Send preprocessed observation to server"""
        obs_bytes = pickle.dumps(obs)
        obs_iter = send_bytes_in_chunks(obs_bytes, services_pb2.Observation)
        self.stub.SendObservations(obs_iter)

    def receive_actions(self):
        """Continuously receive actions from server"""
        while self.running:
            try:
                chunk = self.stub.GetActions(services_pb2.Empty())
                if chunk.data:
                    actions: list[TimedAction] = pickle.loads(chunk.data)
                    with self.action_lock:
                        for a in actions:
                            self.action_queue.put(a)
            except grpc.RpcError as e:
                self.logger.error(f"Error receiving actions: {e}")

    def apply_actions(self):
        """Apply actions in the queue to the robot"""
        with self.action_lock:
            while not self.action_queue.empty():
                action: TimedAction = self.action_queue.get_nowait()
                tensor = action.get_action()
                action_dict = {k: tensor[i].item() for i, k in enumerate(self.robot.action_features)}
                self.robot.send_action(action_dict)

    def preprocess_observation(self) -> TimedObservation:
        """Preprocess raw robot state into TimedObservation"""
        raw_obs: RawObservation = {
            "observation.images.top": np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8),
            "observation.images.side": np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8),
            "observation.state": np.random.rand(6).astype(np.float32),
            "task": self.config.task,
        }
        latest_timestep = 0  # could be from last action if desired
        return TimedObservation(timestamp=time.time(), observation=raw_obs, timestep=latest_timestep)

    def run(self):
        """Main loop: send observation -> receive actions -> apply"""
        action_thread = threading.Thread(target=self.receive_actions, daemon=True)
        action_thread.start()

        while self.running:
            obs = self.preprocess_observation()
            self.send_observation(obs)
            self.apply_actions()
            time.sleep(self.config.environment_dt)  # maintain loop rate

        self.stop()
        action_thread.join()


def async_client(cfg: RobotClientConfig):
    client = RobotClient(cfg)
    if client.start():
        client.run()


if __name__ == "__main__":
    import argparse
    from lerobot.robots import RobotConfig

    parser = argparse.ArgumentParser()
    parser.add_argument("--robot.type", required=True)
    parser.add_argument("--robot.port", required=True)
    parser.add_argument("--robot.id", required=True)
    parser.add_argument("--task", default="dummy")
    parser.add_argument("--server_address", required=True)
    parser.add_argument("--policy_type", required=True)
    parser.add_argument("--pretrained_name_or_path", default="")
    parser.add_argument("--actions_per_chunk", type=int, default=50)
    parser.add_argument("--environment_dt", type=float, default=0.05)
    args = parser.parse_args()

    robot_cfg = RobotConfig(
        type=args.robot.type,
        port=args.robot.port,
        id=args.robot_id,
        cameras={}  # optional: fill in if needed
    )

    cfg = RobotClientConfig(
        policy_type=args.policy_type,
        pretrained_name_or_path=args.pretrained_name_or_path,
        robot=robot_cfg,
        actions_per_chunk=args.actions_per_chunk,
        server_address=args.server_address,
        task=args.task,
        environment_dt=args.environment_dt,
    )

    async_client(cfg)
