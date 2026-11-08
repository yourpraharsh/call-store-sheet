import base64, gzip, io, json, re, subprocess, sys, glob, hashlib
from PIL import Image
OLD_SHA = "cb00331c0737c1bf55615ad7abd370e584be227eb66aa144d39d926a851a19d8"
O = open("index.html", encoding="utf-8", newline="").read()
assert hashlib.sha256(O.encode()).hexdigest() == OLD_SHA, "repo page is not the expected version"
blob = "".join(open(p).read().strip() for p in sorted(glob.glob(".github/patch/p*.txt")))
ops = json.loads(gzip.decompress(base64.b64decode(blob)))

def find_img(h3, alt):
    g = O.find("<h3>" + h3 + "</h3>"); assert g > 0, h3
    m = re.compile(r'<img src="(data:image/[a-z]+;base64,[A-Za-z0-9+/=]+)"[^>]*?alt="' + re.escape(alt)).search(O, g)
    return Image.open(io.BytesIO(base64.b64decode(m.group(1).split(",", 1)[1]))).convert("RGB")

def to_uri(im):
    b = io.BytesIO(); im.save(b, "WEBP", quality=86, method=5)
    return "data:image/webp;base64," + base64.b64encode(b.getvalue()).decode()

def whiten(im):
    px = im.load(); c = px[14, 1100]; y = 1100
    while y > 1000 and sum(abs(a - b) for a, b in zip(px[14, y], c)) < 12: y -= 1
    for yy in range(y + 1, im.height):
        for x in range(im.width):
            if sum(abs(a - b) for a, b in zip(px[x, yy], c)) < 14: px[x, yy] = (255, 255, 255)
    return im

ok_src = find_img("Centred + Okay", "1 · Plain answers").crop((40, 1119, 500, 1176))
def okay(im):
    im.paste(ok_src, (40, 1119)); bg = im.getpixel((14, 1086))
    from PIL import ImageDraw
    ImageDraw.Draw(im).rectangle((60, 1066, 480, 1104), fill=bg); return im

C, A = "Centred + Okay", "A · Dark band"
assets = {
 "@@P0@@": lambda: to_uri(whiten(find_img(C, "2 · Video on top"))),
 "@@P1@@": lambda: to_uri(whiten(find_img(C, "4 · Video + collapsed"))),
 "@@P2@@": lambda: to_uri(whiten(find_img(C, "5 · Illustration on top"))),
 "@@P3@@": lambda: to_uri(okay(find_img(A, "1 · Plain answers"))),
 "@@P4@@": lambda: to_uri(whiten(okay(find_img(A, "2 · Video on top")))),
 "@@P5@@": lambda: to_uri(okay(find_img(A, "3 · Collapsed questions"))),
 "@@P6@@": lambda: to_uri(whiten(okay(find_img(A, "4 · Video + collapsed")))),
 "@@P7@@": lambda: to_uri(whiten(okay(find_img(A, "5 · Illustration on top")))),
}
def story():
    subprocess.run(["curl", "-fsSL", "-o", "story.mp4", "https://raw.githubusercontent.com/yourpraharsh/meesho-prototype/main/public/videos/self-pickup-story-v2.mp4"], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", "story.mp4", "-an", "-vf", "scale=480:-2,fps=24", "-c:v", "libx264", "-preset", "slow", "-crf", "30", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "story-small.mp4"], check=True)
    return "data:video/mp4;base64," + base64.b64encode(open("story-small.mp4", "rb").read()).decode()
assets["@@P8@@"] = story

spans = []
for pre, suf, new in ops:
    assert O.count(pre) == 1
    a0 = O.find(pre) + len(pre); a1 = O.find(suf, a0); assert a1 >= a0
    spans.append((a0, a1, new))
spans.sort(); out = []; cur = 0
for a0, a1, new in spans:
    assert a0 >= cur; out.append(O[cur:a0]); out.append(new); cur = a1
out.append(O[cur:]); N = "".join(out)
for k, f in assets.items():
    if k in N: N = N.replace(k, f())
assert "@@P" not in N
for must in ("Clear Answers", "night-shift theme", "chosen-pill", "data-story", "What this tells us"):
    assert must in N, must
open("index.html", "w", encoding="utf-8", newline="").write(N)
print("updated", len(N))
