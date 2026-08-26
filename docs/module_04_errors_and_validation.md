# Module 04 — Errors, Validation & Response Design

## 📌 Overview
Designing predictable, standardized JSON error responses, handling FastAPI request validation errors (422 Unprocessable Entity), raising custom business domain exceptions, and implementing centralized exception handlers.

---

## 📝 Conceptual Questions & Implementation Notes

### 1. Consistent Error Response Shape
> Design an enterprise-grade error schema for the entire API.

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Product with ID 42 was not found.",
    "details": []
  }
}
```

### 2. Custom Exception Handlers in FastAPI
> How to intercept `RequestValidationError`, `HTTPException`, and custom `AppError` exceptions in FastAPI using `@app.exception_handler`.

**Answer:**
*(Write your explanation and implementation notes here)*

---

## 📷 Screenshots & Execution Proof

*(Store screenshots in `../screenshots/module_04/` and link them below)*

```markdown
<!-- Example screenshot embed:
![Validation Error 422](../screenshots/module_04/validation_error_422.png)
![Custom Error 404 Response](../screenshots/module_04/custom_404_error.png)
-->
```
