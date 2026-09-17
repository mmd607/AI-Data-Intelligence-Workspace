/**
 * Shared HTTP plumbing for every domain module in `api-client/`. This is the only file
 * that calls `fetch` — every domain module (`datasets.ts`, `profiling.ts`, `ml.ts`,
 * `ai.ts`) goes through `request()` here, which is itself only ever imported from within
 * `api-client/`, per 02_DOCS/ARCHITECTURE.md "Module Boundaries" ("no component may call
 * the backend directly — all network access goes through a single typed API-client
 * module").
 */

export const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

/**
 * A failed API call — either a network failure (`status` undefined), a structured
 * backend error (`{"error": {"code", "message"}}`, `code` populated), or a FastAPI/
 * Pydantic validation error (`{"detail": [...]}`, `code` undefined).
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
    public readonly code?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "DELETE";
  /** JSON-serialized as the request body with a `Content-Type: application/json` header. */
  json?: unknown;
  /** Sent as-is (e.g. a file upload) — the browser sets the multipart boundary itself. */
  formData?: FormData;
}

interface StructuredErrorBody {
  error?: { code?: string; message?: string };
  detail?: string | Array<{ loc?: Array<string | number>; msg?: string }>;
}

/**
 * The backend uses two distinct error shapes (`02_DOCS/ARCHITECTURE.md` "API Contract
 * Philosophy"): `{"error": {"code", "message"}}` from every domain module's own
 * exception handler, and FastAPI/Pydantic's own `{"detail": [...]}` for request-shape
 * validation errors (422) that never reach application code. Both are handled here so
 * every caller gets one consistent `ApiError`.
 */
async function describeErrorResponse(response: Response): Promise<{ message: string; code?: string }> {
  let body: StructuredErrorBody | undefined;
  try {
    body = (await response.json()) as StructuredErrorBody;
  } catch {
    return { message: `Request failed with status ${response.status}.` };
  }

  if (body?.error?.message) {
    return { message: body.error.message, code: body.error.code };
  }

  if (typeof body?.detail === "string") {
    return { message: body.detail };
  }

  if (Array.isArray(body?.detail) && body.detail.length > 0) {
    const first = body.detail[0];
    const location = Array.isArray(first.loc) ? first.loc.join(".") : undefined;
    const message = first.msg ?? "The request was invalid.";
    return { message: location ? `${location}: ${message}` : message };
  }

  return { message: `Request failed with status ${response.status}.` };
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const init: RequestInit = { method: options.method ?? "GET" };

  if (options.json !== undefined) {
    init.headers = { "Content-Type": "application/json" };
    init.body = JSON.stringify(options.json);
  } else if (options.formData) {
    init.body = options.formData;
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, init);
  } catch {
    throw new ApiError(`Could not reach the server while calling ${path}.`);
  }

  if (!response.ok) {
    const { message, code } = await describeErrorResponse(response);
    throw new ApiError(message, response.status, code);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}
