/**
 * CampusResolve frontend API client.
 *
 * Every function here talks to the FastAPI backend over the Fetch API.
 * No data is ever hardcoded here — everything comes from the live API.
 */
const API_BASE = window.CAMPUS_RESOLVE_API_BASE || "http://localhost:8000";

const Session = {
  KEY_TOKEN: "cr_token",
  KEY_ROLE: "cr_role",
  KEY_NAME: "cr_name",

  save(token, role, name) {
    localStorage.setItem(this.KEY_TOKEN, token);
    localStorage.setItem(this.KEY_ROLE, role);
    localStorage.setItem(this.KEY_NAME, name);
  },
  token() {
    return localStorage.getItem(this.KEY_TOKEN);
  },
  role() {
    return localStorage.getItem(this.KEY_ROLE);
  },
  name() {
    return localStorage.getItem(this.KEY_NAME);
  },
  isLoggedIn() {
    return !!this.token();
  },
  clear() {
    localStorage.removeItem(this.KEY_TOKEN);
    localStorage.removeItem(this.KEY_ROLE);
    localStorage.removeItem(this.KEY_NAME);
  },
  requireAuth() {
    if (!this.isLoggedIn()) {
      window.location.href = "login.html";
    }
  },
  requireRole(...roles) {
    this.requireAuth();
    if (!roles.includes(this.role())) {
      window.location.href = "dashboard.html";
    }
  },
  logout() {
    this.clear();
    window.location.href = "login.html";
  },
};

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function apiRequest(path, { method = "GET", body, isForm = false, auth = true } = {}) {
  const headers = {};
  if (!isForm) headers["Content-Type"] = "application/json";
  if (auth && Session.token()) headers["Authorization"] = `Bearer ${Session.token()}`;

  let resp;
  try {
    resp = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body ? (isForm ? body : JSON.stringify(body)) : undefined,
    });
  } catch (networkErr) {
    throw new ApiError(
      "Could not reach the CampusResolve server. Is the backend running?",
      0
    );
  }

  if (resp.status === 401) {
    Session.clear();
    if (!window.location.pathname.endsWith("login.html")) {
      window.location.href = "login.html";
    }
    throw new ApiError("Session expired. Please log in again.", 401);
  }

  let data = null;
  const text = await resp.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch (e) {
      data = null;
    }
  }

  if (!resp.ok) {
    const message = (data && (data.detail || data.message)) || `Request failed (${resp.status})`;
    throw new ApiError(typeof message === "string" ? message : JSON.stringify(message), resp.status);
  }

  return data;
}

const Api = {
  // ---- Auth ----
  register: (payload) => apiRequest("/api/auth/register", { method: "POST", body: payload, auth: false }),
  login: (payload) => apiRequest("/api/auth/login", { method: "POST", body: payload, auth: false }),
  me: () => apiRequest("/api/auth/me"),

  // ---- Users / Profile ----
  getProfile: () => apiRequest("/api/users/me"),
  updateProfile: (payload) => apiRequest("/api/users/me", { method: "PUT", body: payload }),
  changePassword: (payload) => apiRequest("/api/users/me/password", { method: "PUT", body: payload }),
  listUsers: (role) => apiRequest(`/api/users${role ? `?role=${role}` : ""}`),
  createStaff: (payload) => apiRequest("/api/users/staff", { method: "POST", body: payload }),
  deactivateUser: (id) => apiRequest(`/api/users/${id}/deactivate`, { method: "PUT" }),
  activateUser: (id) => apiRequest(`/api/users/${id}/activate`, { method: "PUT" }),

  // ---- Catalog ----
  listDepartments: () => apiRequest("/api/departments"),
  createDepartment: (payload) => apiRequest("/api/departments", { method: "POST", body: payload }),
  listCategories: () => apiRequest("/api/categories"),
  createCategory: (payload) => apiRequest("/api/categories", { method: "POST", body: payload }),
  listStaff: () => apiRequest("/api/staff"),

  // ---- Complaints ----
  createComplaint: (payload) => apiRequest("/api/complaints", { method: "POST", body: payload }),
  listComplaints: (params = {}) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") qs.set(k, v);
    });
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return apiRequest(`/api/complaints${suffix}`);
  },
  getComplaint: (id) => apiRequest(`/api/complaints/${id}`),
  assignComplaint: (id, staffId) =>
    apiRequest(`/api/complaints/${id}/assign`, { method: "PUT", body: { staff_id: staffId } }),
  updateStatus: (id, payload) => apiRequest(`/api/complaints/${id}/status`, { method: "PUT", body: payload }),
  confirmResolution: (id) => apiRequest(`/api/complaints/${id}/confirm`, { method: "PUT" }),
  reopenComplaint: (id, note) =>
    apiRequest(`/api/complaints/${id}/reopen`, { method: "PUT", body: { status: "REOPENED", note } }),
  addComment: (id, message) =>
    apiRequest(`/api/complaints/${id}/comments`, { method: "POST", body: { message } }),
  uploadAttachment: (id, file, kind = "evidence") => {
    const form = new FormData();
    form.append("file", file);
    return apiRequest(`/api/complaints/${id}/attachments?kind=${kind}`, {
      method: "POST",
      body: form,
      isForm: true,
    });
  },

  // ---- Notifications ----
  listNotifications: () => apiRequest("/api/notifications"),
  markNotificationRead: (id) => apiRequest(`/api/notifications/${id}/read`, { method: "PUT" }),
  markAllNotificationsRead: () => apiRequest("/api/notifications/read-all", { method: "PUT" }),

  // ---- Dashboards ----
  studentDashboard: () => apiRequest("/api/dashboard/student"),
  staffDashboard: () => apiRequest("/api/dashboard/staff"),
  adminDashboard: () => apiRequest("/api/dashboard/admin"),
};

// ---------- Toasts ----------
function toast(message, type = "info") {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  container.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

function formatDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" }) +
    " " + d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}

function statusLabel(s) {
  return (s || "").replace(/_/g, " ");
}
