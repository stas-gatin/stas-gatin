"""Generate the animated SVG assets for the GitHub profile README.

Everything is plain SVG + SMIL so it animates inside GitHub's <img> sandbox
(no scripts, no external fonts).
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets"
OUT.mkdir(parents=True, exist_ok=True)

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"


# ---------------------------------------------------------------- hero ------

PHRASES = [
    "flying a statically unstable aircraft",
    "teaching a hexapod to walk with PPO",
    "running 4 neural nets on the Neural Engine",
    "writing flight firmware from scratch in C++",
]
SLOT = 5.0          # seconds per phrase
TYPE_T = 1.7        # typing duration
HOLD_UNTIL = 4.1    # erase starts here (relative to slot start)
ERASE_T = 0.55
CW = 12.0           # forced char width (textLength) at font-size 20
TOTAL = SLOT * len(PHRASES)


SHIFT = 0.15 + TYPE_T  # start the cycle with phrase 0 already typed, so frame 0 is never empty


def typing_timeline(i, n):
    """(time, chars) pairs for phrase i with n characters over the full cycle."""
    s = i * SLOT
    ev = [(s + 0.15 + k * TYPE_T / n, k) for k in range(1, n + 1)]
    ev += [(s + HOLD_UNTIL + (n - k) * ERASE_T / n, k) for k in range(n - 1, -1, -1)]
    ev.sort()
    state0 = ([c for t, c in ev if t <= SHIFT + 1e-9] or [0])[-1]
    shifted = sorted(((t - SHIFT) % TOTAL, c) for t, c in ev)
    pts = [(0.0, state0)] + [(t, c) for t, c in shifted if t > 1e-6]
    return sorted({round(t, 4): c for t, c in pts}.items())


def state_at(pts, t):
    return [c for tt, c in pts if tt <= t + 1e-9][-1]


def smil_discrete(attr, pts, fmt):
    key_times = ";".join(f"{t / TOTAL:.5f}" for t, _ in pts)
    values = ";".join(fmt(c) for _, c in pts)
    return (f'<animate attributeName="{attr}" dur="{TOTAL}s" repeatCount="indefinite" '
            f'calcMode="discrete" keyTimes="{key_times}" values="{values}"/>')


def hero():
    W, H = 1280, 400
    tx, ty = 116, 298  # terminal text origin
    clips, lines, timelines = [], [], []
    for i, p in enumerate(PHRASES):
        n = len(p)
        pts = typing_timeline(i, n)
        timelines.append(pts)
        # the static width is the frame shown wherever SMIL does not run
        clips.append(
            f'<clipPath id="c{i}"><rect x="{tx}" y="{ty - 22}" height="30" width="{pts[0][1] * CW:.1f}">'
            f'{smil_discrete("width", pts, lambda c: f"{c * CW:.1f}")}</rect></clipPath>')
        # WebKit ignores a zero-width clip and would draw every phrase at once,
        # so phrases are also hidden outright whenever they have no characters.
        vis = lambda c: "visible" if c > 0 else "hidden"
        lines.append(
            f'<text x="{tx}" y="{ty}" clip-path="url(#c{i})" textLength="{n * CW:.1f}" '
            f'lengthAdjust="spacing" visibility="{vis(pts[0][1])}">{p}'
            f'{smil_discrete("visibility", pts, vis)}</text>')
    # cursor sits after whichever phrase is currently on screen
    times = sorted({t for pts in timelines for t, _ in pts})
    cursor_pts = [(t, sum(state_at(pts, t) for pts in timelines)) for t in times]
    cursor_x0 = tx + cursor_pts[0][1] * CW + 2
    cursor_anim = smil_discrete("x", cursor_pts, lambda c: f"{tx + c * CW + 2:.1f}")

    # attitude indicator geometry
    cx, cy, r = 1034, 200, 128
    ladder = []
    for deg in (-20, -10, 10, 20):
        y = cy - deg * 3.2
        half = 34 if abs(deg) == 20 else 22
        ladder.append(f'<line x1="{cx - half}" y1="{y}" x2="{cx + half}" y2="{y}"/>')
        ladder.append(f'<text x="{cx + half + 8}" y="{y + 4}">{abs(deg)}</text>')
        ladder.append(f'<text x="{cx - half - 8}" y="{y + 4}" text-anchor="end">{abs(deg)}</text>')
    for deg in (-15, -5, 5, 15):
        y = cy - deg * 3.2
        ladder.append(f'<line x1="{cx - 10}" y1="{y}" x2="{cx + 10}" y2="{y}" opacity=".6"/>')

    import math
    ticks = []
    for a in (-60, -45, -30, -20, -10, 10, 20, 30, 45, 60):
        rad = math.radians(a - 90)
        long_ = a in (-60, -30, 30, 60)
        r1, r2 = r + 6, r + (20 if long_ else 13)
        ticks.append(
            f'<line x1="{cx + r1 * math.cos(rad):.1f}" y1="{cy + r1 * math.sin(rad):.1f}" '
            f'x2="{cx + r2 * math.cos(rad):.1f}" y2="{cy + r2 * math.sin(rad):.1f}"/>')

    # step response decoration (underdamped second order), drawn along the bottom
    step = []
    x0, x1, yb, amp = 60, 1220, 382, 34
    for k in range(0, 241):
        t = k / 240
        tt = t * 9
        zeta, wn = 0.28, 1.6
        wd = wn * math.sqrt(1 - zeta ** 2)
        yv = 1 - math.exp(-zeta * wn * tt) * (math.cos(wd * tt) + zeta / math.sqrt(1 - zeta ** 2) * math.sin(wd * tt))
        step.append(f"{x0 + t * (x1 - x0):.1f},{yb - yv * amp:.1f}")
    step_path = "M" + " L".join(step)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Stanislav Gatin. The whole stack of a machine, from firmware to learned policies.">
<title>Stanislav Gatin</title>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#04070e"/>
    <stop offset=".55" stop-color="#081326"/>
    <stop offset="1" stop-color="#0c2146"/>
  </linearGradient>
  <radialGradient id="glow" cx="{cx}" cy="{cy}" r="300" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#2f81f7" stop-opacity=".32"/>
    <stop offset="1" stop-color="#2f81f7" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="glow2" cx="160" cy="40" r="420" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#a371f7" stop-opacity=".16"/>
    <stop offset="1" stop-color="#a371f7" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="name" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#ffffff"/>
    <stop offset="1" stop-color="#9ecbff"/>
  </linearGradient>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#1b5fb8"/>
    <stop offset="1" stop-color="#0f3b78"/>
  </linearGradient>
  <linearGradient id="ground" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#0b1c36"/>
    <stop offset="1" stop-color="#050c18"/>
  </linearGradient>
  <linearGradient id="fade" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#fff" stop-opacity="0"/>
    <stop offset=".15" stop-color="#fff" stop-opacity="1"/>
    <stop offset=".85" stop-color="#fff" stop-opacity="1"/>
    <stop offset="1" stop-color="#fff" stop-opacity="0"/>
  </linearGradient>
  <mask id="fadeMask"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>
  <pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse">
    <circle cx="1.5" cy="1.5" r="1.1" fill="#9ecbff" opacity=".13"/>
  </pattern>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="22"/></clipPath>
  <clipPath id="adi"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>
  {"".join(clips)}
</defs>

<g clip-path="url(#card)">
  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  <rect width="{W}" height="{H}" fill="url(#dots)"/>
  <rect width="{W}" height="{H}" fill="url(#glow2)"/>
  <rect width="{W}" height="{H}" fill="url(#glow)"/>

  <!-- step response along the bottom: the signature of a control loop settling -->
  <g mask="url(#fadeMask)">
    <line x1="{x0}" y1="{yb - amp}" x2="{x1}" y2="{yb - amp}" stroke="#9ecbff" stroke-opacity=".18" stroke-dasharray="4 6"/>
    <path id="step" d="{step_path}" fill="none" stroke="#2f81f7" stroke-width="2" stroke-opacity=".5" stroke-linecap="round"/>
    <g>
      <circle r="9" fill="#5fb3ff" fill-opacity=".18"/>
      <circle r="3.5" fill="#9ecbff"/>
      <animateMotion dur="7s" repeatCount="indefinite" calcMode="spline" keyTimes="0;1" keySplines=".4 0 .6 1" path="{step_path}"/>
    </g>
  </g>

  <!-- left column -->
  <g font-family="{SANS}">
    <text x="72" y="92" font-family="{MONO}" font-size="15" letter-spacing="3" fill="#5fb3ff">FOUNDER @ CURRENTSKY  ·  AI ENGINEERING</text>
    <text x="68" y="172" font-size="76" font-weight="800" fill="url(#name)" letter-spacing="-1.5">Stanislav Gatin</text>
    <text x="72" y="222" font-size="25" fill="#b6c4da">The whole stack of a machine.
      <tspan fill="#ffffff" font-weight="600">From firmware to learned policies.</tspan>
    </text>
  </g>

  <!-- terminal -->
  <rect x="72" y="{ty - 42}" width="636" height="60" rx="12" fill="#060b16" fill-opacity=".85" stroke="#1f3b63"/>
  <g font-family="{MONO}" font-size="20" fill="#e6edf3">
    <text x="92" y="{ty}" fill="#3fb950" font-weight="700">$</text>
    {"".join(lines)}
    <rect y="{ty - 18}" width="10" height="22" x="{cursor_x0:.1f}" fill="#5fb3ff">
      {cursor_anim}
      <animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1s" repeatCount="indefinite"/>
    </rect>
  </g>

  <!-- attitude indicator -->
  <circle cx="{cx}" cy="{cy}" r="{r + 44}" fill="none" stroke="#2f81f7" stroke-opacity=".28" stroke-dasharray="2 9">
    <animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="60s" repeatCount="indefinite"/>
  </circle>
  <circle cx="{cx}" cy="{cy}" r="{r + 58}" fill="none" stroke="#a371f7" stroke-opacity=".16" stroke-dasharray="40 14 4 14">
    <animateTransform attributeName="transform" type="rotate" from="360 {cx} {cy}" to="0 {cx} {cy}" dur="90s" repeatCount="indefinite"/>
  </circle>

  <g clip-path="url(#adi)">
    <g>
      <animateTransform attributeName="transform" type="rotate" dur="11s" repeatCount="indefinite" calcMode="spline"
        values="-9 {cx} {cy};7 {cx} {cy};-4 {cx} {cy};11 {cx} {cy};-2 {cx} {cy};-9 {cx} {cy}"
        keyTimes="0;.22;.41;.63;.82;1"
        keySplines=".45 0 .55 1;.45 0 .55 1;.45 0 .55 1;.45 0 .55 1;.45 0 .55 1"/>
      <g>
        <animateTransform attributeName="transform" type="translate" dur="13s" repeatCount="indefinite" calcMode="spline"
          values="0 6;0 -14;0 10;0 -6;0 6" keyTimes="0;.3;.55;.8;1"
          keySplines=".45 0 .55 1;.45 0 .55 1;.45 0 .55 1;.45 0 .55 1"/>
        <rect x="{cx - 260}" y="{cy - 260}" width="520" height="260" fill="url(#sky)"/>
        <rect x="{cx - 260}" y="{cy}" width="520" height="260" fill="url(#ground)"/>
        <line x1="{cx - 260}" y1="{cy}" x2="{cx + 260}" y2="{cy}" stroke="#9ecbff" stroke-width="2.5"/>
        <g stroke="#e6edf3" stroke-width="2" stroke-linecap="round" fill="#e6edf3" opacity=".85"
           font-family="{MONO}" font-size="11">
          {"".join(ladder)}
        </g>
      </g>
    </g>
  </g>

  <!-- fixed bezel, roll scale and aircraft symbol -->
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#2f81f7" stroke-opacity=".9" stroke-width="3"/>
  <circle cx="{cx}" cy="{cy}" r="{r + 4}" fill="none" stroke="#9ecbff" stroke-opacity=".25" stroke-width="1"/>
  <g stroke="#9ecbff" stroke-width="2" stroke-opacity=".75" stroke-linecap="round">{"".join(ticks)}</g>
  <path d="M{cx} {cy - r - 4} l-8 -14 h16 z" fill="#ffb020"/>
  <g stroke="#ffb020" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" fill="none">
    <path d="M{cx - 62} {cy} h50 l12 14 l12 -14 h50"/>
  </g>
  <circle cx="{cx}" cy="{cy}" r="4" fill="#ffb020"/>
  <text x="{cx}" y="{cy + r + 34}" text-anchor="middle" font-family="{MONO}" font-size="12" letter-spacing="4" fill="#9ecbff" fill-opacity=".55">KAIROS · ATTITUDE</text>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="22" fill="none" stroke="#9ecbff" stroke-opacity=".14"/>
</svg>
'''


# ------------------------------------------------------------- numbers -----
# Real data, as of Sep 2026 (see README comments for sources).
MONTHLY = [0, 16, 61, 51, 202, 229, 295, 101, 85]          # GitHub contributions Jan..Sep 2026
LOC = [("Swift", 34342, "#f05138"), ("C++", 6713, "#2f81f7"), ("Python", 6514, "#e3b341")]

CELLS = [
    # label, big, unit, line1, line2, accent, viz
    ("UAV", "~1,500", "h", "over six years building", "a thrust vectored UAV", "#2f81f7", "protos"),
    ("REINFORCEMENT LEARNING", "450M", "+", "RL steps simulated, about", "4,000 hours of walking", "#a371f7", "curve"),
    ("RL HEXAPOD", "98", "%", "goals reached on rocky", "ground, with zero falls", "#3fb950", "segments"),
    ("COMPUTER VISION", "35→6", "ms", "YOLO inference on iPhone", "after an FP16 rebuild", "#f0883e", "latency"),
    ("GITHUB · 2026", "1,000", "+", "contributions this year,", "most in private repos", "#3fb950", "monthly"),
    ("CODE", "47k", "+", "lines written since May", "across four projects", "#f05138", "loc"),
    ("PULL REQUESTS", "~150", "", "merged into the flight", "stack since May", "#a371f7", "prs"),
    ("RL HEXAPOD", "0", "", "lines of hand written", "gait. It taught itself", "#db61a2", "code"),
]

THEMES = {
    "dark": dict(card="#0d1117", border="#30363d", text="#e6edf3", sub="#8b949e", faint="#21262d", glow=.16),
    "light": dict(card="#ffffff", border="#d0d7de", text="#1f2328", sub="#59636e", faint="#eaeef2", glow=.10),
}


def viz(kind, x, y, w, accent, c):
    """Mini visual in the band [y, y+44] of a cell, x..x+w."""
    if kind == "protos":
        xs = [x + 6, x + w * .5, x + w - 8]
        out = [f'<line x1="{xs[0]}" y1="{y + 14}" x2="{xs[2]}" y2="{y + 14}" stroke="{c["border"]}" stroke-width="2"/>',
               f'<line x1="{xs[0]}" y1="{y + 14}" x2="{xs[2]}" y2="{y + 14}" stroke="{accent}" stroke-width="2" stroke-dasharray="3 5"/>']
        for i, (px, lab) in enumerate(zip(xs, ("I", "II", "III"))):
            out.append(f'<circle cx="{px:.1f}" cy="{y + 14}" r="6" fill="{accent if i == 2 else c["card"]}" stroke="{accent}" stroke-width="2"/>')
            out.append(f'<text x="{px:.1f}" y="{y + 40}" text-anchor="middle" font-family="{MONO}" font-size="12" fill="{c["sub"]}">{lab}</text>')
        out.append(f'''<circle cx="{xs[2]:.1f}" cy="{y + 14}" r="6" fill="none" stroke="{accent}" stroke-width="1.5">
      <animate attributeName="r" values="6;15" dur="2.2s" repeatCount="indefinite"/>
      <animate attributeName="stroke-opacity" values=".8;0" dur="2.2s" repeatCount="indefinite"/></circle>''')
        return "".join(out)
    if kind == "curve":
        import math, random
        rnd = random.Random(7)
        pts = []
        for k in range(61):
            t = k / 60
            v = 1 - math.exp(-3.2 * t) + rnd.uniform(-.05, .05) * (1 - t)
            pts.append((x + t * w, y + 40 - max(0, min(1, v)) * 36))
        line = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts)
        area = line + f" L{x + w:.1f},{y + 40} L{x:.1f},{y + 40} Z"
        return (f'<path d="{area}" fill="url(#area{accent[1:]})"/>'
                f'<path d="{line}" fill="none" stroke="{accent}" stroke-width="2" stroke-linejoin="round"/>'
                f'<g><circle r="4" fill="{accent}"/><animateMotion dur="5s" repeatCount="indefinite" path="{line}"/></g>')
    if kind == "segments":
        n, gap = 50, 1.6
        sw = (w - gap * (n - 1)) / n
        return "".join(
            f'<rect x="{x + i * (sw + gap):.1f}" y="{y + 10}" width="{sw:.1f}" height="16" rx="1.2" '
            f'fill="{accent if i < 49 else c["faint"]}"/>' for i in range(n))
    if kind == "latency":
        full = w - 64
        return (f'<text x="{x}" y="{y + 12}" font-family="{MONO}" font-size="11" fill="{c["sub"]}">FP32</text>'
                f'<rect x="{x + 40}" y="{y + 3}" width="{full:.1f}" height="10" rx="5" fill="{c["faint"]}"/>'
                f'<text x="{x + 40 + full + 6:.1f}" y="{y + 12}" font-family="{MONO}" font-size="11" fill="{c["sub"]}">35</text>'
                f'<text x="{x}" y="{y + 34}" font-family="{MONO}" font-size="11" fill="{c["sub"]}">FP16</text>'
                f'<rect x="{x + 40}" y="{y + 25}" width="{full * 6 / 35:.1f}" height="10" rx="5" fill="{accent}"/>'
                f'<text x="{x + 40 + full * 6 / 35 + 6:.1f}" y="{y + 34}" font-family="{MONO}" font-size="11" fill="{accent}">6</text>')
    if kind == "monthly":
        n = len(MONTHLY); gap = 6
        bw = (w - gap * (n - 1)) / n
        mx = max(MONTHLY)
        out = []
        for i, v in enumerate(MONTHLY):
            h = max(2, v / mx * 30)
            out.append(f'<rect x="{x + i * (bw + gap):.1f}" y="{y + 30 - h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="2" '
                       f'fill="{accent}" fill-opacity="{.35 + .65 * v / mx:.2f}"/>')
            out.append(f'<text x="{x + i * (bw + gap) + bw / 2:.1f}" y="{y + 44}" text-anchor="middle" font-family="{MONO}" '
                       f'font-size="10" fill="{c["sub"]}">{"JFMAMJJAS"[i]}</text>')
        return "".join(out)
    if kind == "loc":
        tot = sum(v for _, v, _ in LOC)
        out, cx_ = [], x
        out.append(f'<clipPath id="locclip"><rect x="{x}" y="{y + 6}" width="{w}" height="12" rx="6"/></clipPath><g clip-path="url(#locclip)">')
        for name, v, col in LOC:
            ww = w * v / tot
            out.append(f'<rect x="{cx_:.1f}" y="{y + 6}" width="{ww:.1f}" height="12" fill="{col}"/>')
            cx_ += ww
        out.append("</g>")
        lx = x
        for name, v, col in LOC:
            out.append(f'<circle cx="{lx + 4}" cy="{y + 36}" r="4" fill="{col}"/>'
                       f'<text x="{lx + 13}" y="{y + 40}" font-family="{MONO}" font-size="11" fill="{c["sub"]}">{name}</text>')
            lx += 13 + len(name) * 7 + 18
        return "".join(out)
    if kind == "prs":
        import random
        rnd = random.Random(3)
        cols, rows, s, g = 30, 5, 6.3, 2
        return "".join(
            f'<rect x="{x + i * (s + g):.1f}" y="{y + 2 + j * (s + g):.1f}" width="{s}" height="{s}" rx="1.4" fill="{accent}" '
            f'fill-opacity="{rnd.choice((.25, .45, .7, 1)):.2f}"/>' for j in range(rows) for i in range(cols))
    if kind == "code":
        return (f'<rect x="{x}" y="{y + 2}" width="{w}" height="34" rx="8" fill="{c["faint"]}"/>'
                f'<text x="{x + 12}" y="{y + 24}" font-family="{MONO}" font-size="13" fill="{c["sub"]}">'
                f'<tspan fill="{accent}">gait</tspan> = policy(obs)</text>')
    return ""


def numbers(theme):
    c = THEMES[theme]
    W, gap, head = 1280, 20, 40
    ch = 250
    cw = (W - gap * 3) / 4
    H = head + ch * 2 + gap
    cells, grads = [], []
    for idx, (label, big, unit, l1, l2, accent, kind) in enumerate(CELLS):
        col, row = idx % 4, idx // 4
        x, y = col * (cw + gap), head + row * (ch + gap)
        gid = f"g{idx}"
        grads.append(f'<radialGradient id="{gid}" cx="{x + cw:.1f}" cy="{y}" r="{cw * .9:.1f}" gradientUnits="userSpaceOnUse">'
                     f'<stop offset="0" stop-color="{accent}" stop-opacity="{c["glow"]}"/>'
                     f'<stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient>')
        cells.append(f'''
  <g>
    <rect x="{x + 1:.1f}" y="{y + 1}" width="{cw - 2:.1f}" height="{ch - 2}" rx="16" fill="{c['card']}" stroke="{c['border']}"/>
    <rect x="{x + 1:.1f}" y="{y + 1}" width="{cw - 2:.1f}" height="{ch - 2}" rx="16" fill="url(#{gid})"/>
    <circle cx="{x + 30:.1f}" cy="{y + 32}" r="4" fill="{accent}"/>
    <text x="{x + 42:.1f}" y="{y + 36.5}" font-family="{MONO}" font-size="12" letter-spacing="1.5" fill="{accent}">{label}</text>
    <text x="{x + 25:.1f}" y="{y + 104}" font-size="60" font-weight="800" fill="{c['text']}" letter-spacing="-1.5">{big}<tspan font-size="30" font-weight="700" fill="{accent}" dx="4">{unit}</tspan></text>
    <text x="{x + 28:.1f}" y="{y + 138}" font-size="18" fill="{c['sub']}">{l1}</text>
    <text x="{x + 28:.1f}" y="{y + 162}" font-size="18" fill="{c['sub']}">{l2}</text>
    {viz(kind, x + 28, y + 184, cw - 56, accent, c)}
  </g>''')
    areas = "".join(
        f'<linearGradient id="area{a[1:]}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{a}" stop-opacity=".35"/>'
        f'<stop offset="1" stop-color="{a}" stop-opacity="0"/></linearGradient>' for a in {cell[5] for cell in CELLS})
    header = (f'<text x="2" y="18" font-family="{MONO}" font-size="13" letter-spacing="4" fill="{c["sub"]}">BY THE NUMBERS</text>'
              f'<text x="{W - 2}" y="18" text-anchor="end" font-family="{MONO}" font-size="13" letter-spacing="4" fill="{c["sub"]}">AS OF SEP 2026</text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="By the numbers: about 1,500 hours building a thrust vectored UAV; over 450 million RL simulation steps; 98 percent of goals reached by the RL hexapod with zero falls; YOLO inference from 35 to 6 ms; over 1,000 GitHub contributions in 2026; over 47 thousand lines of code since May; about 150 pull requests merged; zero lines of hand written gait.">
<title>By the numbers</title>
<defs>{"".join(grads)}{areas}</defs>
<g font-family="{SANS}">{header}{"".join(cells)}
</g>
</svg>
'''


# -------------------------------------------------------------- footer -----

def footer():
    W, H = 1280, 120
    import math
    pts = []
    for k in range(0, 321):
        t = k / 320
        y = 60 + 16 * math.sin(t * math.pi * 6) * math.exp(-2.2 * t)
        pts.append(f"{40 + t * 1200:.1f},{y:.1f}")
    d = "M" + " L".join(pts)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Control, perception, learning.">
<title>Control, perception, learning</title>
<defs>
  <linearGradient id="f" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#2f81f7" stop-opacity="0"/>
    <stop offset=".2" stop-color="#2f81f7"/>
    <stop offset=".6" stop-color="#a371f7"/>
    <stop offset="1" stop-color="#3fb950" stop-opacity="0"/>
  </linearGradient>
</defs>
<path d="{d}" fill="none" stroke="url(#f)" stroke-width="2.5" stroke-linecap="round"/>
<g>
  <circle r="9" fill="#a371f7" fill-opacity=".2"/>
  <circle r="3.5" fill="#a371f7"/>
  <animateMotion dur="6s" repeatCount="indefinite" calcMode="spline" keyTimes="0;1" keySplines=".4 0 .6 1" path="{d}"/>
  <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.1;.85;1" dur="6s" repeatCount="indefinite"/>
</g>
<text x="640" y="108" text-anchor="middle" font-family="{MONO}" font-size="14" letter-spacing="5" fill="#8b949e">CONTROL · PERCEPTION · LEARNING</text>
</svg>
'''


(OUT / "hero.svg").write_text(hero())
(OUT / "numbers-dark.svg").write_text(numbers("dark"))
(OUT / "numbers-light.svg").write_text(numbers("light"))
(OUT / "footer.svg").write_text(footer())
for f in ("hero.svg", "numbers-dark.svg", "numbers-light.svg", "footer.svg"):
    print(f, (OUT / f).stat().st_size, "bytes")
