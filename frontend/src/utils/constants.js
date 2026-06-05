// ─── App-wide constants ───────────────────────────────────────────────────────

export const APP_NAME = 'DocChat';
export const APP_VERSION = '1.0.0';

// ─── API ─────────────────────────────────────────────────────────────────────

export const API_BASE_URL =
  import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1';

// ─── Roles ───────────────────────────────────────────────────────────────────

export const ROLES = {
  ADMIN: 'admin',
  USER: 'user',
};

// ─── Document status values ───────────────────────────────────────────────────

export const DOC_STATUS = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  READY: 'ready',
  FAILED: 'failed',
};

export const DOC_STATUS_LABEL = {
  [DOC_STATUS.PENDING]: 'Pending',
  [DOC_STATUS.PROCESSING]: 'Processing',
  [DOC_STATUS.READY]: 'Ready',
  [DOC_STATUS.FAILED]: 'Failed',
};

export const DOC_STATUS_BADGE = {
  [DOC_STATUS.PENDING]: 'badge-yellow',
  [DOC_STATUS.PROCESSING]: 'badge-blue',
  [DOC_STATUS.READY]: 'badge-green',
  [DOC_STATUS.FAILED]: 'badge-red',
};

// ─── File upload constraints ──────────────────────────────────────────────────

export const UPLOAD_MAX_SIZE_MB = 50;
export const UPLOAD_MAX_SIZE_BYTES = UPLOAD_MAX_SIZE_MB * 1024 * 1024;
export const UPLOAD_ACCEPTED_TYPES = ['.pdf'];
export const UPLOAD_ACCEPTED_MIME = ['application/pdf'];

// ─── Pagination defaults ──────────────────────────────────────────────────────

export const DEFAULT_PAGE_SIZE = 20;
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

// ─── Chat ─────────────────────────────────────────────────────────────────────

export const CHAT_ROLES = {
  USER: 'user',
  ASSISTANT: 'assistant',
  SYSTEM: 'system',
};

export const MAX_QUESTION_LENGTH = 2000;

// ─── Password policy ──────────────────────────────────────────────────────────

export const PASSWORD_MIN_LENGTH = 8;
export const PASSWORD_RULES = [
  { label: 'At least 8 characters', test: (pw) => pw.length >= 8 },
  { label: 'One uppercase letter', test: (pw) => /[A-Z]/.test(pw) },
  { label: 'One number', test: (pw) => /[0-9]/.test(pw) },
  { label: 'One special character', test: (pw) => /[^A-Za-z0-9]/.test(pw) },
];

// ─── Date/time formatting ─────────────────────────────────────────────────────

export const DATE_FORMAT_OPTIONS = {
  year: 'numeric',
  month: 'short',
  day: 'numeric',
};

export const DATETIME_FORMAT_OPTIONS = {
  year: 'numeric',
  month: 'short',
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
};

// ─── Audit action labels ──────────────────────────────────────────────────────

export const AUDIT_ACTIONS = {
  LOGIN: 'LOGIN',
  LOGOUT: 'LOGOUT',
  REGISTER: 'REGISTER',
  PASSWORD_CHANGE: 'PASSWORD_CHANGE',
  PASSWORD_RESET_REQUEST: 'PASSWORD_RESET_REQUEST',
  PASSWORD_RESET: 'PASSWORD_RESET',
  EMAIL_VERIFY: 'EMAIL_VERIFY',
  DOCUMENT_UPLOAD: 'DOCUMENT_UPLOAD',
  DOCUMENT_DELETE: 'DOCUMENT_DELETE',
  DOCUMENT_REPROCESS: 'DOCUMENT_REPROCESS',
  CHAT_ASK: 'CHAT_ASK',
  SESSION_CREATE: 'SESSION_CREATE',
  SESSION_DELETE: 'SESSION_DELETE',
  USER_ROLE_CHANGE: 'USER_ROLE_CHANGE',
  USER_DELETE: 'USER_DELETE',
};

// ─── Toast / alert types ──────────────────────────────────────────────────────

export const ALERT_TYPES = {
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info',
};

// ─── Local storage keys ───────────────────────────────────────────────────────

export const STORAGE_KEYS = {
  THEME: 'docchat_theme',
  SIDEBAR_COLLAPSED: 'docchat_sidebar_collapsed',
};

// ─── Routes ───────────────────────────────────────────────────────────────────

export const ROUTES = {
  LOGIN: '/login',
  REGISTER: '/register',
  FORGOT_PASSWORD: '/forgot-password',
  RESET_PASSWORD: '/reset-password',
  VERIFY_EMAIL: '/verify-email',
  DASHBOARD: '/dashboard',
  CHAT: '/chat',
  PROFILE: '/profile',
  SETTINGS: '/settings',
  ADMIN: '/admin',
  ADMIN_CHAT: '/admin/chat',
  ADMIN_AUDIT: '/admin/audit',
  NOT_FOUND: '/404',
};