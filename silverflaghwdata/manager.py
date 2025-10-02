import os

supportedStates = []
betterSupportedStates = []

try:
    for item in os.listdir("silverflaghwdata/states/"):
        if item.endswith(".py") and "__init__" not in item and "__pycache__" not in item:
            supportedStates.append(item[:-3].capitalize())
except Exception as e:
    print(f"Failed to list the directories for the scrapers. Try reinstalling through pip.\nError: {e}")
    exit()

def list_states(better=False):
    if better:
        print("Better supported states:", betterSupportedStates)
    else:
        print("Loaded scrapers for states:", supportedStates)
