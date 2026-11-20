from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import base64
import io
import zipfile
from typing import List
from face_generation.backend.pipeline import _init_models, process_image_with_insight

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event('startup')
async def startup_event():
    # Model initialization is deferred to the first processing request.
    # This prevents a slow model download from blocking Uvicorn/port 8000.
    pass


def _map_ext_to_format(ext: str) -> str:
    if not ext:
        return 'PNG'
    ext = ext.lower()
    if ext in ('jpg', 'jpeg'):
        return 'JPEG'
    if ext == 'png':
        return 'PNG'
    return 'PNG'


def process_image_bytes(data: bytes, out_format: str = 'PNG') -> bytes:
    # simple processing: open image and resize to max 1024 preserving aspect
    with Image.open(io.BytesIO(data)) as im:
        im = im.convert('RGB')
        max_size = (1024, 1024)
        im.thumbnail(max_size)
        out = io.BytesIO()
        im.save(out, format=out_format)
        out.seek(0)
        return out.read()


@app.post('/process')
async def process(file: UploadFile = File(...)):
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail='Empty file')
    processed = process_image_bytes(contents)
    return StreamingResponse(io.BytesIO(processed), media_type='image/png')


@app.post('/download-zip')
async def download_zip(file: UploadFile = File(...)):
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail='Empty file')

    # use insightface pipeline to process and return processed image with same filename
    ext = file.filename.rsplit('.', 1)[1] if '.' in file.filename else 'png'
    out_ext = ext.lower()
    try:
        processed = process_image_with_insight(contents, source_bytes=None, out_ext=out_ext)
    except Exception:
        # fallback to simple processing if insightface fails
        processed = process_image_bytes(contents, out_format='PNG')

    mem = io.BytesIO()
    with zipfile.ZipFile(mem, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(file.filename, processed)
    mem.seek(0)
    return StreamingResponse(mem, media_type='application/zip', headers={
        'Content-Disposition': 'attachment; filename=images.zip'
    })


@app.post('/download-zip-raw')
async def download_zip_raw(file: UploadFile = File(...)):
    contents = await file.read()    
    if not contents:
        raise HTTPException(status_code=400, detail='Empty file')

    mem = io.BytesIO()
    with zipfile.ZipFile(mem, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(file.filename, contents)
    mem.seek(0)
    return StreamingResponse(mem, media_type='application/zip', headers={
        'Content-Disposition': 'attachment; filename=images.zip'
    })


@app.post('/process-batch')
async def process_batch(source: UploadFile = File(...), files: List[UploadFile] = File(...)):
    """Process multiple files using a provided source image.

    Expects form fields:
    - source: single upload (source face image)
    - files: multiple uploads (images to process)

    Returns a ZIP containing original and processed images.
    """
    if not files:
        raise HTTPException(status_code=400, detail='No files provided')

    # read source and pass to pipeline
    source_bytes = await source.read()

    mem = io.BytesIO()
    with zipfile.ZipFile(mem, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            contents = await f.read()
            if not contents:
                continue
            ext = f.filename.rsplit('.', 1)[1] if '.' in f.filename else 'png'
            out_ext = ext.lower()
            try:
                processed = process_image_with_insight(contents, source_bytes=source_bytes, out_ext=out_ext)
            except Exception:
                processed = process_image_bytes(contents, out_format='PNG')
            zf.writestr(f.filename, processed)

    mem.seek(0)
    return StreamingResponse(mem, media_type='application/zip', headers={
        'Content-Disposition': 'attachment; filename=processed_batch.zip'
    })


@app.post('/download-batch-raw')
async def download_batch_raw(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail='No files provided')

    mem = io.BytesIO()
    with zipfile.ZipFile(mem, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            contents = await f.read()
            if not contents:
                continue
            zf.writestr(f.filename, contents)
    mem.seek(0)
    return StreamingResponse(mem, media_type='application/zip', headers={
        'Content-Disposition': 'attachment; filename=processed_batch.zip'
    })


@app.post('/process-batch-preview')
async def process_batch_preview(source: UploadFile = File(...), files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail='No files provided')

    source_bytes = await source.read()
    results = []

    for f in files:
        contents = await f.read()
        if not contents:
            continue
        ext = f.filename.rsplit('.', 1)[1] if '.' in f.filename else 'png'
        out_ext = ext.lower()
        try:
            processed = process_image_with_insight(contents, source_bytes=source_bytes, out_ext=out_ext)
        except Exception:
            processed = process_image_bytes(contents, out_format='PNG')
            out_ext = 'png'

        encoded = base64.b64encode(processed).decode('ascii')
        mime_type = 'image/png' if out_ext == 'png' else 'image/jpeg'
        results.append({
            'filename': f.filename,
            'image': f'data:{mime_type};base64,{encoded}'
        })

    return results
