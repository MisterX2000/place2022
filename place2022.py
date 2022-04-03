from os import listdir, makedirs
from os.path import isfile, join
from PIL import Image
import json
import logging
from logging.handlers import TimedRotatingFileHandler
from get import get_token, get_image_url
import requests
import math
import time
import threading


# region Logger
logFormatter = logging.Formatter("[%(asctime)s]%(levelname)-6s %(module)-8s: %(message)s", "%d.%m.%Y %H:%M:%S")
log = logging.getLogger()
log.setLevel(logging.INFO)

makedirs("logs", exist_ok=True)
fileHandler = TimedRotatingFileHandler(join("logs", __name__ + ".log"), when="midnight", interval=1, backupCount=30)
fileHandler.setFormatter(logFormatter)
log.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
log.addHandler(consoleHandler)
# endregion


def convert():
    path = "frames/png"
    target = "frames/webp"
    
    files = []
    
    # Get all files
    for f in listdir(path):
        fp = join(path, f)
        ft = join(target, f).replace(".png", ".webp")
        
        
        if not isfile(fp):
            continue
        # merge multiple images
        if "_" in f and not "_0" in f:
            #log.info("WEBU: Skipping (Merge) " + f)
            continue
        # check if file or already converted
        if isfile(ft) or isfile(ft.replace("_0", "")):
            #log.info("WEBU: Skipping " + f)
            continue
        
        files.append(f)

    # Convert
    for i, f in enumerate(files):
        fp = join(path, f)
        ft = join(target, f).replace(".png", ".webp")
        
        # merge multiple images
        if "_0" in f:
            log.info(f"WEBU: ({i+1}/{len(files)}) Merging {fp}")

            if isfile(fp.replace("_0", "_3")):
                images = [Image.open(fp), Image.open(fp.replace("_0", "_1")), Image.open(fp.replace("_0", "_2")), Image.open(fp.replace("_0", "_3"))]
                new_im = Image.new('RGB', (2000, 2000))
            else:
                images = [Image.open(fp), Image.open(fp.replace("_0", "_1"))]
                new_im = Image.new('RGB', (2000, 1000))

            for i, im in enumerate(images):
                x = 0 if (i == 0 or i == 2) else 1000
                y = 0 if (i == 0 or i == 1) else 1000
                new_im.paste(im, (x, y))
            
            new_im.save(ft.replace("_0", ""), lossless = True, method = 6)
            continue
        
        # convert to webp
        log.info(f"WEBU: ({i+1}/{len(files)}) Converting {fp}")
        im = Image.open(fp)
        im.save(ft, lossless = True, method = 6)


def gen_json():
    path = "frames/webp"
    files = [join(path, f) for f in listdir(path) if isfile(join(path, f))]
    
    frames = {"frames": sorted(files)}
    log.info("WEBU: Saving frames.json")
    with open("frames/frames.json", 'w') as f:
        json.dump(frames, f)


def update_web():
    log.info("WEBU: Updating web...")
    convert()
    gen_json()

        
if __name__ == "__main__":
    output_dir = "frames/png"
    sleep_time = 30
    token_timeout = 120
    
    makedirs(output_dir, exist_ok=True)
    
    req_counter = token_timeout

    while True:
        req_counter += 1
        if req_counter > token_timeout:
            token = get_token()
            log.info("MAIN: Got Token " + token)
            req_counter = 0

            # start web update thread if not already running
            if not threading.active_count() > 1:
                threading.Thread(target=update_web).start()
            else:
                log.info("MAIN: Web Update Thread already running")
            
    
        urls = get_image_url(token)
        
        curr = math.floor(time.time())

        for i, url in enumerate(urls):
            filename = f"{curr}_{i}.png"
            path = join(output_dir, filename)

            req = requests.get(url)
            log.info("MAIN: Saving image " + filename)
            with open(path, "wb") as f:
                f.write(req.content)
            
        time.sleep(sleep_time)

