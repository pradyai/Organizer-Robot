# Organizer-Robot
# Project Environment with Docker - smolVLA

1. Build the Docker container in the `testfolder` directory:

```bash
docker build -t smolvla_img .
```
2. Run the container and mount the `testfolder` repository inside the container:

```bash
docker run --rm -it --network=host \
  -v $(pwd)/testfolder:/app/testfolder \
  smolvla_img
``` 

3. Then, you can run three scripts: loading, training and evaluating smolVLA. You need to be inside `hishamstest/smolvla_test` (currently only for testing):

```bash
python testfolder/load_smolvla.py
python testfolder/train_smolvla.py
python testfolder/eval_smolvla.py
```

4. To run the socketserver version which publishes a tensor every 10 seconds (probe) you need two terminals and run these two scripts (first the eval, then wait until server connection, then the second):

```bash
python testfolder/eval_smolvla_socket.py
python testfolder/testclient.py
``` 

5. To spin up the smolvla evaluation server:

```bash
python testfolder/00_server_eval_smolvla_v2.py 
```

test it with:

```bash
python python testfolder/00_client_sendactionreq_v1.py 
```

6. To run the actual PolicyServer:

```bash
PYTHONPATH=/app/src python -m testfolder.01_policy_server_v1     --host=127.0.0.1     --port=8080     --fps=30     --inference_latency=0.033     --obs_queue_timeout=1
```

