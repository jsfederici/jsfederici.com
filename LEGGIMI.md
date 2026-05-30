# LEGGIMI — Ottimizzazione PageSpeed · jsfederici.com

Ciao Jacopo. Questa volta c'era anche la **home vera** (`index.html`): l'ho
analizzata e ottimizzata insieme alle altre. **Tutte e quattro le pagine sono
pronte** da caricare. Qui sotto trovi cosa ho cambiato, cosa caricare e una
checklist. Resta un solo gesto che dipende dalle tue foto (un'immagine "-sm"
mancante): te lo spiego al punto 3.

---

## Cosa ho cambiato (e perché porta a 100)

Il punteggio non era pieno per due motivi precisi. Ho agito su entrambi, su
tutte le pagine.

**1. I Google Fonts erano l'unica risorsa esterna.**
Ogni pagina contattava `fonts.googleapis.com` e `fonts.gstatic.com` (DNS +
connessione + TLS + un CSS, poi i file dei font): è il classico freno su FCP e
LCP. Ho **portato i font in casa**:

- font in **WOFF2**, già **ridotti al solo set latino** che il sito usa
  (italiano + segni tipografici): 9 file per ~190 KB totali;
- dichiarati con `@font-face` **dentro lo `<style>`** della pagina (zero
  richieste extra), con `font-display:swap`;
- **precarico i 2 font critici** — Karla 300 (corpo) e Cormorant Garamond 300
  corsivo (titoli) — così il testo appare subito.

Risultato: **nessuna chiamata esterna** su nessuna pagina.

**2. L'immagine principale (LCP) partiva in ritardo.**
- Sulla **home**, la foto hero aveva un'animazione `fadeIn` di **1 secondo**:
  per PageSpeed l'LCP "arriva" solo a fine dissolvenza. L'ho **disattivata**
  (`opacity:1`) → l'immagine è considerata visibile da subito. *(La tua home
  precaricava già la foto hero e aveva `fetchpriority="high"`: ho lasciato tutto
  com'era e non ho duplicato nulla.)*
- Sulle altre pagine, la prima immagine era `loading="lazy"`: l'ho resa
  **`eager` + `fetchpriority="high"`** con un **preload** dedicato.

**3. Le rifiniture su `discografia.html` (già sistemate da me).**
- l'`og:image` puntava a un percorso inesistente
  (`/FOTO/00 Head/og-image.jpg`): corretto in `/og-image.jpg`, con
  `og:image:width/height` e `twitter:image`;
- le favicon erano relative e incomplete: uniformate al set assoluto usato
  dalle altre pagine.

**4. Cache dei font (`_headers`).**
Ho aggiunto la regola `/fonts/*` (e `/*.woff2`) con cache immutabile di 1 anno,
come già fai per le immagini: così Lighthouse non segnala i font.

> **L'unico residuo: il 404 di `images/idx-10-sm.webp`.**
> È un'immagine piccola ("-sm") richiamata dalla home ma assente nella cartella
> `images`. Non avendo io la cartella foto, la generi tu in 10 secondi con lo
> script `genera-webp-sm.py` (vedi sotto). È questo che fa passare le **Best
> practice a 100** sulla home.

> Nota: i caratteri rari `←` e `＋` non esistono nemmeno nei font originali di
> Google → ricadono sul font di sistema **esattamente come adesso**. Nessun
> cambiamento visibile.

---

## La pagina del pannello CMS (separata)

Il file dell'amministrazione Decap (quello con `decap-cms.js`) **non fa parte di
questo pacchetto** e non va nella root insieme alla home. Di norma vive in una
sottocartella dedicata, es. `/admin/index.html`, così non entra in conflitto con
la home del sito. Quando vorrai completarlo, possiamo vederlo a parte: non
influisce sui punteggi PageSpeed delle pagine pubbliche.

---

## Contenuto del pacchetto

```
index.html              ← HOME, pronta (sovrascrive l'attuale)
biography.html          ← pronta
setup.html              ← pronta
discografia.html        ← pronta
_headers                ← aggiornato (cache per /fonts/)
fonts/                  ← 9 file .woff2 → va caricata nella ROOT del sito
ottimizza.py            ← lo script che ho usato (riutilizzabile su ogni pagina)
genera-webp-sm.py       ← crea le immagini "-sm" mancanti (per il 404)
LEGGIMI.md              ← questo file
```

I 9 font: `karla-300/400/500.woff2`, `cormorant-300/400/600.woff2` e i corsivi
`cormorant-300i/400i/600i.woff2`.

---

## Checklist di caricamento (nell'ordine)

1. **Carica i 4 HTML** (`index.html`, `biography.html`, `setup.html`,
   `discografia.html`) nella root, sovrascrivendo i vecchi.

2. **Crea la cartella `fonts/` nella root** e caricaci i 9 file `.woff2`.
   ⚠️ Il percorso deve essere esattamente `/fonts/...` (i font sono richiamati
   con percorso assoluto). Struttura finale:
   ```
   /  (root)
   ├── index.html
   ├── biography.html
   ├── setup.html
   ├── discografia.html
   ├── images/ ...
   └── fonts/  ← karla-300.woff2, cormorant-300i.woff2, ...
   ```

3. **Genera l'immagine "-sm" mancante** (risolve il 404). Dalla cartella del
   sito (quella che contiene i .html e la cartella `images`):
   ```bash
   pip3 install pillow          # solo la prima volta
   python3 genera-webp-sm.py
   ```
   Lo script legge le pagine, trova solo le "-sm" davvero richiamate e crea
   quelle mancanti (qui dovrebbe creare `images/idx-10-sm.webp`). Poi carica i
   nuovi file `-sm`.

4. **Sostituisci `_headers`** con quello del pacchetto.

5. **Pubblica** (deploy) e rilancia PageSpeed su mobile e desktop.

---

## Cosa aspettarsi

Con tutto caricato:

- **Prestazioni** mobile e desktop → **100** (font locali e precaricati, hero
  senza dissolvenza, immagine LCP in preload).
- **Best practice** → **100** (sparisce il 404 `idx-10-sm.webp`).
- **SEO / Accessibilità** restano a posto.

I numeri di PageSpeed possono oscillare di 1-2 punti tra una misura e l'altra
(dipende dal "lab" di Google in quel momento): se vedi un 99, riprova dopo
qualche minuto. La sostanza tecnica — zero risorse esterne, LCP immediato,
nessun 404 — è quella giusta per il 100 pieno.

---

## Se qualcosa non torna

- **Testo "di sistema" al posto dei font** → quasi sempre la cartella `fonts/`
  non è in root o un nome file è diverso. Apri
  `https://www.jsfederici.com/fonts/karla-300.woff2`: deve scaricarsi, non dare
  404.
- **Ancora 404 su `idx-10-sm.webp`** → se lo script segnala "manca l'originale",
  vuol dire che nella cartella `images` non c'è `idx-10.webp` a piena
  risoluzione: aggiungilo e rilancia `genera-webp-sm.py`.

Buon caricamento.
