from flask import Flask, render_template, request, jsonify, redirect, url_for, Response, send_from_directory
import json
import os
from datetime import datetime
import math

app = Flask(__name__, static_folder="static")
DATA_FILE = "data/attendance.json"

# ---------- helpers ----------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"sessions": [], "records": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def session_stats(sid, records):
    recs = [r for r in records if r["session_id"] == sid]
    return {"count": len(recs)}

# ---------- PWA files ----------

@app.route("/manifest.json")
def manifest():
    m = {
        "name": "Presençômetro 3ºC TDS",
        "short_name": "Presençômetro",
        "description": "Registro de presença com geolocalização — 3ºC TDS",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#080b12",
        "theme_color": "#7c3aed",
        "orientation": "portrait-primary",
        "icons": [
            {"src": "/static/icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": "/static/icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}
        ],
        "categories": ["education", "utilities"],
        "lang": "pt-BR"
    }
    return jsonify(m)

@app.route("/sw.js")
def service_worker():
    sw = """
const CACHE = 'presencometro-v1';
const OFFLINE_URLS = ['/', '/static/offline.html'];

self.addEventListener('install', e => {
    e.waitUntil(caches.open(CACHE).then(c => c.addAll(OFFLINE_URLS)));
    self.skipWaiting();
});

self.addEventListener('activate', e => {
    e.waitUntil(caches.keys().then(keys =>
        Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ));
    self.clients.claim();
});

self.addEventListener('fetch', e => {
    if (e.request.method !== 'GET') return;
    e.respondWith(
        fetch(e.request)
            .then(res => {
                const clone = res.clone();
                caches.open(CACHE).then(c => c.put(e.request, clone));
                return res;
            })
            .catch(() => caches.match(e.request).then(r => r || caches.match('/static/offline.html')))
    );
});
"""
    return Response(sw, mimetype="application/javascript")

# ---------- pages ----------

@app.route("/")
def index():
    data = load_data()
    sessions = sorted(data["sessions"], key=lambda s: s["created_at"], reverse=True)
    for s in sessions:
        s["_count"] = len([r for r in data["records"] if r["session_id"] == s["id"]])
    return render_template("index.html", sessions=sessions)

@app.route("/credits")
def credits():
    return render_template("credits.html")

@app.route("/session/<sid>")
def session_detail(sid):
    data = load_data()
    session = next((s for s in data["sessions"] if s["id"] == sid), None)
    if not session:
        return redirect(url_for("index"))
    records = sorted(
        [r for r in data["records"] if r["session_id"] == sid],
        key=lambda r: r["timestamp"], reverse=True
    )
    return render_template("session.html", session=session, records=records)

# ---------- API ----------

@app.route("/api/sessions", methods=["GET"])
def api_sessions():
    data = load_data()
    sessions = sorted(data["sessions"], key=lambda s: s["created_at"], reverse=True)
    for s in sessions:
        s["count"] = len([r for r in data["records"] if r["session_id"] == s["id"]])
    return jsonify({"ok": True, "sessions": sessions})

@app.route("/api/session/new", methods=["POST"])
def api_new_session():
    body = request.json or {}
    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"ok": False, "error": "nome é obrigatório"}), 400
    data = load_data()
    session = {
        "id": str(int(datetime.now().timestamp() * 1000)),
        "name": name,
        "created_at": datetime.now().isoformat(),
        "lat": body.get("lat"),
        "lon": body.get("lon"),
        "radius": int(body.get("radius", 100)),
        "active": True,
        "address": body.get("address", "")
    }
    data["sessions"].append(session)
    save_data(data)
    return jsonify({"ok": True, "session": session}), 201

# Legacy route kept for compatibility
@app.route("/session/new", methods=["POST"])
def new_session():
    return api_new_session()

@app.route("/api/session/<sid>", methods=["GET"])
def api_session_get(sid):
    data = load_data()
    session = next((s for s in data["sessions"] if s["id"] == sid), None)
    if not session:
        return jsonify({"ok": False, "error": "sessão não encontrada"}), 404
    records = [r for r in data["records"] if r["session_id"] == sid]
    session["count"] = len(records)
    return jsonify({"ok": True, "session": session, "records": records})

@app.route("/api/session/<sid>/close", methods=["POST"])
def api_close_session(sid):
    data = load_data()
    for s in data["sessions"]:
        if s["id"] == sid:
            s["active"] = False
            s["closed_at"] = datetime.now().isoformat()
            save_data(data)
            return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "sessão não encontrada"}), 404

# Legacy
@app.route("/session/<sid>/close", methods=["POST"])
def close_session(sid):
    return api_close_session(sid)

@app.route("/api/session/<sid>/records", methods=["GET"])
def api_get_records(sid):
    data = load_data()
    records = sorted(
        [r for r in data["records"] if r["session_id"] == sid],
        key=lambda r: r["timestamp"], reverse=True
    )
    return jsonify({"ok": True, "records": records, "count": len(records)})

# Legacy
@app.route("/session/<sid>/records")
def get_records(sid):
    data = load_data()
    records = [r for r in data["records"] if r["session_id"] == sid]
    return jsonify(records)

@app.route("/api/checkin", methods=["POST"])
def api_checkin():
    body = request.json or {}
    sid   = (body.get("session_id") or "").strip()
    name  = (body.get("name") or "").strip()
    lat   = body.get("lat")
    lon   = body.get("lon")

    if not name:
        return jsonify({"ok": False, "error": "nome é obrigatório"}), 400
    if not sid:
        return jsonify({"ok": False, "error": "session_id é obrigatório"}), 400

    data = load_data()
    session = next((s for s in data["sessions"] if s["id"] == sid), None)
    if not session:
        return jsonify({"ok": False, "error": "sessão não encontrada"}), 404
    if not session.get("active"):
        return jsonify({"ok": False, "error": "sessão encerrada"}), 400

    duplicate = any(
        r["session_id"] == sid and r["name"].lower() == name.lower()
        for r in data["records"]
    )
    if duplicate:
        return jsonify({"ok": False, "error": "presença já registrada nesta sessão"}), 409

    distance = None
    location_valid = True
    if session.get("lat") is not None:
        if lat is None or lon is None:
            return jsonify({"ok": False, "error": "esta sessão exige GPS — permita o acesso à localização"}), 400
        distance = haversine(session["lat"], session["lon"], lat, lon)
        location_valid = distance <= session["radius"]

    if not location_valid:
        return jsonify({
            "ok": False,
            "error": f"fora da área permitida ({int(distance)}m de distância, máximo {session['radius']}m)"
        }), 400

    record = {
        "id": str(int(datetime.now().timestamp() * 1000)),
        "session_id": sid,
        "name": name,
        "lat": lat,
        "lon": lon,
        "distance": round(distance, 1) if distance is not None else None,
        "timestamp": datetime.now().isoformat()
    }
    data["records"].append(record)
    save_data(data)
    return jsonify({"ok": True, "record": record}), 201

# Legacy
@app.route("/checkin", methods=["POST"])
def checkin():
    return api_checkin()

@app.route("/api/session/<sid>/export", methods=["GET"])
def api_export_csv(sid):
    fmt = request.args.get("format", "csv")
    data = load_data()
    session = next((s for s in data["sessions"] if s["id"] == sid), None)
    records = sorted(
        [r for r in data["records"] if r["session_id"] == sid],
        key=lambda r: r["timestamp"]
    )
    lines = ["Nome,Horário,Latitude,Longitude,Distância (m)"]
    for r in records:
        ts = datetime.fromisoformat(r["timestamp"]).strftime("%d/%m/%Y %H:%M:%S")
        dist = r.get("distance") if r.get("distance") is not None else ""
        lines.append(f'{r["name"]},{ts},{r.get("lat","")},{r.get("lon","")},{dist}')
    csv_content = "\n".join(lines)
    session_name = session["name"] if session else sid
    filename = f"presenca_{session_name.replace(' ','_')}.csv"
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# Legacy
@app.route("/session/<sid>/export")
def export_csv(sid):
    return api_export_csv(sid)

# ---------- Health ----------

@app.route("/api/health")
def api_health():
    data = load_data()
    return jsonify({
        "ok": True,
        "sessions": len(data["sessions"]),
        "records": len(data["records"]),
        "active_sessions": sum(1 for s in data["sessions"] if s.get("active"))
    })

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    app.run(debug=True, port=5000)
