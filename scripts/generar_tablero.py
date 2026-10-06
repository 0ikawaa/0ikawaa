#!/usr/bin/env python3
"""Regenera profile-dark.svg y profile-light.svg con datos vivos de la API de GitHub.

Lo que se recalcula solo: los anos construyendo y el reparto de lenguajes. El resto
(stack, que construyo) es texto fijo de mas abajo, porque no hay API que lo sepa.

Los repos de servidores de juego se excluyen a proposito: son cientos de MB de assets
en Lua y C# que tapaban el TypeScript, que es lo que de verdad escribo.

El acento es el teal de MA Importaciones (#0FB09E), muestreado del panel.
"""
import base64, datetime, json, math, os, urllib.request

USUARIO = '0ikawaa'
EXCLUIR = {'Unity', 'UnityNetwork', 'Server-FiveM', 'vyper-rp', 'vyper-mu', 'Server', USUARIO}
TOKEN = os.environ.get('GITHUB_TOKEN', '')

STACK = ['TypeScript', 'React', 'Next.js', 'Tailwind', 'Prisma', 'PostgreSQL',
         'three.js', 'Vercel', 'Mercado Libre API', 'Odoo', 'Shopify']
FOCO = ['Fichas de producto con visor 3D y realidad aumentada',
        'Paneles internos: importaciones, stock, precios y rentabilidad',
        'Integraciones Mercado Libre, Odoo y Shopify']
EN_PRODUCCION = ['panel-ma', 'mundoshop', 'telas-harturo', 'web-maimpo']
INTEGRACIONES = ['Mercado Libre', 'Odoo', 'Shopify']
COLOR_LANG = {'TypeScript': '#3178c6', 'JavaScript': '#f1e05a', 'CSS': '#663399',
              'HTML': '#e34c26', 'PHP': '#4F5D95', 'Otros': '#8b949e'}

OSCURO = {'bg': '#0d1117', 'card': '#161b22', 'bd': '#272e36', 'fg': '#e6edf3',
          'mut': '#8b949e', 'ten': '#6e7681', 'ac': '#0FB09E', 'acsuave': '#0c2b2a',
          'pill': '#1c232b'}
CLARO  = {'bg': '#ffffff', 'card': '#f6f8fa', 'bd': '#d8dee4', 'fg': '#1f2328',
          'mut': '#636c76', 'ten': '#8c959f', 'ac': '#0B8577', 'acsuave': '#e2f5f2',
          'pill': '#eef1f4'}

W, H = 880, 470
FUENTE = ('font-family="ui-sans-serif,-apple-system,BlinkMacSystemFont,'
          'Segoe UI,Helvetica,Arial,sans-serif"')


def api(ruta):
    req = urllib.request.Request('https://api.github.com' + ruta,
                                 headers={'Accept': 'application/vnd.github+json',
                                          'User-Agent': 'generar-tablero'})
    if TOKEN:
        req.add_header('Authorization', 'Bearer ' + TOKEN)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def datos():
    repos, pagina = [], 1
    while True:
        lote = api(f'/users/{USUARIO}/repos?per_page=100&page={pagina}')
        repos += lote
        if len(lote) < 100:
            break
        pagina += 1

    desde = min(r['created_at'] for r in repos)[:10]
    anos = (datetime.date.today() - datetime.date.fromisoformat(desde)).days / 365.25

    porlang = {}
    for r in repos:
        if r['name'] in EXCLUIR:
            continue
        for lang, n in api(f"/repos/{USUARIO}/{r['name']}/languages").items():
            porlang[lang] = porlang.get(lang, 0) + n

    total = sum(porlang.values()) or 1
    orden = sorted(porlang.items(), key=lambda kv: -kv[1])
    langs = [(k, round(v / total * 100, 1)) for k, v in orden[:5]]
    resto = round(100 - sum(p for _, p in langs), 1)
    if resto > 0.05:
        langs.append(('Otros', resto))

    avatar = api(f'/users/{USUARIO}')['avatar_url']
    with urllib.request.urlopen(avatar + '&s=192', timeout=30) as r:
        foto = base64.b64encode(r.read()).decode()
    return anos, langs, foto


def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def donut(cx, cy, r, w, c, langs):
    out, ang = [], -90.0
    for nombre, pct in langs:
        barrido = pct / 100 * 360
        a0, a1 = math.radians(ang), math.radians(ang + barrido - 1.4)
        x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
        x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        grande = 1 if barrido > 180 else 0
        col = COLOR_LANG.get(nombre, '#8b949e')
        out.append(f'<path d="M {x0:.2f} {y0:.2f} A {r} {r} 0 {grande} 1 {x1:.2f} {y1:.2f}" '
                   f'fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/>')
        ang += barrido
    # Solo el porcentaje: el nombre del lenguaje ya esta en la leyenda y a este
    # tamano no entra en el agujero del donut.
    out.append(f'<text x="{cx}" y="{cy + 6}" text-anchor="middle" font-size="17" '
               f'font-weight="700" fill="{c["fg"]}">{langs[0][1]}%</text>')
    return '\n'.join(out)


def construir(c, anos, langs, foto):
    uri = 'data:image/jpeg;base64,' + foto
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
         f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" {FUENTE}>',
         f'<rect width="{W}" height="{H}" rx="16" fill="{c["bg"]}"/>']

    def card(x, y, w, h, r=12):
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" '
                f'fill="{c["card"]}" stroke="{c["bd"]}"/>')

    # ── hero: jerarquia alta, avatar grande, franja de acento ───────────
    s.append(card(22, 22, 836, 104, 14))
    s.append(f'<rect x="22" y="22" width="4" height="104" fill="{c["ac"]}"/>')
    s.append(f'<rect x="22" y="22" width="14" height="104" fill="{c["ac"]}" opacity="0.07"/>')
    s.append('<defs><clipPath id="avatar"><circle cx="84" cy="74" r="32"/></clipPath></defs>')
    s.append(f'<circle cx="84" cy="74" r="35" fill="none" stroke="{c["ac"]}" stroke-width="1.5" opacity="0.5"/>')
    s.append(f'<image x="52" y="42" width="64" height="64" clip-path="url(#avatar)" '
             f'preserveAspectRatio="xMidYMid slice" href="{uri}" xlink:href="{uri}"/>')
    s.append(f'<text x="136" y="68" font-size="25" font-weight="700" letter-spacing="-0.3" '
             f'fill="{c["fg"]}">Matías Olivieri</text>')
    s.append(f'<text x="136" y="92" font-size="13" fill="{c["mut"]}">Web Developer · Uruguay</text>')
    s.append(f'<text x="136" y="110" font-size="11.5" fill="{c["ten"]}">@{USUARIO}</text>')
    s.append(f'<rect x="676" y="58" width="158" height="32" rx="16" fill="{c["acsuave"]}" stroke="{c["ac"]}" stroke-opacity="0.35"/>')
    s.append(f'<circle cx="697" cy="74" r="3.5" fill="{c["ac"]}"/>')
    s.append(f'<text x="710" y="78" font-size="12" font-weight="600" fill="{c["ac"]}">MA Importaciones</text>')

    # ── 3 metricas, no 4: las dos flojas se fusionan en una que si dice algo ──
    stats = [('4', 'SISTEMAS EN PRODUCCIÓN', ' · '.join(EN_PRODUCCION[:2]) + ' +2'),
             (f'{anos:.1f}', 'AÑOS CONSTRUYENDO', f'desde {datetime.date.today().year - int(anos)}'),
             ('3', 'INTEGRACIONES', ' · '.join(INTEGRACIONES))]
    aw = (836 - 2 * 14) / 3
    for i, (v, lab, sub) in enumerate(stats):
        x = 22 + i * (aw + 14)
        s.append(card(x, 140, aw, 88))
        s.append(f'<text x="{x + 20}" y="180" font-size="32" font-weight="700" fill="{c["fg"]}">{v}</text>')
        s.append(f'<text x="{x + 20}" y="199" font-size="9.5" letter-spacing="1.2" fill="{c["mut"]}">{lab}</text>')
        s.append(f'<text x="{x + 20}" y="215" font-size="10" fill="{c["ten"]}">{esc(sub)}</text>')

    # ── stack ───────────────────────────────────────────────────────────
    s.append(card(22, 242, 540, 206))
    s.append(f'<rect x="22" y="242" width="3" height="206" rx="1.5" fill="{c["ac"]}" opacity="0.45"/>')
    s.append(f'<text x="44" y="268" font-size="9.5" letter-spacing="1.4" fill="{c["mut"]}">STACK</text>')
    px, py = 44, 280
    for p in STACK:
        w = len(p) * 6.5 + 24
        if px + w > 548:
            px, py = 44, py + 31
        s.append(f'<rect x="{px}" y="{py}" width="{w:.0f}" height="25" rx="12.5" fill="{c["pill"]}" stroke="{c["bd"]}"/>')
        s.append(f'<text x="{px + w / 2:.0f}" y="{py + 17}" text-anchor="middle" font-size="11" fill="{c["fg"]}">{p}</text>')
        px += w + 8

    s.append(f'<line x1="44" y1="350" x2="540" y2="350" stroke="{c["bd"]}"/>')
    s.append(f'<text x="44" y="372" font-size="9.5" letter-spacing="1.4" fill="{c["mut"]}">QUÉ CONSTRUYO</text>')
    for i, t in enumerate(FOCO):
        y = 392 + i * 19
        s.append(f'<path d="M 45 {y - 4} l 4 4 l -4 4" fill="none" stroke="{c["ac"]}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>')
        s.append(f'<text x="58" y="{y + 4}" font-size="11.5" fill="{c["fg"]}">{esc(t)}</text>')

    # ── lenguajes ───────────────────────────────────────────────────────
    s.append(card(576, 242, 282, 206))
    s.append(f'<text x="598" y="268" font-size="9.5" letter-spacing="1.4" fill="{c["mut"]}">LENGUAJES</text>')
    s.append(donut(640, 352, 38, 13, c, langs))
    for i, (n, p) in enumerate(langs):
        y = 292 + i * 24
        s.append(f'<rect x="716" y="{y - 8}" width="9" height="9" rx="2.5" fill="{COLOR_LANG.get(n, "#8b949e")}"/>')
        s.append(f'<text x="732" y="{y}" font-size="11" fill="{c["fg"]}">{n}</text>')
        s.append(f'<text x="840" y="{y}" text-anchor="end" font-size="11" font-weight="600" fill="{c["mut"]}">{p}%</text>')
    s.append(f'<text x="598" y="438" font-size="9" fill="{c["ten"]}">sin los repos de game servers</text>')

    s.append('</svg>')
    return '\n'.join(s)


if __name__ == '__main__':
    anos, langs, foto = datos()
    print(f'anos: {anos:.1f} | lenguajes: {langs}')
    for nombre, tema in (('profile-dark.svg', OSCURO), ('profile-light.svg', CLARO)):
        open(nombre, 'w').write(construir(tema, anos, langs, foto))
        print('escrito', nombre)
