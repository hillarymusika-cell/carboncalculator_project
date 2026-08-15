# Cosmic Carbon Calculator

[![Live Demo](https://img.shields.io/badge/demo-onrender-00C7D2?style=flat-square)](https://carboncalculator-project.onrender.com/auth/login)
[![Python](https://img.shields.io/badge/python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-2.3+-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-see%20repo-lightgrey?style=flat-square)](#license)

**Estimate · Track · Reduce**

A full-stack carbon footprint calculator that turns everyday choices — how you travel, power your home, and manage your household — into clear CO₂e totals, history, and charts.

**Live:** [carboncalculator-project.onrender.com](https://carboncalculator-project.onrender.com/auth/login)

---

## Features

| Feature | Description |
|--------|-------------|
| **Multi-step assessment** | Guided form for transport, housing, and energy |
| **Instant breakdown** | Per-category CO₂e (transport, housing, energy, household, tree offset) |
| **Dashboard** | Dark eco-themed overview with doughnut + trend charts (Chart.js) |
| **History** | Saved assessments per account; recent panel in the nav |
| **Auth** | Email/password + Google OAuth (Authlib) |
| **Responsive UI** | Mobile drawer nav, desktop horizontal nav, consistent teal/cyan design system |
| **Docker-ready** | Production image with Gunicorn |
| **Real-time APIs** | `/api/calculate` preview without saving |

---

## Tech stack

**Backend**
- Flask 2.3+
- Flask-SQLAlchemy, Flask-Login, Flask-WTF (CSRF)
- Authlib (Google OAuth)
- PostgreSQL (production) / SQLite (local default via instance)
- Gunicorn

**Frontend**
- Jinja2 templates
- Vanilla CSS (design tokens in `base.css`)
- Vanilla JS (`base.js`, `home.js`, `dashboard.js`, …)
- Chart.js 4.x (CDN)

**Ops**
- Docker / docker-compose
- Deployed on Render

---

## Quick start

### Prerequisites

- Python 3.11+
- (Optional) Docker
- (Optional) Google OAuth credentials for social login

### Local (venv)

```bash
git clone https://github.com/hillarymusika-cell/carboncalculator_project.git
cd carboncalculator_project

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt

# Optional env
cp .env.example .env        # if present; otherwise export vars below
export FLASK_DEBUG=1
export SECRET_KEY=dev-secret-change-me

python app.py
# → http://127.0.0.1:5000
```

### Docker

```bash
docker build -t cosmic-carbon .
docker run --rm -p 5000:5000 \
  -e SECRET_KEY=change-me \
  -e FLASK_DEBUG=0 \
  cosmic-carbon
```

Or with Compose:

```bash
docker compose up --build
```

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes (prod) | Flask session / CSRF secret |
| `DATABASE_URL` | Prod | PostgreSQL URL (e.g. Render). Falls back to SQLite under `instance/` |
| `FLASK_DEBUG` | No | `1` for debug reloader |
| `PORT` | No | Default `5000` |
| `GOOGLE_CLIENT_ID` | OAuth | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | OAuth | Google OAuth client secret |

Use a `.env` file with `python-dotenv` for local development.

---

## Project structure

```
carboncalculator_project/
├── app.py                 # Entry: create_app + Gunicorn target
├── init.py                # App factory
├── auth.py                # Login, signup, logout, Google OAuth
├── views.py               # Home, dashboard, about, submit, history, APIs
├── models.py              # User + assessment models
├── calculator.py          # Emission factors & calculators + pure APIs
├── validate_password.py
├── hash.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── static/
│   ├── base.css / base.js       # Design system + nav
│   ├── home.css / home.js       # Hero + multi-step form
│   ├── about.css
│   ├── login.css / login.js
│   ├── signup.css / signup.js
│   ├── dashboard.css / dashboard.js
│   └── home.png
└── templates/
    ├── base.html
    ├── home.html
    ├── about.html
    ├── login.html
    ├── sign_up.html
    └── dashboard.html
```

All page styles and scripts live in `static/`. Templates only inject routes/CSRF where Jinja is required (`window.APP_ROUTES`, `window.CSRF_TOKEN`).

---

## How emissions are calculated

Factors live in `calculator.py` (kg CO₂e per unit). Summary:

### Transport (`TRANSPORT_FACTORS`)

| Mode | Factor (kg CO₂e / unit) |
|------|-------------------------|
| Car | 0.192 |
| Bus | 0.089 |
| Motorcycle | 0.135 |
| Electric train | 0.041 |
| Thermo train | 0.093 |
| Bicycle | 0.0 |
| Other | 0.15 |

Frequency (times/week) scales the transport total.

### Fuel / energy (`FUEL_FACTORS`)

| Source | Factor |
|--------|--------|
| Gas / petroleum | 2.31 |
| Coal | 2.65 |
| Charcoal | 1.89 |
| Electricity | 0.475 |
| Firewood | 1.25 |

Monthly energy expense is used as the activity units for the selected fuel.

### Household & offset

| Source | Factor |
|--------|--------|
| Buildings (per house) | 15.0 |
| Adults | 45.0 |
| Livestock | 18.0 |
| Pets | 40.0 |
| Trees | −21.0 / 12 (monthly offset) |

Totals are stored in kg CO₂e; the UI displays tonnes (÷ 1000).

> Factors are illustrative estimates. Adjust `calculator.py` for region-specific values (e.g. grid intensity).

---

## UI notes

- **Design tokens** (`base.css`): teal deep/base/light, cyan accent, eco green, paper/ink, shared radius & shadow.
- **Nav**: hamburger drawer on mobile; horizontal links ≥900px.
- **Assessment**: 3-step progress (Transport → Housing → Energy) with card-style radios.
- **Dashboard**: dark theme, live badge, category doughnut + weekly trend, history table toggle.

---

## API / routes (high level)

| Method | Path | Purpose |
|--------|------|---------|
| GET/POST | `/auth/login` | Login |
| GET/POST | `/auth/signup` | Registration |
| POST | `/auth/logout` | Logout |
| GET | `/auth/google` | Google OAuth start |
| GET | `/` or home | Landing + assessment form |
| POST | `/submit` | Save assessment → dashboard |
| GET | `/dashboard` | Charts + history |
| GET | `/history` | JSON recent assessments |
| GET | `/about` | About page |
| GET | `/api/factors` | Emission factor tables |
| POST | `/api/calculate` | Real-time full calc (no save) |
| POST | `/api/calculate/single` | Real-time single source |

CSRF is enforced via Flask-WTF; external JS reads `window.CSRF_TOKEN`.

---

## Real-time calculation APIs

Pure logic lives in `calculator.py`. HTTP wrappers are in `views.py`.

### Python (no Flask)

```python
from calculator import calculate_from_inputs, calculate_single, list_factors

result = calculate_from_inputs({
    "transport": "car",
    "frequency": 5,
    "fuel": "electricity",
    "energy_expense": 200,
    "house_no": 1,
    "adults": 2,
    "trees": 10,
})
# result["total_kg_co2e"], result["breakdown"], result["detailed"], ...

print(calculate_single("transport", 3, transport_type="bus"))
print(list_factors())
```

### HTTP

| Method | Path | Auth | Saves? | Purpose |
|--------|------|------|--------|---------|
| `GET` | `/api/factors` | No | No | Factor tables for UI |
| `POST` | `/api/calculate` | No | No | Full footprint (JSON or form) |
| `POST` | `/api/calculate/single` | No | No | One source only |
| `POST` | `/submit` | Yes | Yes | Calculate **and** store history |

**Example — live full calc**

```bash
curl -s -X POST http://127.0.0.1:5000/api/calculate \
  -H "Content-Type: application/json" \
  -d '{"transport":"car","frequency":5,"fuel":"electricity","energy_expense":200,"house_no":1,"adults":2,"trees":10}'
```

**Example — single source**

```bash
curl -s -X POST http://127.0.0.1:5000/api/calculate/single \
  -H "Content-Type: application/json" \
  -d '{"source":"trees","units":10}'
```

The assessment form debounces calls to `/api/calculate` and shows a live estimate above the nav buttons.

---

## Deployment (Render)

1. Connect the GitHub repo.
2. Set build: `pip install -r requirements.txt`
3. Start: `gunicorn --bind 0.0.0.0:$PORT --workers 3 app:app`
4. Add env: `SECRET_KEY`, `DATABASE_URL` (Render Postgres), optional Google OAuth keys.
5. Ensure `instance/` or the DB URL is writable/persistent.

The included `Dockerfile` uses the same Gunicorn command for container deploys.

---

## Development tips

```bash
# Debug server
FLASK_DEBUG=1 python app.py

# Format / lint (if you add tools)
# ruff check . && ruff format .
```

When changing emission logic, update both `calculator.py` and the About page copy so users see matching explanations.

---

## Roadmap ideas

- [ ] Region-specific emission factors (selectable country/grid)
- [ ] Export PDF / CSV of history
- [ ] Personalized reduction tips
- [ ] Email verification & password reset
- [ ] Dark/light theme toggle on all pages

---

## Contributing

1. Fork and create a feature branch.
2. Keep UI CSS/JS in `static/`; avoid large inline blocks in templates.
3. Match existing design tokens and a11y patterns (focus rings, `aria-*` on nav).
4. Open a PR with a short description of the change and screenshots for UI work.

---

## License

See the repository for license terms. If none is specified yet, contact the maintainer before redistributing.

---

## Credits

Built as a carbon awareness tool for estimating personal / household CO₂e from transport, energy, and home data. Charts by [Chart.js](https://www.chartjs.org/).

**Maintainer:** [hillarymusika-cell](https://github.com/hillarymusika-cell)
