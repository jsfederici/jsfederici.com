#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ottimizza.py — Ottimizzazione prestazioni per il sito jsfederici.com
Applica, a QUALSIASI pagina HTML del sito, le stesse modifiche usate per
portare PageSpeed al 100%:

  1. Rimuove Google Fonts (2 preconnect + CSS esterno + noscript) e li
     sostituisce con font self-hosted in /fonts (woff2 sottoinsieme Latino).
  2. Inietta le @font-face nello <style> inline (nessuna richiesta extra).
  3. Precarica i 2 font critici (corpo + titoli) e la prima immagine (LCP).
  4. Toglie il fade-in di 1s dall'immagine hero (sblocca l'LCP).
  5. Marca la prima immagine come eager + fetchpriority=high + decoding=async.

È IDEMPOTENTE: se la pagina è già ottimizzata, non fa nulla.

Uso:
    python3 ottimizza.py index.html              # sovrascrive (fa un .bak)
    python3 ottimizza.py index.html out.html      # scrive su un nuovo file
"""
import re, sys, os, shutil

FONTFACE = (
"@font-face{font-family:'Karla';font-style:normal;font-weight:300;font-display:swap;src:url('/fonts/karla-300.woff2') format('woff2')}"
"@font-face{font-family:'Karla';font-style:normal;font-weight:400;font-display:swap;src:url('/fonts/karla-400.woff2') format('woff2')}"
"@font-face{font-family:'Karla';font-style:normal;font-weight:500;font-display:swap;src:url('/fonts/karla-500.woff2') format('woff2')}"
"@font-face{font-family:'Cormorant Garamond';font-style:normal;font-weight:300;font-display:swap;src:url('/fonts/cormorant-300.woff2') format('woff2')}"
"@font-face{font-family:'Cormorant Garamond';font-style:normal;font-weight:400;font-display:swap;src:url('/fonts/cormorant-400.woff2') format('woff2')}"
"@font-face{font-family:'Cormorant Garamond';font-style:normal;font-weight:600;font-display:swap;src:url('/fonts/cormorant-600.woff2') format('woff2')}"
"@font-face{font-family:'Cormorant Garamond';font-style:italic;font-weight:300;font-display:swap;src:url('/fonts/cormorant-300i.woff2') format('woff2')}"
"@font-face{font-family:'Cormorant Garamond';font-style:italic;font-weight:400;font-display:swap;src:url('/fonts/cormorant-400i.woff2') format('woff2')}"
"@font-face{font-family:'Cormorant Garamond';font-style:italic;font-weight:600;font-display:swap;src:url('/fonts/cormorant-600i.woff2') format('woff2')}"
)

FONT_PRELOADS = (
'  <link rel="preload" href="/fonts/karla-300.woff2" as="font" type="font/woff2" crossorigin>\n'
'  <link rel="preload" href="/fonts/cormorant-300i.woff2" as="font" type="font/woff2" crossorigin>\n'
)

def attr(tag, name):
    m = re.search(r'\b' + name + r'\s*=\s*"([^"]*)"', tag, re.I)
    return m.group(1) if m else None

def optimize(html):
    notes = []
    if '/fonts/karla-300.woff2' in html:
        return html, ['già ottimizzato — nessuna modifica']

    # 1) Rimuovi tutte le righe che puntano a Google Fonts (preconnect, css, noscript)
    lines = html.split('\n')
    kept, removed = [], 0
    for ln in lines:
        if ('fonts.googleapis.com' in ln) or ('fonts.gstatic.com' in ln):
            removed += 1
            continue
        kept.append(ln)
    html = '\n'.join(kept)
    if removed:
        notes.append(f'rimosse {removed} righe Google Fonts')

    # 1b) Inserisci i preload dei font self-hosted subito prima di <style>
    if removed:
        html = re.sub(r'([ \t]*)<style', FONT_PRELOADS + r'\1<style', html, count=1, flags=re.I)
        notes.append('aggiunti preload font self-hosted')

    # 2) Inietta le @font-face all'inizio dello <style> inline
    html = re.sub(r'<style>', '<style>\n' + FONTFACE + '\n', html, count=1)
    notes.append('iniettate @font-face')

    # 3) Togli il fade-in dall'immagine hero (sblocca LCP). No-op se assente.
    new = html.replace('.hero-photo-wrap{animation:fadeIn 1s ease forwards}',
                       '.hero-photo-wrap{opacity:1}')
    if new != html:
        notes.append('rimosso fade-in hero (LCP istantaneo)')
        html = new

    # 4) Prima immagine del body -> eager + fetchpriority + decoding + preload
    bi = html.lower().find('<body')
    m = re.search(r'<img\b[^>]*>', html[bi:], re.I) if bi != -1 else None
    if m:
        start, end = bi + m.start(), bi + m.end()
        tag = m.group(0)
        new_tag = re.sub(r'\s+loading\s*=\s*"lazy"', '', tag, flags=re.I)
        add = ''
        if not re.search(r'\bloading\s*=', new_tag, re.I):       add += ' loading="eager"'
        if not re.search(r'\bfetchpriority\s*=', new_tag, re.I): add += ' fetchpriority="high"'
        if not re.search(r'\bdecoding\s*=', new_tag, re.I):      add += ' decoding="async"'
        if add:
            new_tag = re.sub(r'<img\b', '<img' + add, new_tag, count=1, flags=re.I)
        html = html[:start] + new_tag + html[end:]
        notes.append('prima immagine: eager + fetchpriority=high')

        # preload dell'immagine LCP (responsive se ha srcset) — SOLO se non già presente
        srcset = attr(new_tag, 'srcset'); sizes = attr(new_tag, 'sizes'); src = attr(new_tag, 'src')
        # Cerca preload immagine già esistenti (rel=preload + as=image, in qualsiasi ordine)
        existing = [m.group(0) for m in re.finditer(r'<link\b[^>]*>', html, re.I)
                    if re.search(r'rel\s*=\s*["\']preload["\']', m.group(0), re.I)
                    and re.search(r'as\s*=\s*["\']image["\']', m.group(0), re.I)]
        already = any(src and src in p for p in existing)
        if already:
            notes.append('preload immagine LCP già presente — non duplicato')
        else:
            if srcset:
                pl = ('  <link rel="preload" as="image" imagesrcset="' + srcset + '"' +
                      ((' imagesizes="' + sizes + '"') if sizes else '') + ' fetchpriority="high">\n')
            elif src:
                pl = '  <link rel="preload" as="image" href="' + src + '" fetchpriority="high">\n'
            else:
                pl = ''
            if pl:
                html = re.sub(r'([ \t]*)<style', pl + r'\1<style', html, count=1, flags=re.I)
                notes.append('aggiunto preload immagine LCP')

    return html, notes

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else src
    with open(src, encoding='utf-8') as f:
        html = f.read()
    out, notes = optimize(html)
    if dst == src and out != html:
        shutil.copy(src, src + '.bak')
    with open(dst, 'w', encoding='utf-8') as f:
        f.write(out)
    print(f'{src}: ' + '; '.join(notes))

if __name__ == '__main__':
    main()
