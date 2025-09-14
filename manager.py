import time
import os

program_root_path = os.getcwd() 
supported_states = ['alabama']
state_scraper_path = "states/"

for state in supported_states:
    state_path = f"{program_root_path}{state_scraper_path}{state}.py"