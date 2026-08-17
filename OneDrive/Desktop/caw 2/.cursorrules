# AI Agent System Instructions & Grounding Rules

You are an autonomous coding agent operating on the URL Shortener project. You must strictly adhere to the following architectural, security, and operational guidelines. Do not deviate from these rules without explicit human approval.

## 1. Dependency Management & Supply Chain Safety
- **No Unvetted Packages:** You are strictly forbidden from adding new third-party dependencies to `package.json` unless explicitly instructed by the user. 
- **Use Built-ins First:** Always attempt to solve problems using the Node.js standard library or existing dependencies before suggesting a new package.
- **Dependency Vetting:** If a new package is absolutely required, you must pause execution and request human review for supply-chain vetting before modifying the lockfile.

## 2. Authentication & Authorization (BOLA/IDOR Prevention)
- **Zero-Trust Endpoints:** All new and modified endpoints must implement explicit authorization checks. Never assume the caller is authorized based on authentication alone.
- **Mandatory Middleware:** You must use the existing `src/middleware/auth.js` middlewares (`requireAuth` and `requireAdmin`). Do not implement ad-hoc JWT validation or custom authorization logic.
- **Resource Ownership:** For all resource modification/deletion endpoints (e.g., `DELETE /users/:id`), you must verify that the requesting user owns the resource or has global admin privileges.
- **No Hardcoded Secrets:** Never hardcode secrets, tokens, or keys in the source code. Always use `process.env` for configuration.

## 3. Architecture, Error Handling & Utilities
- **Database Access:** All Postgres queries must be wrapped in the standard `queryWithTimeout` utility to prevent connection hanging.
- **Idempotency & State:** Operations should be idempotent where possible. Ensure explicit rowCount validations when performing updates or deletes (e.g., throwing a `404` if `rowCount === 0`).
- **Structured Logging:** Use the project's existing structured logger utility for all errors and critical state transitions. Do not use standard `console.log()` or `console.error()`. Log the context (user ID, resource ID, error trace) without logging sensitive PII.
- **Fail Closed:** In the event of an unhandled exception or ambiguous state, the system must fail closed (deny access/abort operation) and return a standard `500` format without leaking internal stack traces to the client.

## 4. Input Validation & Schema Enforcement
- **Validate at the Boundary:** Every incoming `req.body`, `req.params`, and `req.query` must be validated against a strict schema (e.g., Zod / Joi) before hitting database or business logic. Strip unknown keys automatically.

## 5. Secret & PII Hygiene in Telemetry
- **Redaction Rules:** Never log raw tokens, authorization headers, passwords, or PII (e.g., raw email addresses or IP addresses unless hashed/masked) inside structured logger payloads.

## 6. Test Co-Generation Requirement
- **No Untested Mutations:** Every new route handler or database mutation must include corresponding unit/integration test cases under `tests/` covering:
  1. The happy path (`200`/`201`).
  2. The unauthorized/forbidden path (`401`/`403`).
  3. The non-existent resource path (`404`).
  4. The transient timeout/database failure fallback (`503`/`504`).
