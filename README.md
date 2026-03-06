# EngBrain

Mobile-first PWA for pump engineers.

## Stack

- **Frontend**: Next.js 15
- **Backend**: FastAPI (Python)
- **Database**: Supabase
- **AI**: OpenRouter
- **Payments**: Stripe

## Local Development

### API (FastAPI)

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Web (Next.js)

```bash
cd apps/web
npm install
npm run dev
```
