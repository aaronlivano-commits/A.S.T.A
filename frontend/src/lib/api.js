// Thin fetch wrapper for talking to the FastAPI backend through the Vite proxy.
//
//   - All paths are relative to `/api/v1` (Vite proxies those to localhost:8000).
//   - When a Firebase user is signed in, we attach the ID token as a Bearer header.
//   - Callers can override the base path or skip auth (e.g. for /auth/verify or /health).
//
// Usage:
//   const topics = await api.get("/topics");
//   const saved = await api.post("/topics", { title: "Biochem" });
//   await api.upload("/training/text", "file", datasetFile);

import { auth } from "@/firebase/config";

const API_BASE = "/api/v1";

class ApiError extends Error {
  constructor(message, { status, body } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

async function authHeader() {
  const user = auth.currentUser;
  if (!user) return {};
  // Firebase always returns a fresh, signed ID token here.
  const token = await user.getIdToken();
  return { Authorization: `Bearer ${token}` };
}

async function request(path, { method = "GET", body, headers, signal } = {}) {
  const url = path.startsWith("http") ? path : `${API_BASE}${path}`;
  const finalHeaders = { ...(await authHeader()), ...(headers || {}) };

  // Let the browser set Content-Type for FormData (so the multipart boundary is added).
  if (body && !(body instanceof FormData)) {
    finalHeaders["Content-Type"] = finalHeaders["Content-Type"] || "application/json";
  }

  let res;
  try {
    res = await fetch(url, { method, body, headers: finalHeaders, signal });
  } catch (networkErr) {
    throw new ApiError(`Network error calling ${url}: ${networkErr.message}`);
  }

  if (res.status === 204) return null;

  const contentType = res.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await res.json() : await res.text();

  if (!res.ok) {
    const detail =
      payload && typeof payload === "object" && payload.detail
        ? payload.detail
        : `Request failed (${res.status})`;
    throw new ApiError(detail, { status: res.status, body: payload });
  }
  return payload;
}

async function get(path, opts) {
  return request(path, { ...opts, method: "GET" });
}

async function post(path, body, opts) {
  const serialized =
    body instanceof FormData
      ? body
      : body !== undefined && body !== null
      ? JSON.stringify(body)
      : undefined;
  return request(path, { ...opts, method: "POST", body: serialized });
}

async function patch(path, body, opts) {
  return request(path, {
    ...opts,
    method: "PATCH",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
}

async function del(path, opts) {
  return request(path, { ...opts, method: "DELETE" });
}

// Multipart upload helper: appends a single file under `fieldName`.
function upload(path, fieldName, file, extraFields = {}) {
  const fd = new FormData();
  fd.append(fieldName, file);
  for (const [k, v] of Object.entries(extraFields)) {
    fd.append(k, v);
  }
  return post(path, fd);
}

// Subscribe to an SSE event stream. `handlers` is { eventName: cb }.
// Returns an unsubscribe function.
async function streamSse(path, payload, handlers = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(await authHeader()) },
    body: JSON.stringify(payload),
  });
  if (!res.ok || !res.body) {
    throw new ApiError(`Stream failed (${res.status})`, { status: res.status });
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const dispatch = (eventName, data) => {
    const cb = handlers[eventName];
    if (cb) cb(data);
  };

  // Read the response in a background loop; expose stop() via the returned function.
  let stopped = false;
  (async () => {
    while (!stopped) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // SSE frames are separated by blank lines; events by newlines.
      let sep;
      while ((sep = buffer.indexOf("\n\n")) !== -1) {
        const frame = buffer.slice(0, sep);
        buffer = buffer.slice(sep + 2);
        const lines = frame.split("\n");
        let name = "message";
        let dataLines = [];
        for (const line of lines) {
          if (line.startsWith("event:")) name = line.slice(6).trim();
          else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
        }
        if (!dataLines.length) continue;
        const raw = dataLines.join("\n");
        let parsed = raw;
        try {
          parsed = JSON.parse(raw);
        } catch {
          /* keep as string */
        }
        dispatch(name, parsed);
      }
    }
  })();

  return () => {
    stopped = true;
    reader.cancel().catch(() => {});
  };
}

export const api = {
  ApiError,
  get,
  post,
  patch,
  del,
  upload,
  streamSse,
};

export default api;
