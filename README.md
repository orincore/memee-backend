# Memee Backend

A production-ready FastAPI backend for the Memee meme aggregator platform.

## Features
- Fetch memes from Reddit, upload to Cloudinary, and store metadata in Supabase
- Public API for browsing memes by category
- Affiliate product endpoint
- Secure, token-protected meme fetching
- CORS support for web and mobile

## Project Structure
```
app/
  main.py           # FastAPI entrypoint
  routes/           # API route definitions
  models/           # Pydantic models
  services/         # Business logic (Reddit, Supabase, Cloudinary)
```

## Setup
1. **Clone the repo**
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure environment**
   - Copy `.env.example` to `.env` and fill in your credentials
4. **Run the server**
   ```bash
   uvicorn app.main:app --reload
   ```

## API Endpoints
- `GET /memes/{category}` — Paginated memes by category
- `GET /products` — Affiliate products
- `POST /fetch-memes/{category}` — Trigger meme fetch (requires `x-api-token` header)

## Suggestions
- Use FastAPI BackgroundTasks for non-blocking meme fetching
- For scale, consider Redis caching and hosting on Render.com or Railway.app

## License
MIT 

Perfect! Here’s a checklist and tips for testing your other endpoints in Postman:

---

## 1. **Login**
- **POST** `/auth/login`
- Body: `form-data`
  - login_id: (your email or username)
  - password: (your password)
- If you haven’t verified your email, you’ll get a “Email not verified” error.

---

## 2. **Verify OTP**
- **POST** `/auth/verify-otp`
- Body: `form-data`
  - email: (your email)
  - otp: (the code you received by email)

---

## 3. **Resend OTP**
- **POST** `/auth/resend-otp`
- Body: `form-data`
  - email: (your email)

---

## 4. **Send Friend Request**
- **POST** `/friends/request`
- Body: `x-www-form-urlencoded` or `form-data`
  - to_user_id: (the user ID of the friend you want to add)
- Note: For now, user authentication is mocked (always user_id=1). In production, this will be replaced with JWT auth.

---

## 5. **Respond to Friend Request**
- **POST** `/friends/respond`
- Body: `x-www-form-urlencoded` or `form-data`
  - request_id: (the friend request ID)
  - accept: (true/false)

---

## 6. **List Friends**
- **GET** `/friends/list`
- No body needed.

---

## 7. **Search Users**
- **GET** `/friends/search?q=USERNAME`
- Replace `USERNAME` with the username or part of the username you want to search for.

---

## 8. **Swagger UI**
- You can also test all endpoints interactively at [http://localhost:8000/docs](http://localhost:8000/docs).

---

### ⚠️ **If you get errors:**
- Read the error message in the response and/or your server logs.
- If you see a 409 error on signup, the username/email is already taken.
- If you see a 403 on login, your email is not verified.
- If you see a 500 error, check your server logs for details and let me know!

---

Would you like:
- Example Postman requests for any specific endpoint?
- Help with JWT authentication for real user sessions?
- To proceed with meme/message sharing between friends?

Let me know if you hit any issues or want to see example request/response bodies!