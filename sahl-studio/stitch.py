from PIL import Image
import glob, os, sys
# Header heights (px at 375 wide) of each showcase site's sticky header. Add new sites here.
HDR = {"barber": 92, "dental": 69, "restaurant": 52}
sites = sys.argv[1:] or list(HDR)
for site in sites:
    hh = HDR.get(site, 64)
    files = sorted(f for f in glob.glob(f"frames/{site}/*.jpg") if not f.endswith("header.jpg"))
    ys = [int(os.path.basename(f)[:4]) for f in files]
    H = ys[-1] + 812
    tall = Image.new("RGB", (375, H), (10, 10, 10))
    for f, y in zip(files, ys):
        im = Image.open(f).convert("RGB")
        if im.size != (375, 812): im = im.resize((375, 812), Image.LANCZOS)
        tall.paste(im, (0, y))
    tall.save(f"frames/{site}_tall.png")
    head = Image.open(f"frames/{site}/header.jpg").convert("RGB")
    s = head.size[0] / 375
    head.crop((0, 0, head.size[0], int(hh * s))).save(f"frames/{site}_header.png")
    # top frame with header for stills (cover, posts)
    head.save(f"frames/{site}_top.png")
    print(site, tall.size, head.size)
