import { useEffect, useState, useCallback } from 'react';
import { auditApi } from '../api/auditApi';
import AuditTable from '../components/AuditTable';
import LoadingSpinner from '../components/LoadingSpinner';
import { compactObject } from '../utils/helpers';
import { DEFAULT_PAGE_SIZE } from '../utils/constants';

export default function AuditLogsPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [total, setTotal] = useState(0);

  // Filters
  const [filters, setFilters] = useState({
    action: '',
    user_id: '',
    limit: DEFAULT_PAGE_SIZE,
    offset: 0,
  });

  const setFilter = (key) => (e) =>
    setFilters((prev) => ({ ...prev, [key]: e.target.value, offset: 0 }));

  const loadLogs = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = compactObject(filters);
      const res = await auditApi.getLogs(params);
      const data = res.data;
      setLogs(data?.logs || data || []);
      setTotal(data?.total || (data?.logs || data || []).length);
    } catch {
      setError('Failed to load audit logs.');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => { loadLogs(); }, [loadLogs]);

  const totalPages = Math.ceil(total / filters.limit);
  const currentPage = Math.floor(filters.offset / filters.limit) + 1;

  const goToPage = (page) =>
    setFilters((prev) => ({ ...prev, offset: (page - 1) * prev.limit }));

  return (
    <div className="page-content">
      <div className="page-header">
        <h1 className="page-title">Audit Logs</h1>
        <p className="page-subtitle">
          Track all user actions and system events
        </p>
      </div>

      {error && <div className="alert alert-error" style={{ marginBottom: 20 }}>{error}</div>}

      {/* Filters */}
      <div
        className="card"
        style={{
          padding: '16px 20px',
          marginBottom: 20,
          display: 'flex',
          gap: 12,
          alignItems: 'flex-end',
          flexWrap: 'wrap',
        }}
      >
        <div className="form-group" style={{ margin: 0, minWidth: 160 }}>
          <label className="form-label" style={{ fontSize: '0.78rem' }}>Action</label>
          <input
            className="form-input"
            placeholder="e.g. LOGIN"
            value={filters.action}
            onChange={setFilter('action')}
          />
        </div>

        <div className="form-group" style={{ margin: 0, minWidth: 160 }}>
          <label className="form-label" style={{ fontSize: '0.78rem' }}>User ID</label>
          <input
            className="form-input"
            placeholder="Filter by user ID"
            value={filters.user_id}
            onChange={setFilter('user_id')}
          />
        </div>

        <div className="form-group" style={{ margin: 0, minWidth: 100 }}>
          <label className="form-label" style={{ fontSize: '0.78rem' }}>Per page</label>
          <select
            className="form-input"
            value={filters.limit}
            onChange={(e) =>
              setFilters((prev) => ({ ...prev, limit: Number(e.target.value), offset: 0 }))
            }
          >
            {[10, 20, 50, 100].map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>

        <button className="btn btn-secondary btn-sm" onClick={loadLogs}>
          🔄 Refresh
        </button>
      </div>

      {/* Table */}
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '60px 0' }}>
          <LoadingSpinner />
        </div>
      ) : (
        <>
          <div style={{ marginBottom: 8, fontSize: '0.85rem', color: 'var(--text2)' }}>
            Showing {logs.length} of {total} records
          </div>
          <AuditTable logs={logs} />

          {/* Pagination */}
          {totalPages > 1 && (
            <div style={{ display: 'flex', gap: 6, marginTop: 16, alignItems: 'center' }}>
              <button
                className="btn btn-sm btn-secondary"
                onClick={() => goToPage(currentPage - 1)}
                disabled={currentPage === 1}
              >
                ← Prev
              </button>
              <span style={{ fontSize: '0.85rem', color: 'var(--text2)' }}>
                Page {currentPage} of {totalPages}
              </span>
              <button
                className="btn btn-sm btn-secondary"
                onClick={() => goToPage(currentPage + 1)}
                disabled={currentPage === totalPages}
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}