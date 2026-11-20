This is a minimal Next.js frontend scaffold that lets you:

- Pick an image file (input)
- Preview the selected image
- (Optional) Send the image to your backend for processing — configure `BACKEND_URL` in the code
- Download a ZIP containing the original and processed preview (uses `jszip` client-side)

Quick start:

1. cd frontend
2. npm install
3. npm run dev

Notes:
- The page currently simulates processing locally. To wire to an actual backend, update the `processImage()` function in `pages/index.js` to POST to your backend endpoint and return a URL or blob of the processed result.
- Frontend runs on port 3000 by default.
