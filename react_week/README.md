# React + Vite

## Running Customer Intelligence

Create a private backend configuration file once. In the VS Code PowerShell terminal, run:

```powershell
Copy-Item backend\.env.example backend\.env
notepad backend\.env
```

In `backend\.env`, replace `APP_USERNAME` with your chosen login name, `APP_PASSWORD` with a new strong password, and `APP_AUTH_SECRET` with a randomly generated value. Generate one with:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Paste the generated value after `APP_AUTH_SECRET=` and save the file. Do not share or commit `backend\.env`; it is excluded from Git. Then restart the backend and frontend:

```powershell
.\start_all.bat
```

The backend reads `backend\.env` directly, so credentials do not depend on which terminal launched it. `APP_AUTH_SECRET` must be at least 32 characters. The login grants a 12-hour session; all application `/api/` endpoints except `/api/auth/login` require its bearer token. Use HTTPS when deploying outside a trusted local machine.

The Feedback History page can download a complete analysis PDF or a PDF limited to an individual upload batch; reports include sentiment/severity analysis and graphical charts.

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
