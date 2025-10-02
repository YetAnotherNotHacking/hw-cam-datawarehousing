import sys
import argparse
from silverflaghwdata.states import stateScrapers, run_all
import silverflaghwdata.manager as management

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=str, help="Run a specific state scraper")
    parser.add_argument("--list", action="store_true", help="List available states")
    parser.add_argument("--better", action="store_true", help="Show better supported states")
    args = parser.parse_args()

    if args.list:
        management.list_states(better=args.better)
        return

    if args.state:
        state = args.state.lower()
        if state in stateScrapers:
            stateScrapers[state]()
        else:
            print("Unknown state:", state)
    else:
        run_all()

if __name__ == "__main__":
    main()