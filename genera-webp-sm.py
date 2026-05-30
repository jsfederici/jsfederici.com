#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
genera-webp-sm.py — Genera SOLO le varianti "-sm" che il sito usa e che mancano
===============================================================================

A cosa serve
------------
Le pagine usano immagini responsive, es:

    srcset="images/idx-10-sm.webp 450w, images/idx-10.webp 900w"

Su PageSpeed risultava un 404 perché mancava `images/idx-10-sm.webp`.
Questo script:
  1. legge i file .html del sito,
  2. trova TUTTE le immagini "-sm" realmente richiamate (e la loro larghezza
     dichiarata nel srcset, es. 450w),
  3. crea SOLO quelle che mancano davvero, ridimensionando l'immagine a piena
     risoluzione che hai già nella cartella `images`.

Vantaggi rispetto a generare tutto a tappeto:
  • non crea file inutili (hero, icone, copertine senza "-sm" restano intatte);
  • ogni "-sm" viene creata esattamente alla larghezza che il sito si aspetta.

Cosa NON fa
-----------
  • non tocca le "-sm" già presenti (idempotente);
  • non ingrandisce mai un'immagine (al massimo la riduce).

Requisiti
---------
Python 3 + Pillow con supporto WebP:

    pip3 install pillow

(su macOS `sips` non esporta in WebP, per questo si usa Pillow.)

Uso
---
Lancialo dalla cartella del sito (quella che contiene i .html e la cartella
`images`):

    python3 genera-webp-sm.py
    python3 genera-webp-sm.py /percorso/della/cartella/sito
    python3 genera-webp-sm.py . --force      # rigenera anche le -sm esistenti
"""

import sys
import os
import re
import glob

DEFAULT_W = 640    # larghezza usata solo se il srcset non dichiara un valore "Nw"
QUALITY   = 82
METHOD    = 6


def main():
    args = [a for a in sys.argv[1:] if a != "--force"]
    force = "--force" in sys.argv[1:]
    root = args[0] if args else "."

    if not os.path.isdir(root):
        print(f'ERRORE: la cartella "{root}" non esiste.')
        sys.exit(1)

    images_dir = os.path.join(root, "images")
    if not os.path.isdir(images_dir):
        print(f'ERRORE: non trovo la cartella "images" dentro "{os.path.abspath(root)}".')
        print('Lancia lo script dalla cartella del sito (quella con i .html e /images).')
        sys.exit(1)

    html_files = glob.glob(os.path.join(root, "*.html"))
    if not html_files:
        print(f'ERRORE: nessun file .html in "{os.path.abspath(root)}".')
        sys.exit(1)

    # --- Pillow + WebP ---
    try:
        from PIL import Image, features
    except ImportError:
        print('ERRORE: manca Pillow.  Installalo con:  pip3 install pillow')
        sys.exit(1)
    if not features.check("webp"):
        print('ERRORE: questa installazione di Pillow non supporta il WebP.')
        print('Prova:  pip3 install --upgrade --force-reinstall pillow')
        sys.exit(1)

    # --- 1) raccogli i riferimenti "-sm" e la larghezza dichiarata ---
    # mappa:  "idx-10-sm.webp" -> larghezza massima dichiarata (int) o None
    wanted = {}
    ref_re   = re.compile(r'images/([A-Za-z0-9._-]+-sm\.webp)')
    width_re = lambda name: re.compile(
        r'images/' + re.escape(name) + r'\s+(\d+)w')

    for hf in html_files:
        try:
            txt = open(hf, encoding="utf-8").read()
        except Exception:
            continue
        for name in ref_re.findall(txt):
            wanted.setdefault(name, None)
            m = width_re(name).search(txt)
            if m:
                w = int(m.group(1))
                if wanted[name] is None or w > wanted[name]:
                    wanted[name] = w

    if not wanted:
        print('Nessun riferimento "-sm" trovato nei file .html. Niente da fare.')
        return

    # --- 2) genera quelle mancanti ---
    created, present, base_missing, errors = [], [], [], []

    for name in sorted(wanted):
        dst = os.path.join(images_dir, name)
        if os.path.exists(dst) and not force:
            present.append(name)
            continue

        base_name = name[:-len("-sm.webp")] + ".webp"   # idx-10-sm.webp -> idx-10.webp
        base = os.path.join(images_dir, base_name)
        if not os.path.exists(base):
            base_missing.append((name, base_name))
            continue

        target_w = wanted[name] or DEFAULT_W
        try:
            im = Image.open(base)
            im.load()
            w, h = im.size
            if im.mode in ("P", "CMYK"):
                im = im.convert("RGB")
            final_w = min(target_w, w)        # mai ingrandire
            final_h = round(h * final_w / w)
            out = im.resize((final_w, final_h), Image.LANCZOS)
            out.save(dst, "WEBP", quality=QUALITY, method=METHOD)
            created.append(f"{name}  ({final_w}x{final_h}, da {base_name})")
        except Exception as e:
            errors.append(f"{name}: {e}")

    # --- 3) report ---
    print(f'\nSito:   {os.path.abspath(root)}')
    print(f'Pagine: {", ".join(os.path.basename(h) for h in sorted(html_files))}')
    print(f'Trovate {len(wanted)} immagini "-sm" richiamate dal sito.')
    print("=" * 60)
    if created:
        print(f'\n✓ Create {len(created)} (mancavano):')
        for c in created:
            print(f"    + {c}")
    if present:
        print(f'\n• Già presenti, saltate: {len(present)}'
              + ('  (usa --force per rigenerarle)' if not force else ''))
    if base_missing:
        print(f'\n⚠ Impossibile creare {len(base_missing)}: manca l\'originale a '
              f'piena risoluzione nella cartella images:')
        for sm, base in base_missing:
            print(f"    ! {sm}  ->  serve  images/{base}")
    if errors:
        print(f'\n⚠ Errori ({len(errors)}):')
        for e in errors:
            print(f"    ! {e}")
    if not created and not base_missing and not errors:
        print('\nTutte le varianti "-sm" richiamate dal sito sono già presenti. ✓')
    print()


if __name__ == "__main__":
    main()
