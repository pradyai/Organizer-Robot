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