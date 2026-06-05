import { useState, useRef } from 'react';
import { adminApi } from '../api/adminApi';

export default function UploadForm({ onSuccess }) {
  const [title, setTitle]     = useState('');
  const [desc, setDesc]       = useState('');
  const [file, setFile]       = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState('');
  const fileRef = useRef();

  const submit = async (e) => {
    e.preventDefault();
    if (!file || !title.trim()) { setError('Title and file are required.'); return; }
    setError(''); setLoading(true);
    try {
      const fd = new FormData();
      fd.append('title', title);
      fd.append('description', desc);
      fd.append('file', file);
      await adminApi.uploadDocument(fd);
      setTitle(''); setDesc(''); setFile(null);
      if (fileRef.current) fileRef.current.value = '';
      onSuccess?.();
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed');
    }
    setLoading(false);
  };

  return (
    <form onSubmit={submit} className="flex-col gap-3">
      {error && <div className="alert alert-error">{error}</div>}
      <div className="form-group">
        <label className="form-label">Document Title *</label>
        <input className="form-input" value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g. Company Policy 2024" />
      </div>
      <div className="form-group">
        <label className="form-label">Description</label>
        <input className="form-input" value={desc} onChange={e => setDesc(e.target.value)} placeholder="Optional description" />
      </div>
      <div className="form-group">
        <label className="form-label">PDF File *</label>
        <input ref={fileRef} className="form-input" type="file" accept=".pdf" onChange={e => setFile(e.target.files[0])} />
        <span className="form-hint">PDF only, max 50MB</span>
      </div>
      <button className="btn btn-primary" type="submit" disabled={loading}>
        {loading ? 'Uploading...' : 'Upload Document'}
      </button>
    </form>
  );
}