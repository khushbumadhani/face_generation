import { useState, useEffect } from 'react'

export default function Home() {
  const [sourceFile, setSourceFile] = useState(null)
  const [sourcePreview, setSourcePreview] = useState(null)
  const [files, setFiles] = useState([])
  const [filesPreviews, setFilesPreviews] = useState([])
  const [processedPreviews, setProcessedPreviews] = useState([])

  const [processing, setProcessing] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [batchProcessedBlobs, setBatchProcessedBlobs] = useState([])
  const [backendUrl, setBackendUrl] = useState('http://localhost:8000')

  useEffect(()=>{
    // set backend URL only on client to avoid SSR/CSR mismatch
    try{
      const env = process.env.NEXT_PUBLIC_BACKEND_URL
      if(env) setBackendUrl(env)
    }catch(e){
      // ignore
    }
  },[])

  function handleSourceChange(e) {
    const f = e.target.files?.[0]
    if (!f) return
    setSourceFile(f)
    setSourcePreview(URL.createObjectURL(f))
  }

  function handleFilesChange(e) {
    const fl = Array.from(e.target.files || [])
    setFiles(fl)
    setFilesPreviews(fl.map(f => URL.createObjectURL(f)))
  }

  function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.style.display = 'none'
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    const event = new MouseEvent('click', {
      view: window,
      bubbles: true,
      cancelable: true,
    })
    a.dispatchEvent(event)
    setTimeout(() => {
      URL.revokeObjectURL(url)
      document.body.removeChild(a)
    }, 1000)
  }

  async function handleDownloadZip() {
    if (!sourceFile) return alert('Select a source image for the face to use')
    if (!files || files.length === 0) return alert('Select one or more images to download')
    setDownloading(true)
    try {
      if (batchProcessedBlobs.length === files.length) {
        const form = new FormData()
        batchProcessedBlobs.forEach(item => form.append('files', item.blob, item.filename))
        const res = await fetch(backendUrl + '/download-batch-raw', { method: 'POST', body: form })
        if (!res.ok) throw new Error('Batch ZIP download failed')
        const blob = await res.blob()
        downloadBlob(blob, 'processed_batch.zip')
        return
      }

      const form = new FormData()
      form.append('source', sourceFile)
      files.forEach(f => form.append('files', f))
      const res = await fetch(backendUrl + '/process-batch', { method: 'POST', body: form })
      if (!res.ok) throw new Error('Batch ZIP download failed')
      const blob = await res.blob()
      downloadBlob(blob, 'processed_batch.zip')
    } catch (err) {
      console.error(err)
      alert('Batch ZIP download failed: ' + err.message)
    } finally {
      setDownloading(false)
    }
  }

  function dataUrlToBlob(dataUrl) {
    const [header, base64] = dataUrl.split(',')
    const mime = header.match(/:(.*?);/)[1]
    const bytes = atob(base64)
    const array = new Uint8Array(bytes.length)
    for (let i = 0; i < bytes.length; i++) array[i] = bytes.charCodeAt(i)
    return new Blob([array], { type: mime })
  }

  async function handleBatchProcess() {
    if (!sourceFile) return alert('Select a source image for the face to use')
    if (!files || files.length === 0) return alert('Select one or more images to process')
    try {
      setProcessing(true)
      const form = new FormData()
      form.append('source', sourceFile)
      files.forEach(f => form.append('files', f))
      const res = await fetch(backendUrl + '/process-batch-preview', { method: 'POST', body: form })
      if (!res.ok) throw new Error('Batch processing failed')
      const data = await res.json()
      setProcessedPreviews(data)
      setBatchProcessedBlobs(data.map(item => ({ filename: item.filename, blob: dataUrlToBlob(item.image) })))
    } catch (err) {
      console.error(err)
      alert('Batch processing failed: ' + err.message)
    } finally {
      setProcessing(false)
    }
  }

  async function handleBatchDownloadZip() {
    if (!sourceFile) return alert('Select a source image for the face to use')
    if (!files || files.length === 0) return alert('Select one or more images to download')
    setDownloading(true)
    try {
      if (batchProcessedBlobs.length === files.length) {
        const form = new FormData()
        batchProcessedBlobs.forEach(item => form.append('files', item.blob, item.filename))
        const res = await fetch(backendUrl + '/download-batch-raw', { method: 'POST', body: form })
        if (!res.ok) throw new Error('Batch ZIP download failed')
        const blob = await res.blob()
        downloadBlob(blob, 'processed_batch.zip')
        return
      }

      const form = new FormData()
      form.append('source', sourceFile)
      files.forEach(f => form.append('files', f))
      const res = await fetch(backendUrl + '/process-batch', { method: 'POST', body: form })
      if (!res.ok) throw new Error('Batch ZIP download failed')
      const blob = await res.blob()
      downloadBlob(blob, 'processed_batch.zip')
    } catch (err) {
      console.error(err)
      alert('Batch ZIP download failed: ' + err.message)
    } finally {
      setDownloading(false)
    }
  }

  return (
    <main className="container">
      <div className="header">
        <div>
          <div className="title">Face Generation</div>
          <div className="sub">Upload images, preview results and download processed outputs</div>
        </div>
       
      </div>

      <div className="grid">
        <div>
          <div className="panel">
            <div className="controls">
              <div style={{display:'flex',gap:12}}>
                <div>
                  <div className="sub">Source image</div>
                  <div className="notes" style={{marginBottom:8}}>Upload the face you want to use for swapping into all target images.</div>
                  <input type="file" accept="image/*" onChange={handleSourceChange} />
                </div>
                <div>
                  <div className="sub">Target images</div>
                  <div className="notes" style={{marginBottom:8}}>Upload the images whose faces should be replaced by the source face.</div>
                  <input type="file" accept="image/*" multiple onChange={handleFilesChange} />
                </div>
              </div>
            </div>
          </div>
        </div>

        <aside>
          <div className="panel">
            <h3 style={{marginTop:0}}>Actions</h3>
            <div style={{marginTop:12}} className="actions">
              <>
                <button type="button" className="btn" onClick={handleBatchProcess} disabled={processing || !sourceFile || files.length===0}>{processing ? 'Processing...' : 'Generate Preview'}</button>
                <button type="button" className="ghost" onClick={handleBatchDownloadZip} disabled={downloading || !sourceFile || files.length===0}>{downloading ? 'Downloading...' : 'Download ZIP'}</button>
              </>
            </div>
          </div>
        </aside>

        <div className="panel preview-panel" style={{marginTop:12}}>
          <h3 style={{margin:'0 0 8px 0'}}>Preview</h3>
          <div className="preview">
            {filesPreviews.length > 0 && (
              <div style={{display:'grid',gap:16}}>
                {sourcePreview && (
                  <div>
                    <div className="sub">Source</div>
                    <img src={sourcePreview} alt="source" className="file-thumb" />
                  </div>
                )}
                {filesPreviews.length > 0 && (
                  <div className="batch-results-grid">
                    <div className="sub">Batch results</div>
                    <div className="batch-cards">
                      {filesPreviews.map((previewUrl, i) => (
                        <div key={i} className="batch-card">
                          <div className="batch-card-column">
                            <div className="batch-card-title">Actual</div>
                            <img src={previewUrl} alt={`input-${i}`} className="file-thumb" />
                            <div className="file-label">{files[i]?.name || `input-${i}`}</div>
                          </div>
                          <div className="batch-card-column">
                            <div className="batch-card-title">Processed</div>
                            {processedPreviews[i] ? (
                              <>
                                <img src={processedPreviews[i].image} alt={`output-${i}`} className="file-thumb" />
                                <div className="file-label">{processedPreviews[i].filename}</div>
                              </>
                            ) : (
                              <div className="notes">Run batch process to show output.</div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="footer">Built with InsightFace + FastAPI — first request may take longer while models load.</div>
    </main>
  )
}
