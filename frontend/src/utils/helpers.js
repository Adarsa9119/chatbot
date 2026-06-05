import {
  DATE_FORMAT_OPTIONS,
  DATETIME_FORMAT_OPTIONS,
  UPLOAD_MAX_SIZE_BYTES,
  UPLOAD_ACCEPTED_MIME,
  PASSWORD_RULES,
} from './constants';

// ─── Date helpers ─────────────────────────────────────────────────────────────

/**
 * Format an ISO date string or Date to a readable date.
 * @param {string|Date} date
 * @returns {string}
 */
export const formatDate = (date) => {
  if (!date) return '—';
  try {
    return new Date(date).toLocaleDateString(undefined, DATE_FORMAT_OPTIONS);
  } catch {
    return String(date);
  }
};

/**
 * Format an ISO date string or Date to a readable date+time.
 * @param {string|Date} date
 * @returns {string}
 */
export const formatDateTime = (date) => {
  if (!date) return '—';
  try {
    return new Date(date).toLocaleString(undefined, DATETIME_FORMAT_OPTIONS);
  } catch {
    return String(date);
  }
};

/**
 * Human-readable relative time (e.g. "3 minutes ago").
 * @param {string|Date} date
 * @returns {string}
 */
export const timeAgo = (date) => {
  if (!date) return '—';
  const diff = Date.now() - new Date(date).getTime();
  const seconds = Math.floor(diff / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return formatDate(date);
};

// ─── File helpers ─────────────────────────────────────────────────────────────

/**
 * Format bytes to a human-readable file size string.
 * @param {number} bytes
 * @returns {string}
 */
export const formatFileSize = (bytes) => {
  if (!bytes && bytes !== 0) return '—';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
};

/**
 * Validate a file before upload.
 * Returns an error string or null if valid.
 * @param {File} file
 * @returns {string|null}
 */
export const validateUploadFile = (file) => {
  if (!file) return 'No file selected.';
  if (!UPLOAD_ACCEPTED_MIME.includes(file.type)) {
    return 'Only PDF files are accepted.';
  }
  if (file.size > UPLOAD_MAX_SIZE_BYTES) {
    return `File is too large. Maximum size is ${UPLOAD_MAX_SIZE_BYTES / (1024 * 1024)} MB.`;
  }
  return null;
};

// ─── String helpers ───────────────────────────────────────────────────────────

/**
 * Truncate a string to a max length with ellipsis.
 * @param {string} str
 * @param {number} maxLen
 * @returns {string}
 */
export const truncate = (str, maxLen = 80) => {
  if (!str) return '';
  return str.length > maxLen ? str.slice(0, maxLen) + '…' : str;
};

/**
 * Capitalize the first letter of a string.
 * @param {string} str
 * @returns {string}
 */
export const capitalize = (str) => {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
};

/**
 * Return initials from a name string (e.g. "John Doe" → "JD").
 * @param {string} name
 * @returns {string}
 */
export const getInitials = (name) => {
  if (!name) return '?';
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join('');
};

// ─── Password helpers ─────────────────────────────────────────────────────────

/**
 * Check all password rules and return an array of { label, met } objects.
 * @param {string} password
 * @returns {{ label: string, met: boolean }[]}
 */
export const checkPasswordStrength = (password) =>
  PASSWORD_RULES.map((rule) => ({ label: rule.label, met: rule.test(password) }));

/**
 * Return 0-4 strength score for a password.
 * @param {string} password
 * @returns {number}
 */
export const passwordStrengthScore = (password) =>
  PASSWORD_RULES.filter((rule) => rule.test(password)).length;

// ─── API error helpers ────────────────────────────────────────────────────────

/**
 * Extract a user-friendly error message from an Axios error response.
 * @param {any} err - Axios error
 * @param {string} fallback - default message
 * @returns {string}
 */
export const extractApiError = (err, fallback = 'An unexpected error occurred.') => {
  const detail = err?.response?.data?.detail;
  if (!detail) return fallback;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg || String(d)).join(', ');
  return fallback;
};

// ─── Object helpers ───────────────────────────────────────────────────────────

/**
 * Remove keys with undefined/null values from an object.
 * Useful for building query param objects.
 * @param {object} obj
 * @returns {object}
 */
export const compactObject = (obj) =>
  Object.fromEntries(
    Object.entries(obj).filter(([, v]) => v !== undefined && v !== null && v !== '')
  );

/**
 * Build a URLSearchParams string from an object (skipping empty values).
 * @param {object} params
 * @returns {string}
 */
export const buildQueryString = (params) => {
  const clean = compactObject(params);
  return new URLSearchParams(clean).toString();
};

// ─── UI helpers ───────────────────────────────────────────────────────────────

/**
 * Scroll an element into view smoothly.
 * @param {React.RefObject} ref
 */
export const scrollToBottom = (ref) => {
  ref?.current?.scrollIntoView({ behavior: 'smooth' });
};

/**
 * Copy text to clipboard. Returns true on success.
 * @param {string} text
 * @returns {Promise<boolean>}
 */
export const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
};

/**
 * Download a JSON object as a .json file.
 * @param {object} data
 * @param {string} filename
 */
export const downloadJSON = (data, filename = 'export.json') => {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
};