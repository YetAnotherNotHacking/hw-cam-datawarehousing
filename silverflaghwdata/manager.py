import os

supportedStates = []
betterSupportedStates = []

try:
    for item in os.listdir("silverflaghwdata/states/"):
        if item.endswith(".py") and "__init__" not in item and "__pycache__" not in item:
            supportedStates.append(item[:-3])
except Exception as e:
    print(f"Failed to list the directories for the scrapers. This isn't a huge problem, as the script should run anyway.\nError: {e}")
    print(f"Falling back to hardcoded list...")
    supportedStates.append(['kansas', 'indiana', 'minnesota', 'idaho', 'florida', 'deleware', 'iowa', 'alaska', 'maryland', 'connecticut', 'california', 'mississippi', 'michigan', 'kentucky', 'arizona', 'alabama', 'louisiana', 'illinois', 'arkansas', 'maine', 'massachusetts', 'georgia', 'colorado'])

def list_states(better=False):
    if better:
        print("Better supported states:", betterSupportedStates)
    else:
        print("Loaded scrapers for states:", supportedStates)

list_states()