# Module 05 — Authentication & Authorization

## 📌 Overview
Authentication ("who you are") vs Authorization ("what you can do"). Implementation of password hashing with bcrypt, JSON Web Tokens (JWT) signed with HMAC-SHA256, Bearer token authentication flow, and Role-Based Access Control (RBAC).

---

## 📝 Conceptual Questions & Implementation Notes

### 1. Authentication vs Authorization
> Detail the core distinction between authentication and authorization with code/endpoint examples.

**Answer:**
*(Write your explanation here)*

### 2. JWT (JSON Web Token) Anatomy & Security
> Explain the three parts of a JWT: Header, Payload (claims), and Signature. Why must secret keys remain private, and how does token expiration (`exp`) mitigate replay attacks?

**Answer:**
*(Write your explanation here)*

### 3. Implementing Dependency Injection Auth in FastAPI
> Explain the `OAuth2PasswordBearer` and `Depends(get_current_user)` pattern.

**Answer:**
*(Write your explanation here)*

---

## 📷 Screenshots & Execution Proof

*(Store screenshots in `../screenshots/module_05/` and link them below)*

```markdown
<!-- Example screenshot embed:
![Login JWT Generation](../screenshots/module_05/login_jwt_token.png)
![Protected Endpoint 401 Unauthorized](../screenshots/module_05/unauthorized_access.png)
![Protected Endpoint 200 with Bearer](../screenshots/module_05/authorized_profile_access.png)
-->
```
