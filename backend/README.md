FastAPI backend for face-generation frontend

Endpoints:
- POST /process : accepts `file` form field, returns processed image (PNG)
- POST /download-zip : accepts `file` form field, returns ZIP containing original and processed image
 - POST /process-batch : accepts a `source` image and multiple `files` form fields, returns a ZIP containing originals and processed images
 - POST /process-batch : accepts a `source` image and multiple `files` form fields, returns a ZIP containing processed images (each file in the ZIP uses the same filename as the corresponding input)

Run locally:

```bash
cd backend
python -m pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
