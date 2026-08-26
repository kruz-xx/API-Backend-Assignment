# Module 00 — What Even Is an API? (Prerequisites)

##  Overview
Understanding what an API (Application Programming Interface) is conceptually, distinguishing between client and server roles, understanding protocols, and contrasting web pages with APIs.

---

##  Conceptual Questions & Answers

### 1. What is an API?
> Explain in your own words: what is an API? Don't just say "Application Programming Interface" — explain the concept to someone who only knows how to use a browser.

**Answer:**

Analogy used here: TV Remote to change the volume.

When using a remote control to increase or decrease the volume on a TV, we don't need to understand the internal circuitry of the speakers or how sound waves are amplified. We just see the buttons with either plus and minus or, up and down arrows indicating what button does what. 

According to the button we press, the remote control sends an infrared signal to the TV which the setup box recognises and hence follows through with the command. This command is then processed and carried out, changing the volume on the TV.

This is how an API request works. So, an API is an interface that allows two softwares to communicate effectively and share information securely and efficiently.

---

### 2. Client Vs Server Relationship
> Explain the client-server relationship.

**Answer:**

Client: The one who requests the actions or for information. AKA The browser or terminal (using curl).

Server: The one who provides responses for the request. It holds the business logic, processes incoming requests, talks to the database and also sends back the data.

ASCII Diagram:

```text
+-------------------+                      +-------------------+
|                   |  HTTP Request ---->  |                   |
|      CLIENT       |  (GET /api/users)    |      SERVER       |
| (Browser/Postman) |                      | (FastAPI Backend) |
|                   |  <--- HTTP Response  |                   |
+-------------------+     (200 OK + JSON)  +-------------------+
                                                     |
                                                     v
                                           +-------------------+
                                           |     Database      |
                                           +-------------------+
```

---

### 3. Statelessness Concept
> Why is HTTP described as "stateless"? What does that mean for how authentication and login sessions work?

**Answer:**

HTTP being stateless refers to the independency of requests in a server. It means that the server does not have built-in memory for previous requests and hence treats every request independently. 

It's relation to how authentication and login sessions work leads back to the fact that the server does not hold your request in memory after it is fulfilled unless you attach an identifier to every single request. These identifiers can be JWT tokens, session cookies or an API key. This helps prove your identity and keep you logged-in into the server. 

---

### 4. API vs Web Page
> Explain the difference between an API and a web page: both use HTTP, but what is fundamentally different about what they return and who/what consumes it?

**Answer:**

The main difference between an API and a web page comes down to their formats. A web page is usually HTML, CSS or JavaScript; these formats are designed to be rendered in a web browser for human consumption. 

Meanwhile, an API returns raw, structured data in JSON or XML formats, these are supposed to be consumed programmatically by machines, applications, or even frontend frameworks like React. 

---

### 5. Three real APIs
> List APIs you use in daily life without realizing it and briefly describe what each one does.

**Answer:**

(1.) Payment apps like Google Pay:
     E-commerce apps like Google Pay send payment details throught secure payment APIs to authorize and verify transactions without exposing sensitive information or storing the sensitive data in their own servers.

(2.) Travel websites like TripAdvisor:
     Travel websites like TripAdvisor use APIs to pull in data from various sources like airlines, hotels, and local tour operators. This allows users to compare prices and book flights, hotels, and activities all in one place.

(3.) Delivery apps like Blinkit:
     Blinkit's mobile app uses APIs to fetch product details, check inventory, process payments, and coordinate with delivery partners for smooth, real-time tracking of orders. 

---

