import cv2

cap = cv2.VideoCapture(0)
ret, frame = cap.read()
cap.release()

if ret:
    cv2.imwrite("frame_plot.jpg", frame)
    print("Frame saved as frame.jpg")
else:
    print("Failed to capture frame")
