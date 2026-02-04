# Thresholds and landmark indices (MediaPipe 468-point model)
EAR_THRESHOLD = 0.21
BLINK_FRAMES_REQUIRED = 2
PUPIL_MOVE_THRESHOLD = 2.0
IRIS_EDGE_THRESHOLD = 0.12
LIVELINESS_REQUIRED = 2

# Eye landmarks (6-point EAR)
left_eye = [33, 160, 158, 133, 153, 144]
right_eye = [263, 387, 385, 362, 380, 373]

# Approx iris perimeter landmarks (468-model compatible)
left_iris_approx = [159, 145, 153, 154]
right_iris_approx = [386, 374, 380, 381]
