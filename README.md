# EngBrain

Mobile-first PWA for pump engineers.

## Stack

- **Frontend**: Next.js 16
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
uvicorn app.main:app --reload --port 8000
```

### Web (Next.js)

```bash
cd apps/web
npm install
npm run dev
```

## Supabase Setup

Run the following SQL in the Supabase SQL editor for your project:

### Enable pgvector
```sql
create extension if not exists vector;
```

### Norm documents table
```sql
create table norm_documents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id),
  content text not null,
  embedding vector(1536),
  metadata jsonb default '{}',
  created_at timestamptz default now()
);

create or replace function match_norm_documents(
  query_embedding vector(1536),
  match_threshold float,
  match_count int,
  filter_user_id uuid
)
returns table (id uuid, content text, metadata jsonb, similarity float)
language plpgsql
as $$
begin
  return query
  select nd.id, nd.content, nd.metadata,
    1 - (nd.embedding <=> query_embedding) as similarity
  from norm_documents nd
  where (nd.user_id is null or nd.user_id = filter_user_id)
    and 1 - (nd.embedding <=> query_embedding) > match_threshold
  order by nd.embedding <=> query_embedding
  limit match_count;
end;
$$;
```
