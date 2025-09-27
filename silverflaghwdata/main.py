import sys
from silverflaghwdata.states import stateScrapers, run_all

def main():
    if len(sys.argv) > 1:
        state = sys.argv[1].lower()
        if state in stateScrapers:
            stateScrapers[state]()
        else:
            print("Unknown state:", state)
    else:
        run_all()


if __name__ == "__main__":
    main()