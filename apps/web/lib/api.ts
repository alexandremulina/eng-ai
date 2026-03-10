const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = "ApiError"
  }
}

async function apiFetch<T>(
  path: string,
  options: RequestInit & { token?: string } = {}
): Promise<T> {
  const { token, headers: extraHeaders, ...fetchOptions } = options
  const res = await fetch(`${API_URL}${path}`, {
    ...fetchOptions,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(extraHeaders ?? {}),
    },
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw new ApiError(res.status, error.detail ?? "Request failed")
  }
  return res.json()
}

export const api = {
  convert: (body: object, token?: string) =>
    apiFetch("/calculations/convert", { method: "POST", body: JSON.stringify(body), token }),
  npsh: (body: object, token?: string) =>
    apiFetch("/calculations/npsh", { method: "POST", body: JSON.stringify(body), token }),
  headLoss: (body: object, token?: string) =>
    apiFetch("/calculations/head-loss", { method: "POST", body: JSON.stringify(body), token }),
  queryNorms: (body: object, token?: string) =>
    apiFetch("/norms/query", { method: "POST", body: JSON.stringify(body), token }),
  diagnose: (formData: FormData, token?: string) =>
    apiFetch("/diagnosis/analyze", {
      method: "POST",
      body: formData,
      token,
      headers: {},
    }),
  parallelPumps: (body: object, token?: string) =>
    apiFetch("/calculations/parallel-pumps", { method: "POST", body: JSON.stringify(body), token }),
  extractPumpCurve: (formData: FormData, token?: string) =>
    apiFetch("/calculations/extract-pump-curve", {
      method: "POST",
      body: formData,
      token,
      headers: {},
    }),
  boltTorque: (body: object, token?: string) =>
    apiFetch("/calculations/bolt-torque", { method: "POST", body: JSON.stringify(body), token }),
  materialSelection: (body: object, token?: string) =>
    apiFetch("/calculations/material-selection", { method: "POST", body: JSON.stringify(body), token }),
}

export { ApiError }
