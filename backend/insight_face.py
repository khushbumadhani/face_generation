import os
import cv2
import insightface

from insightface.app import FaceAnalysis
from insightface.model_zoo import get_model

INPUT_DIR = "001"
OUTPUT_DIR = "001_output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

app = FaceAnalysis(name='buffalo_l')
app.prepare(ctx_id=-1)

swapper = get_model(
    'inswapper_128.onnx',
    download=False
)

source_img = cv2.imread("source.jpg")
# fallback: try first valid image in INPUT_DIR
if source_img is None:
    for f in os.listdir(INPUT_DIR):
        if f.lower().endswith(('.jpg', '.jpeg', '.png')):
            candidate = os.path.join(INPUT_DIR, f)
            source_img = cv2.imread(candidate)
            if source_img is not None:
                print(f"Using '{candidate}' as source image fallback.")
                break

if source_img is None:
    raise SystemExit(
        "Source image 'girl_model.jpg' not found and no valid images in INPUT_DIR.\n"
        "Place a source image named 'girl_model.jpg' next to the script or add an image to the INPUT_DIR."
    )

# ensure a face is detected in the source image
source_faces = app.get(source_img)
if not source_faces:
    raise SystemExit("No face detected in the source image. Use a different source image.")

source_face = source_faces[0]

for file in os.listdir(INPUT_DIR):

    if not file.lower().endswith(
        ('.jpg', '.jpeg', '.png')
    ):
        continue

    path = os.path.join(INPUT_DIR, file)

    img = cv2.imread(path)
    if img is None:
        print(f"Warning: failed to read '{path}', skipping.")
        continue

    faces = app.get(img)

    result = img.copy()

    if not faces:
        print(f"No faces found in '{file}', saving original (resized).")
    else:
        for face in faces:
            result = swapper.get(
                result,
                face,
                source_face,
                paste_back=True
            )

    output_path = os.path.join(
        OUTPUT_DIR,
        file
    )
    result = cv2.resize(
    result,
    (1500, 2000),
    interpolation=cv2.INTER_AREA
)
    cv2.imwrite(output_path, result)

    print(f"Processed {file}")

print("All images completed.")