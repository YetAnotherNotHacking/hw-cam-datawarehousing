import argparse
import os
import sys
import zipfile
import tempfile
import requests
import json
import shutil
from silverflaghwdata.states import stateScrapers, run_all
import silverflaghwdata.manager as management

CONFIG_FILE = "client_config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print("Missing client_config.json, run sfd-client --set ... (see docs) to configure.")
        sys.exit(1)
    with open(CONFIG_FILE) as f:
        return json.load(f)

def get_latest_output(state):
    data_dir = os.path.join("data", state.capitalize())
    if not os.path.exists(data_dir):
        print(f"No data found for {state}")
        sys.exit(1)
    timestamps = [d for d in os.listdir(data_dir) if d.isdigit()]
    if not timestamps:
        print(f"No timestamp dirs for {state}")
        sys.exit(1)
    latest = max(timestamps, key=int)
    return os.path.join(data_dir, latest)

def make_zip(srcdir):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    tmp.close()
    with zipfile.ZipFile(tmp.name, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(srcdir):
            for f in files:
                fpath = os.path.join(root, f)
                arcname = os.path.relpath(fpath, srcdir)
                z.write(fpath, arcname)
    return tmp.name

def upload_zip(cfg, zippath):
    with open(zippath, "rb") as f:
        files = {"file": (os.path.basename(zippath), f)}
        data = {"api_key": cfg["apikey"]}
        r = requests.post(f"{cfg['server']}/collect/uploadpack", data=data, files=files, verify=False)
    try:
        print(json.dumps(r.json(), indent=2))
    except:
        print(r.status_code, r.text)

def main():
    parser = argparse.ArgumentParser(description="Scraper client/uploader")
    parser.add_argument("--state", help="Run specific state scraper")
    parser.add_argument("--list", action="store_true", help="List available states")
    parser.add_argument("--all", action="store_true", help="Run all scrapers")
    parser.add_argument("--upload", action="store_true", help="Upload result after scraping")
    args = parser.parse_args()

    if args.list:
        management.list_states()
        return

    if args.state:
        state = args.state.lower()
        if state in stateScrapers:
            stateScrapers[state]()
            latest_dir = get_latest_output(state)
            if args.upload:
                cfg = load_config()
                zippath = make_zip(latest_dir)
                upload_zip(cfg, zippath)
                os.remove(zippath)
        else:
            print("Unknown state:", state)
    elif args.all:
        run_all()
        if args.upload:
            for state in management.supportedStates:
                latest_dir = get_latest_output(state.lower())
                cfg = load_config()
                zippath = make_zip(latest_dir)
                upload_zip(cfg, zippath)
                os.remove(zippath)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
