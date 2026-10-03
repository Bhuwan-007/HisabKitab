# ITC Shield frontend (Dashboard, Recovery Queue, Audit)

Run (from this folder, with the backend on http://localhost:8000):

    npm install
    npm run dev          # opens on http://localhost:5173

Backend URL: copy .env.example to .env and change VITE_API_URL if needed.

Pages: Dashboard (/), Recovery Queue (/queue, /queue/:id opens the drawer), Audit and accuracy (/audit).
Keyboard in the queue: Arrow keys move, Enter opens, Esc closes the drawer.
mock/server.mjs is a tiny fake API for testing without the backend: node mock/server.mjs
