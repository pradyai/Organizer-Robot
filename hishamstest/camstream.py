import cv2
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt

stream_url = "http://host.docker.internal:8080"
cap = cv2.VideoCapture(stream_url)

ret, frame = cap.read()
if ret:
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    plt.imshow(frame_rgb)
    plt.axis('off')
    plt.savefig("frame_plot.png")
    print("Saved frame plot as frame_plot.png")
else:
    print("Failed to read frame")

cap.release()