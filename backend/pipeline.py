import io
import os
import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis
from insightface.model_zoo import get_model

_app = None
_swapper = None


def _init_models():
    global _app, _swapper
    if _app is None:
        _app = FaceAnalysis(name='buffalo_l')
        _app.prepare(ctx_id=-1)
    if _swapper is None:
        _swapper = get_model('inswapper_128.onnx', download=False)


def _read_image_bytes(data: bytes):
    arr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img


def _encode_image(img, ext='png'):
    ok, buf = cv2.imencode('.' + ext, img)
    if not ok:
        raise RuntimeError('Failed to encode image')
    return buf.tobytes()


def process_image_with_insight(target_bytes: bytes, source_bytes: bytes | None = None, out_ext: str = 'png') -> bytes:
    """Process a target image bytes using insightface face swap with the provided source image bytes.

    Returns processed image bytes encoded with extension `out_ext`.
    """
    _init_models()

    target_img = _read_image_bytes(target_bytes)
    if target_img is None:
        raise ValueError('Invalid target image')

    # determine source face
    if source_bytes:
        src_img = _read_image_bytes(source_bytes)
    else:
        # try to load a local 'source.jpg' if exists
        if os.path.exists('source.jpg'):
            src_img = cv2.imread('source.jpg')
        else:
            src_img = None

    source_face = None
    if src_img is not None:
        src_faces = _app.get(src_img)
        if src_faces:
            source_face = src_faces[0]

    result = target_img.copy()

    faces = _app.get(target_img)
    if faces and source_face is not None:
        for face in faces:
            result = _swapper.get(result, face, source_face, paste_back=True)

    # encode result
    return _encode_image(result, ext=out_ext)
