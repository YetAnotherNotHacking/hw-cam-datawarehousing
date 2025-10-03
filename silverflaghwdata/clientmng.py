import json, os, argparse

CONFIG_FILE = "client_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {"server": "", "apikey": ""}

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def main():
    p = argparse.ArgumentParser(description="Manage client config")
    sub = p.add_subparsers(dest="cmd")

    s = sub.add_parser("set")
    s.add_argument("--server")
    s.add_argument("--apikey")

    g = sub.add_parser("show")

    args = p.parse_args()
    cfg = load_config()

    if args.cmd == "set":
        if args.server:
            cfg["server"] = args.server
        if args.apikey:
            cfg["apikey"] = args.apikey
        save_config(cfg)
        print("Config updated")
    elif args.cmd == "show":
        print(json.dumps(cfg, indent=2))
    else:
        p.print_help()

if __name__ == "__main__":
    main()
