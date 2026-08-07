"""
Generates stylized SVG poster cards for a small catalogue of FICTIONAL movies
(no real film titles/artwork, so there is no IP/copyright concern).
Each poster is a gradient panel with a marquee-style title + genre tag.
"""
import os

OUT_DIR = "static/posters"
os.makedirs(OUT_DIR, exist_ok=True)

# (id, title, genre, [hex1, hex2], accent)
MOVIES = [
    ("midnight_ember",   "Midnight Ember",        "DRAMA",       "#3a0d12", "#c1443c", "#d4af37"),
    ("silver_static",    "Silver Static",         "SCI-FI",      "#0b1024", "#1c3a5e", "#7ecbff"),
    ("the_last_reel",    "The Last Reel",         "MYSTERY",     "#141118", "#3d2b56", "#d4af37"),
    ("paper_moons",      "Paper Moons",           "ROMANCE",     "#2a0f28", "#7a2f5c", "#f2c14e"),
    ("iron_harbor",      "Iron Harbor",           "ACTION",      "#0f1a12", "#1f4d34", "#e0e0d8"),
    ("the_quiet_hour",   "The Quiet Hour",        "THRILLER",    "#0c0c14", "#242438", "#c1443c"),
    ("carousel_of_dust", "Carousel of Dust",      "FANTASY",     "#1a0f24", "#4a2a6b", "#f2c14e"),
    ("blue_static_noon", "Blue Static Noon",      "COMEDY",      "#0d1a1f", "#1b4a52", "#ffd166"),
    ("glass_horizon",    "Glass Horizon",         "ADVENTURE",   "#0a1420", "#1d3f63", "#7ecbff"),
    ("velvet_curtain",   "Velvet Curtain",        "MUSICAL",     "#240a17", "#6b1f3d", "#d4af37"),
]

def poster_svg(title, genre, c1, c2, accent):
    words = title.split()
    if len(words) > 1:
        mid = (len(words) + 1) // 2
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])
    else:
        line1, line2 = title, ""

    perfs = "".join(
        f'<rect x="6" y="{y}" width="14" height="8" rx="2" fill="#000" opacity="0.55"/>'
        f'<rect x="280" y="{y}" width="14" height="8" rx="2" fill="#000" opacity="0.55"/>'
        for y in range(14, 400, 26)
    )

    return f'''<svg viewBox="0 0 300 420" xmlns="http://www.w3.org/2000/svg" font-family="'Bebas Neue', 'Oswald', sans-serif">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{c2}"/>
      <stop offset="100%" stop-color="{c1}"/>
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="30%" r="70%">
      <stop offset="0%" stop-color="{accent}" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="{accent}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="300" height="420" fill="url(#bg)"/>
  <rect width="300" height="420" fill="url(#glow)"/>
  {perfs}
  <rect x="26" y="26" width="248" height="368" fill="none" stroke="{accent}" stroke-width="1.5" opacity="0.55"/>
  <text x="150" y="70" text-anchor="middle" fill="{accent}" font-size="12" letter-spacing="4" opacity="0.9">{genre}</text>
  <line x1="110" y1="84" x2="190" y2="84" stroke="{accent}" stroke-width="1" opacity="0.6"/>
  <text x="150" y="230" text-anchor="middle" fill="#f5f0e6" font-size="34" letter-spacing="1.5">{line1}</text>
  <text x="150" y="266" text-anchor="middle" fill="#f5f0e6" font-size="34" letter-spacing="1.5">{line2}</text>
  <g opacity="0.85">
    <circle cx="150" cy="330" r="16" fill="none" stroke="{accent}" stroke-width="2"/>
    <path d="M144 322 L160 330 L144 338 Z" fill="{accent}"/>
  </g>
  <text x="150" y="392" text-anchor="middle" fill="{accent}" font-size="10" letter-spacing="3" opacity="0.7">NOW SHOWING</text>
</svg>'''

manifest = []
for slug, title, genre, c1, c2, accent in MOVIES:
    svg = poster_svg(title, genre, c1, c2, accent)
    path = os.path.join(OUT_DIR, f"{slug}.svg")
    with open(path, "w") as f:
        f.write(svg)
    manifest.append({"slug": slug, "title": title, "genre": genre, "poster": f"posters/{slug}.svg"})

import json
with open("static/movies.json", "w") as f:
    json.dump(manifest, f, indent=2)

print(f"Generated {len(manifest)} posters into {OUT_DIR}/")
