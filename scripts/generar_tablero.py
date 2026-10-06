#!/usr/bin/env python3
"""Regenera profile-dark.svg y profile-light.svg con datos vivos de la API de GitHub.

Lo que se recalcula solo: los anos construyendo y el reparto de lenguajes. El resto
(stack, que construyo) es texto fijo de mas abajo, porque no hay API que lo sepa.

Los repos de servidores de juego se excluyen a proposito: son cientos de MB de assets
en Lua y C# que tapaban el TypeScript, que es lo que de verdad escribo.
"""
import base64, datetime, json, math, os, urllib.request

USUARIO = '0ikawaa'
EXCLUIR = {'Unity', 'UnityNetwork', 'Server-FiveM', 'vyper-rp', 'vyper-mu', 'Server', USUARIO}
TOKEN = os.environ.get('GITHUB_TOKEN', '')

STACK = ['TypeScript', 'React', 'Next.js', 'Tailwind', 'Prisma', 'PostgreSQL',
         'three.js', 'Vercel', 'Mercado Libre API', 'Odoo', 'Shopify']
FOCO = ['Fichas de producto con visor 3D y realidad aumentada',
        'Paneles internos: importaciones, stock, precios y rentabilidad',
        'Integraciones Mercado Libre <-> Odoo <-> Shopify']
EN_PRODUCCION = ['panel-ma', 'mundoshop', 'telas-harturo', 'web-maimpo']
COLOR_LANG = {'TypeScript': '#3178c6', 'JavaScript': '#f1e05a', 'CSS': '#663399',
              'HTML': '#e34c26', 'PHP': '#4F5D95', 'Otros': '#8b949e'}
# Cortar a dos letras da "TY" para TypeScript, asi que las siglas van a mano.
SIGLA = {'TypeScript': 'TS', 'JavaScript': 'JS', 'Python': 'PY', 'CSS': 'CSS',
         'HTML': 'HTML', 'PHP': 'PHP', 'C#': 'C#', 'Lua': 'LUA'}

OSCURO = {'bg': '#0d1117', 'card': '#161b22', 'bd': '#30363d', 'fg': '#e6edf3',
          'mut': '#8b949e', 'ac': '#3fb950', 'pill': '#21262d'}
CLARO  = {'bg': '#ffffff', 'card': '#f6f8fa', 'bd': '#d0d7de', 'fg': '#1f2328',
          'mut': '#636c76', 'ac': '#1a7f37', 'pill': '#eaeef2'}


def api(ruta):
    req = urllib.request.Request('https://api.github.com' + ruta,
                                 headers={'Accept': 'application/vnd.github+json',
                                          'User-Agent': 'generar-tablero'})
    if TOKEN:
        req.add_header('Authorization', 'Bearer ' + TOKEN)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def datos():
    repos = []
    pagina = 1
    while True:
        lote = api(f'/users/{USUARIO}/repos?per_page=100&page={pagina}')
        repos += lote
        if len(lote) < 100:
            break
        pagina += 1

    desde = min(r['created_at'] for r in repos)[:10]
    anos = (datetime.date.today() - datetime.date.fromisoformat(desde)).days / 365.25

    bytes_por_lang = {}
    for r in repos:
        if r['name'] in EXCLUIR:
            continue
        for lang, n in api(f"/repos/{USUARIO}/{r['name']}/languages").items():
            bytes_por_lang[lang] = bytes_por_lang.get(lang, 0) + n

    total = sum(bytes_por_lang.values()) or 1
    orden = sorted(bytes_por_lang.items(), key=lambda kv: -kv[1])
    langs = [(k, round(v / total * 100, 1)) for k, v in orden[:5]]
    resto = round(100 - sum(p for _, p in langs), 1)
    if resto > 0.05:
        langs.append(('Otros', resto))

    avatar = api(f'/users/{USUARIO}')['avatar_url']
    with urllib.request.urlopen(avatar + '&s=132', timeout=30) as r:
        foto = base64.b64encode(r.read()).decode()

    return anos, langs, foto


def donut(cx, cy, r, w, c, langs):
    out, ang = [], -90.0
    for nombre, pct in langs:
        barrido = pct / 100 * 360
        a0, a1 = math.radians(ang), math.radians(ang + barrido)
        x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
        x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        grande = 1 if barrido > 180 else 0
        col = COLOR_LANG.get(nombre, '#8b949e')
        out.append(f'<path d="M {x0:.2f} {y0:.2f} A {r} {r} 0 {grande} 1 {x1:.2f} {y1:.2f}" '
                   f'fill="none" stroke="{col}" stroke-width="{w}"/>')
        ang += barrido
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r - w / 2 - 1}" fill="{c["card"]}"/>')
    out.append(f'<text x="{cx}" y="{cy - 2}" text-anchor="middle" font-size="19" '
               f'font-weight="700" fill="{c["fg"]}">{langs[0][1]}%</text>')
    out.append(f'<text x="{cx}" y="{cy + 16}" text-anchor="middle" font-size="10.5" '
               f'fill="{c["mut"]}">{langs[0][0]}</text>')
    return '\n'.join(out)


def construir(c, anos, langs, foto):
    W, H = 860, 430
    F = 'font-family="ui-sans-serif,-apple-system,Segoe UI,Helvetica,Arial,sans-serif"'
    uri = 'data:image/jpeg;base64,' + foto
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
         f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" {F}>',
         f'<rect width="{W}" height="{H}" rx="14" fill="{c["bg"]}"/>']
    card = lambda x, y, w, h: (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" '
                               f'fill="{c["card"]}" stroke="{c["bd"]}"/>')
    s.append(card(20, 20, 820, 76))
    s.append('<defs><clipPath id="avatar"><circle cx="60" cy="58" r="22"/></clipPath></defs>')
    s.append(f'<image x="38" y="36" width="44" height="44" clip-path="url(#avatar)" '
             f'preserveAspectRatio="xMidYMid slice" href="{uri}" xlink:href="{uri}"/>')
    s.append(f'<circle cx="60" cy="58" r="22" fill="none" stroke="{c["bd"]}"/>')
    s.append(f'<text x="96" y="50" font-size="19" font-weight="700" fill="{c["fg"]}">Matías Olivieri</text>')
    s.append(f'<text x="96" y="72" font-size="12.5" fill="{c["mut"]}">@{USUARIO} · Web Developer · Uruguay</text>')
    s.append(f'<rect x="672" y="42" width="148" height="30" rx="8" fill="{c["pill"]}" stroke="{c["bd"]}"/>')
    s.append(f'<text x="746" y="62" text-anchor="middle" font-size="12" font-weight="600" fill="{c["fg"]}">MA Importaciones</text>')

    stats = [(str(len(EN_PRODUCCION)), 'SISTEMAS EN PRODUCCIÓN'), (f'{anos:.1f}', 'AÑOS CONSTRUYENDO'),
             (SIGLA.get(langs[0][0], langs[0][0][:3].upper()), 'STACK PRINCIPAL'), ('4', 'INTEGRACIONES')]
    for i, (v, lab) in enumerate(stats):
        x = 20 + i * 207.5
        s.append(card(x, 110, 187.5, 78))
        s.append(f'<text x="{x + 93.75}" y="146" text-anchor="middle" font-size="26" font-weight="700" fill="{c["fg"]}">{v}</text>')
        s.append(f'<text x="{x + 93.75}" y="168" text-anchor="middle" font-size="9" letter-spacing="0.9" fill="{c["mut"]}">{lab}</text>')

    s.append(card(20, 202, 530, 208))
    s.append(f'<text x="42" y="226" font-size="10" letter-spacing="1.1" fill="{c["mut"]}">STACK</text>')
    px, py = 42, 238
    for p in STACK:
        w = len(p) * 6.6 + 22
        if px + w > 530:
            px, py = 42, py + 32
        s.append(f'<rect x="{px}" y="{py}" width="{w:.0f}" height="24" rx="12" fill="{c["pill"]}" stroke="{c["bd"]}"/>')
        s.append(f'<text x="{px + w / 2:.0f}" y="{py + 16}" text-anchor="middle" font-size="11" fill="{c["fg"]}">{p}</text>')
        px += w + 8

    s.append(card(566, 202, 274, 208))
    s.append(donut(640, 290, 46, 15, c, langs))
    for i, (n, p) in enumerate(langs):
        y = 238 + i * 27
        s.append(f'<circle cx="716" cy="{y - 4}" r="4.5" fill="{COLOR_LANG.get(n, "#8b949e")}"/>')
        s.append(f'<text x="730" y="{y}" font-size="11.5" fill="{c["fg"]}">{n}</text>')
        s.append(f'<text x="822" y="{y}" text-anchor="end" font-size="11.5" fill="{c["mut"]}">{p}%</text>')
    s.append(f'<text x="640" y="392" text-anchor="middle" font-size="9" fill="{c["mut"]}">sin repos de game servers</text>')

    s.append(f'<line x1="42" y1="316" x2="528" y2="316" stroke="{c["bd"]}"/>')
    s.append(f'<text x="42" y="340" font-size="10" letter-spacing="1.1" fill="{c["mut"]}">QUE CONSTRUYO</text>')
    for i, t in enumerate(FOCO):
        s.append(f'<circle cx="46" cy="{357 + i * 21}" r="2.5" fill="{c["ac"]}"/>')
        s.append(f'<text x="58" y="{361 + i * 21}" font-size="11.5" fill="{c["fg"]}">{t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")}</text>')
    s.append('</svg>')
    return '\n'.join(s)


if __name__ == '__main__':
    anos, langs, foto = datos()
    print(f'anos: {anos:.1f} | lenguajes: {langs}')
    for nombre, tema in (('profile-dark.svg', OSCURO), ('profile-light.svg', CLARO)):
        open(nombre, 'w').write(construir(tema, anos, langs, foto))
        print('escrito', nombre)
