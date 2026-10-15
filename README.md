# Employee Management API

FastAPI backend with PostgreSQL persistence, user registration/login, JWT bearer
authentication, and protected user management endpoints.

## Setup

1. Create the PostgreSQL database named in `DATABASE_URL` in `.env.development`.
2. Create and activate a virtual environment from this directory:

   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Set `DATABASE_URL` in `.env.development` to your PostgreSQL connection string
   and replace `JWT_SECRET_KEY` with a long random secret.
4. Start the API:

   ```powershell
   uvicorn app.main:app --reload
   ```

The API runs at `http://localhost:8000`; interactive documentation is available
at `http://localhost:8000/docs`. Tables are created on application startup.

## QA and production environments

The backend loads `.env.development` by default. Set `APP_ENV=qa` or
`APP_ENV=production` before starting the application to load `.env.qa` or
`.env.production` respectively. For example, in PowerShell:

```powershell
$env:APP_ENV = "qa"
uvicorn app.main:app
```

Use `APP_ENV=production` for production. Replace the sample database URLs,
JWT secrets, and CORS origins in each environment file with values for your
own infrastructure. The production app refuses to start with a sample or
short JWT secret. Never use sample credentials in a deployed environment.

## Endpoints

- `POST /api/auth/register` — create an employee account.
- `POST /api/auth/login` — exchange an email and password for a bearer token.
- `GET /api/users/me` — return the authenticated account.
- `GET /api/users` — list users (administrator only).
- `GET /api/users/{user_id}` — read a user (self or administrator).
- `PATCH /api/users/{user_id}` — update a user (self or administrator); only
  administrators can change roles.
- `DELETE /api/users/{user_id}` — delete a user (self or administrator).

New registrations always receive the `employee` role. To grant administrator
access, update the user's `role` to `admin` through a trusted database
administration process. Password hashes are never included in API responses.

Set `CORS_ORIGINS` to a comma-separated list of trusted frontend origins when
deploying. Do not use the development JWT secret or sample database credentials
in production.

## Tests

Run `pytest` from this directory.
