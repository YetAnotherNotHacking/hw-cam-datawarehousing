import pkgutil, importlib, threading

stateScrapers = {}

for _, name, _ in pkgutil.iter_modules(__path__):
    mod = importlib.import_module(f"{__name__}.{name}")
    if hasattr(mod, "doScrape"):
        stateScrapers[name] = mod.doScrape

def run_all():
    threads = []
    for fn in stateScrapers.values():
        t = threading.Thread(target=fn)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
