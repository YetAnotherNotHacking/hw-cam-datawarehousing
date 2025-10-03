# server manager, manage settings and run server

import argparse
import csv
import os
import sys
import secrets
import pathlib
from silverflaghwdata.server import configureServer, doServer

def gen_creds_file(path):
    if os.path.exists(path):
        print(f"{path} already exists.")
        return
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["client_id", "api_key"])
        writer.writeheader()
    print(f"Created new creds file at {path}")

def add_cred(path, key=None, user=None):
    if not os.path.exists(path):
        print("Creds file not found. Use gen-creds first.")
        return
    api_key = key or secrets.token_hex(32)
    client_id = user or f"user_{secrets.token_hex(4)}"
    rows = []
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        if r["client_id"] == client_id:
            print(f"User {client_id} already exists")
            return
    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["client_id", "api_key"])
        writer.writerow({"client_id": client_id, "api_key": api_key})
    print(f"Added {api_key} to file as user {client_id}")

def remove_cred(path, user):
    if not os.path.exists(path):
        print("Unable to read file.")
        return
    rows = []
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    rows_new = [r for r in rows if r["client_id"] != user] # build a new list with everything but user
    if len(rows_new) == len(rows):
        print(f"No such user '{user}'")
        return
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["client_id", "api_key"])
        writer.writeheader()
        writer.writerows(rows_new)
    print(f"Removed the user {user}")

def main():
    parser = argparse.ArgumentParser(prog="sfdata-srvmng", description="SilverFlag Data Server Manager")
    sub = parser.add_subparsers(dest="cmd")

    run = sub.add_parser("run", help="Run the server")
    run.add_argument("--host", default="0.0.0.0")
    run.add_argument("--port", type=int, default="9443")
    run.add_argument("--uploaddir", required=True)
    run.add_argument("--credfilelocation", required=True)

    genc = sub.add_parser("gen-creds", help="Generate new empty creds file")
    genc.add_argument("path", help="Path of the cred file ot generate")

    addc = sub.add_parser("add", help="Add new credential")
    addc.add_argument("path", help="Path of the cred file to edit")
    addc.add_argument("--user", help="User/client id")
    addc.add_argument("--key", help="API key (if not supplied, generated)")

    remc = sub.add_parser("remove", help="Remove credential")
    remc.add_argument("path", help="Path of the cred file to edit")
    remc.add_argument("user", help="User/client id")

    args = parser.parse_args()

    if args.cmd == "gen-creds":
        gen_creds_file(args.path)
    elif args.cmd == "add":
        add_cred(args.path, args.key, args.user)
    elif args.cmd == "remove":
        remove_cred(args.path, args.user)
    elif args.cmd == "run":
        updir = pathlib.Path(args.uploaddir)
        updir.mkdir(parents=True, exist_ok=True)
        configureServer(updir, args.credfilelocation, args.host, args.port)
        doServer(args.uploaddir, args.host, args.port)
    else:
        print("Correct your usage.")
        parser.print_help()

if __name__ == "__main__":
    main()