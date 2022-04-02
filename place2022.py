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
        
        # check if file or already converted
        if not isfile(fp):
            continue
        if isfile(ft) or isfile(ft.replace("_0", "")):
            log.info("Skipping " + f)
            continue
        # merge multiple images
        if "_" in f and not "_0" in f:
            log.info("Skipping (Merge) " + f)
            continue
        
        files.append(f)

    # Convert
    for i, f in enumerate(files):
        fp = join(path, f)
        ft = join(target, f).replace(".png", ".webp")
        
        # merge multiple images
        if "_0" in f:
            log.info(f"({i}/{len(files)}) Merging {fp}")
            
            images = [Image.open(fp), Image.open(fp.replace("_0", "_1"))]
            
            widths, heights = zip(*(i.size for i in images))

            total_width = sum(widths)
            max_height = max(heights)

            new_im = Image.new('RGB', (total_width, max_height))

            x_offset = 0
            for im in images:
              new_im.paste(im, (x_offset,0))
              x_offset += im.size[0]
            
            new_im.save(ft.replace("_0", ""), lossless = True, method = 6)
            continue
        
        # convert to webp
        log.info(f"({i}/{len(files)}) Converting {fp}")
        im = Image.open(fp)
        im.save(ft, lossless = True, method = 6)


def gen_json():
    path = "frames/webp"
    files = [join(path, f) for f in listdir(path) if isfile(join(path, f))]
    
    frames = {"frames": sorted(files)}
    log.info("Saving frames.json")
    with open("frames/frames.json", 'w') as f:
        json.dump(frames, f)


def update_web():
    convert()
    gen_json()

        
if __name__ == "__main__":
    output_dir = "frames"
    
    makedirs(output_dir, exist_ok=True)
    
    token = get_token()
    log.info("Got Token: " + token)
    req_counter = 0

    while True:
        req_counter += 1
        if req_counter > 500:
            token = get_token()
            log.info("Got Token: " + token)
            req_counter = 0
            update_web()
    
        urls = get_image_url(token)
        
        curr = math.floor(time.time())

        for i, url in enumerate(urls):
            filename = "{}_{}.png".format(curr, i)
            path = join(output_dir, filename)

            req = requests.get(url)
            log.info("Saving image: " + filename)
            with open(path, "wb") as f:
                f.write(req.content)
            
        time.sleep(30)

