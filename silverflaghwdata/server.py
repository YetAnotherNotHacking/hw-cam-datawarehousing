from flask import Flask, request, abort, jsonify, send_from_directory
import os
import hashlib
import csv
import secrets
import json

app = Flask(__name__)

API_KEYS = {}
UPLOAD_DIR = None
INDEX_FILE = None
UPLOAD_INDEX = {}

def save_index():
    with open(INDEX_FILE, "w") as f:
        json.dump(UPLOAD_INDEX, f)
def load_index():
    global UPLOAD_INDEX
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r") as f:
            UPLOAD_INDEX = json.load(f)
    else:
        UPLOAD_INDEX = {}

def configureServer(uploadDir, credFileLocation, host, port):
    global API_KEYS, UPLOAD_DIR, INDEX_FILE
    if not uploadDir:
        raise ValueError("--uploaddir is required")
    if not credFileLocation:
        raise ValueError("--credfilelocation is required")

    if not host:
        host = "0.0.0.0"
    if not port:
        port = 9443

    UPLOAD_DIR = str(uploadDir)
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    INDEX_FILE = os.path.join(UPLOAD_DIR, "index.json")
    load_index()

    print(f"Saving uploads to {UPLOAD_DIR}")
    API_KEYS = {}
    with open(credFileLocation) as f:
        print(f"Reading API users from {credFileLocation}")
        reader = csv.DictReader(f)
        usercount = 0
        for row in reader:
            usercount += 1
            API_KEYS[row["client_id"]] = row["api_key"]
        print(f"Loaded {usercount} API users")

@app.route("/collect/uploadpack", methods=["POST"])
def uploadpack():
    api_key = request.form.get("api_key")
    f = request.files.get("file")
    if not api_key or not f:
        abort(400, "Required components missing from request.")
    if api_key not in API_KEYS.values():
        abort(401, "Invalid API key.")

    while True:
        randname = secrets.token_hex(32) + ".zip"
        fullpath = os.path.join(UPLOAD_DIR, randname)
        if not os.path.exists(fullpath):
            break

    f.save(fullpath)
    ts = int(os.path.getmtime(fullpath))
    UPLOAD_INDEX[randname] = {"timestamp": ts}
    save_index()

    return jsonify({"status":"ok", "zip_id":randname, "timestamp":ts})

@app.route("/data/list", methods=["GET"])
def list_data():
    result = []
    for fname, meta in UPLOAD_INDEX.items():
        result.append({
            "zip_id": fname,
            "timestamp": meta["timestamp"],
            "download_url": f"/data/get/{fname}"
        })
    return jsonify(result)

@app.route("/data/get/<zipname>", methods=["GET"])
def get_zip(zipname):
    if zipname not in UPLOAD_INDEX:
        abort(404, "Not found")
    return send_from_directory(UPLOAD_DIR, zipname, as_attachment=True)


@app.route("/", methods=["GET"])
def index():
    routes = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != "static":
            routes.append({
                "endpoint": rule.endpoint,
                "methods": list(rule.methods - {"HEAD", "OPTIONS"}),
                "path": str(rule)
            })
    return jsonify(routes)

def doServer(uploadDir, host, port):
    print(f"Starting server on {host}:{port}")
    app.run(ssl_context="adhoc", host=host, port=port)

if __name__=="__main__":
    print("You cannot run this file directly. Please import it and use the doServer() function.")