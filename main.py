
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import sqlite3

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key='verysecretkey')
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
DB_PATH = "staff.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS staff (id INTEGER PRIMARY KEY, name TEXT, cash INTEGER)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
        conn.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", ('admin', 'admin123'))
init_db()

def get_user(request: Request):
    return request.session.get("user")

def fetch_staff():
    with sqlite3.connect(DB_PATH) as conn:
        data = conn.execute("SELECT * FROM staff ORDER BY cash DESC").fetchall()
    return [{"id": r[0], "name": r[1], "cash": r[2], "points": round(r[2]/10000, 2), "place": i+1} for i, r in enumerate(data)]

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "user": get_user(request), "staff": fetch_staff()})

@app.get("/data")
async def data():
    return JSONResponse(fetch_staff())

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    with sqlite3.connect(DB_PATH) as conn:
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
    if user:
        request.session["user"] = username
        return RedirectResponse("/", 302)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Неверный логин или пароль"})

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", 302)

@app.post("/add")
async def add(request: Request, name: str = Form(...), cash: int = Form(...)):
    if get_user(request) != "admin":
        raise HTTPException(403)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT INTO staff (name, cash) VALUES (?, ?)", (name, cash))
    return JSONResponse({"status": "ok"})

@app.post("/delete")
async def delete(request: Request, staff_id: int = Form(...)):
    if get_user(request) != "admin":
        raise HTTPException(403)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM staff WHERE id=?", (staff_id,))
    return JSONResponse({"status": "ok"})

@app.post("/edit")
async def edit(request: Request, staff_id: int = Form(...), name: str = Form(...), cash: int = Form(...)):
    if get_user(request) != "admin":
        raise HTTPException(403)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE staff SET name=?, cash=? WHERE id=?", (name, cash, staff_id))
    return JSONResponse({"status": "ok"})
