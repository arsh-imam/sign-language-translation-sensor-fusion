import cv2
from vision import get_frame_and_shape, release

print("Starting vision test. Click the window then press Q to quit.")

cv2.namedWindow("Vision Test", cv2.WINDOW_NORMAL)

while True:
    frame, shape = get_frame_and_shape()

    label_color = (0, 255, 0) if shape != "NONE" else (0, 0, 255)
    cv2.putText(
        frame, f"Shape: {shape}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2, label_color, 2
    )

    cv2.imshow("Vision Test", frame)

    key = cv2.waitKey(100)
    if key != -1:
        if key & 0xFF == ord("q"):
            break

cv2.destroyAllWindows()
release()
print("Vision test done.")