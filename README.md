# Shubh Bill

Production billing PWA built with Django REST Framework, SQLite, React, Vite, TypeScript, Material UI, and vite-plugin-pwa.

## Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## Docker

```cmd
docker compose up --build
```

App: `http://127.0.0.1:5173`

Admin: `http://127.0.0.1:8000/admin/`

Create admin user:

```cmd
docker compose exec backend python manage.py createsuperuser
```

Seed demo data:

```cmd
docker compose exec backend python manage.py seed_demo_data
```

## PythonAnywhere deployment

Goal: GitHub me push karte hi PythonAnywhere par latest code deploy ho.

### 1. Git repo clean rakho

Is project ko apna separate Git repo banao. Abhi agar parent `Desktop` repo ban gaya ho, to PythonAnywhere par clone karte time sirf `shubh_bill` project repo use karo.

```bash
git init
git add .
git commit -m "Initial shubh bill app"
git branch -M main
git remote add origin git@github.com:YOUR_GITHUB_USER/shubh_bill.git
git push -u origin main
```

### 2. PythonAnywhere par first setup

PythonAnywhere Bash console me:

```bash
git clone git@github.com:YOUR_GITHUB_USER/shubh_bill.git ~/shubh_bill
cd ~/shubh_bill
python3 -m venv ~/.virtualenvs/shubh_bill
bash scripts/pythonanywhere_deploy.sh
```

PythonAnywhere Web tab:

- Manual configuration web app banao.
- Virtualenv: `/home/YOUR_PA_USER/.virtualenvs/shubh_bill`
- Source code / Working directory: `/home/YOUR_PA_USER/shubh_bill/backend`
- WSGI file me `scripts/pythonanywhere_wsgi.py` ka content paste karo aur `yourusername` ko apne PythonAnywhere username se replace karo.
- Static files mapping add karo:
  - URL: `/static/`
  - Directory: `/home/YOUR_PA_USER/shubh_bill/backend/staticfiles`

### 3. Production env values

PythonAnywhere Web tab ke environment variables me ye values rakho:

```bash
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=YOUR_PA_USER.pythonanywhere.com
DJANGO_CORS_ALLOWED_ORIGINS=https://YOUR_PA_USER.pythonanywhere.com
DJANGO_SECRET_KEY=use-a-long-random-secret
```

### 4. Auto deploy on git push

GitHub repo me Settings -> Secrets and variables -> Actions me ye secrets add karo:

```text
PA_SSH_HOST=ssh.pythonanywhere.com
PA_SSH_USER=YOUR_PA_USER
PA_SSH_KEY=your-private-ssh-key
```

Ab `main` branch par push karoge to `.github/workflows/pythonanywhere-deploy.yml` PythonAnywhere me `scripts/pythonanywhere_deploy.sh` run karega.

```bash
git add .
git commit -m "Update app"
git push
```

Note: agar aapke PythonAnywhere plan me SSH available nahi hai, to same deploy command PythonAnywhere Bash console se manually run karni hogi:

```bash
cd ~/shubh_bill
bash scripts/pythonanywhere_deploy.sh
```

### 5. Mobile install check

PythonAnywhere ka HTTPS URL open karo: `https://YOUR_PA_USER.pythonanywhere.com`.

- Android Chrome: browser menu -> Add to Home screen / Install app.
- iPhone Safari: Share button -> Add to Home Screen.
- Agar install option na aaye, pehle ek baar hard refresh karo. PWA files production build ke time `frontend/dist` me banti hain aur deploy script unhe Django static files me collect karta hai.

PythonAnywhere Docker containers run nahi karta, isliye yahan venv + WSGI setup use karo. AWS/VPS par baad me root `Dockerfile` se container deployment use kar sakte hain.
