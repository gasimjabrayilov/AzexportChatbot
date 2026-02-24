import os, uuid, json, re
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

STOPWORDS = {"uzre", "üzrə", "sirket", "şirkət", "lazimdir", "lazımdır", "lazim", "lazım"}

SYSTEM_PROMPT = """You are a query extraction module. Return ONLY valid JSON.
JSON schema: {"intent":"find_service","query":"...","needs_clarification":false}
Extract the shortest searchable query (max 2-3 words) from the user message.
If too vague, set needs_clarification=true.
Text will be in Azerbaijani, Russian or English. First adjust grammar mistakes of sentence. then generate 2-3 keywords.
if useful add a synonym keyword.
"""

def safe_parse(raw: str):
    try:
        return json.loads(raw)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", raw or "")
        return json.loads(m.group(0)) if m else {"query": "", "needs_clarification": True}

def build_or_expr(query: str):
    q = (query or "").lower().strip()
    tokens = [t for t in re.split(r"\s+", q) if len(t) >= 2 and t not in STOPWORDS]
    if not tokens:
        return None
    parts = []
    for t in tokens:
        parts += [f"keywords.ilike.*{t}*", f"services_text.ilike.*{t}*"]
    return ",".join(parts)

def format_rows(rows):
    if not rows:
        return "Bu açar söz üzrə uyğun biznes tapılmadı."
    out = ["✅ Tapılan bizneslər:\n"]
    for i, r in enumerate(rows, 1):
        out.append(
            f"{i}) 🏢 Şirkət: {r.get('company_name','-')}\n"
            f"   👤 Təmsilçi: {r.get('full_name','-')}\n"
            f"   👤 Pozisiya: {r.get('position','-')}\n"
            f"   📞 Telefon: {r.get('phone','-')}\n"
            f"   🧾 Xidmət: {r.get('services_text','-')}\n"
        )
    msg = "\n".join(out)
    return msg[:3900] + "\n…(davamı var)" if len(msg) > 3900 else msg

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # session id via cookie fallback
    sid = request.cookies.get("sid") or str(uuid.uuid4())
    resp = templates.TemplateResponse("chat.html", {"request": request, "sid": sid})
    resp.set_cookie("sid", sid, httponly=True, samesite="lax")
    return resp

@app.post("/api/chat")
async def chat(request: Request):
    data = await request.json()
    sid = data.get("session_id")
    msg = (data.get("message") or "").strip()

    if not msg:
        return JSONResponse({"reply": "Zəhmət olmasa, yazılı mesaj göndərin."})

    if msg == "/start":
        return JSONResponse({"reply": "Salam! Xidmət yazın, uyğun üzvləri tapım."})
    if msg == "/help":
        return JSONResponse({"reply": "Sadəcə xidmət adını yazın: logistika, marketinq, tikinti, ..."})

    # LLM extraction
    c = openai_client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": msg}],
    )
    parsed = safe_parse(c.choices[0].message.content or "")

    if parsed.get("needs_clarification"):
        return JSONResponse({"reply": "Açar söz yazın…"})

    or_expr = build_or_expr(parsed.get("query", ""))
    if not or_expr:
        return JSONResponse({"reply": "Açar söz yazın…"})

    resp = supabase.table("members_with_keywords").select("*").or_(or_expr).execute()
    rows = resp.data or []
    return JSONResponse({"reply": format_rows(rows)})
