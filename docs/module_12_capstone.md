# Module 12 — Capstone Project: Production-Ready Mini API

## 📌 Overview
Architecting and building a unified, production-ready, modular REST backend that incorporates all previous lessons: configuration management, structured logging, JWT authentication & authorization, centralized error handling, pagination, filtering, rate limiting, and comprehensive test coverage.

---

## 🏗️ Architecture & Component Design

### 1. Core Modules
- **Authentication (`/api/v1/auth`, `/api/v1/users`)**: User registration, bcrypt hashing, JWT token issuance, profile retrieval.
- **Catalog (`/api/v1/products`)**: Product CRUD with pagination (`page`, `limit`), categorization, price filtering, and stock updates.
- **Transactions (`/api/v1/orders`)**: Order creation with multiple items, subtotal calculation, inventory checking, and status tracking.

---

## 📷 Screenshots & Execution Proof

*(Store screenshots in `../screenshots/module_12/` and link them below)*

```markdown
<!-- Example screenshot embed:
![Full App Architecture Diagram](../screenshots/module_12/architecture_diagram.png)
![End-to-End Test Suite Run](../screenshots/module_12/e2e_pytest_run.png)
![Interactive Swagger Docs](../screenshots/module_12/capstone_swagger_ui.png)
-->
```
