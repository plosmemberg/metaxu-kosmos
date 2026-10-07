"""Arma la carpeta instalable de la app (PWA) en ../app/, lista para Netlify.

Toma metaxu_beta.html como fuente, genera los íconos (negro con el símbolo
del dorso en blanco), el manifest y el service worker, e inyecta en una
copia (index.html) lo que la instalación necesita."""
import json, re
from pathlib import Path
import subprocess
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
BETA = RAIZ / 'metaxu_beta.html'
APP = RAIZ / 'app'
NEGRO = '#000000'

def simbolo():
    s = BETA.read_text(encoding='utf-8')
    m = re.search(r'const SIMB=(\{.*?\});\n', s, re.S)
    o = json.loads(m.group(1))['metaxu']
    x, y, w, h = (float(v) for v in o['vb'].split())
    return o['inner'].replace('currentColor', '#ffffff'), (x + w / 2, y + h / 2, max(w, h))

def icono(nombre, lado, parte):
    inner, (cx, cy, dim) = simbolo()
    k = lado * parte / dim
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {lado} {lado}">'
           f'<rect width="{lado}" height="{lado}" fill="{NEGRO}"/>'
           f'<g transform="translate({lado/2} {lado/2}) scale({k:.5f}) translate({-cx} {-cy})">{inner}</g></svg>')
    tmp = APP / (nombre + '.svg')
    tmp.write_text(svg, encoding='utf-8')
    pdf = APP / (nombre + '.pdf')
    renderPDF.drawToFile(svg2rlg(str(tmp)), str(pdf))
    subprocess.run(['pdftoppm', '-png', '-r', '96', '-f', '1', '-l', '1',
                    str(pdf), str(APP / nombre)], check=True)
    (APP / (nombre + '-1.png')).replace(APP / (nombre + '.png'))
    tmp.unlink(); pdf.unlink()

def achicar(desde, hacia, lado):
    Image.open(APP / desde).resize((lado, lado), Image.LANCZOS).save(APP / hacia)

MANIFEST = {
    "name": "Metaxu: kósmos", "short_name": "Metaxu",
    "description": "Un sistema para imaginar y describir un mundo, por retazos.",
    "lang": "es", "start_url": "./", "scope": "./", "display": "standalone",
    "background_color": "#ffffff", "theme_color": NEGRO,
    "icons": [
        {"src": "icono-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "icono-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "icono-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ],
}

SW = '''/* Service worker de Metaxu: guarda la app para abrirla sin conexión. */
const VERSION="metaxu-v2";
const ARCHIVOS=["./","./index.html","./manifest.webmanifest","./icono-192.png","./icono-512.png"];
self.addEventListener("install",e=>{
  e.waitUntil(caches.open(VERSION).then(c=>c.addAll(ARCHIVOS)).then(()=>self.skipWaiting()));
});
self.addEventListener("activate",e=>{
  e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==VERSION).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));
});
self.addEventListener("fetch",e=>{
  if(e.request.method!=="GET")return;
  e.respondWith(
    caches.match(e.request,{ignoreSearch:true}).then(guardado=>{
      const red=fetch(e.request).then(r=>{
        if(r&&r.ok&&new URL(e.request.url).origin===location.origin){
          const copia=r.clone();caches.open(VERSION).then(c=>c.put(e.request,copia));
        }
        return r;
      }).catch(()=>guardado);
      return guardado||red;
    })
  );
});
'''

REGISTRO = '''<script>
/* La instalación solo corre cuando la app se sirve por la web. */
if("serviceWorker" in navigator&&location.protocol.startsWith("http")){
  addEventListener("load",()=>{navigator.serviceWorker.register("./sw.js")});
}
</script>
'''

CABEZA = ('<link rel="manifest" href="manifest.webmanifest">'
          f'<meta name="theme-color" content="{NEGRO}">'
          '<link rel="icon" type="image/png" href="icono-192.png">'
          '<link rel="apple-touch-icon" href="icono-180.png">')

def correr():
    APP.mkdir(exist_ok=True)
    icono('icono-512', 512, 0.62)
    icono('icono-maskable-512', 512, 0.46)
    achicar('icono-512.png', 'icono-192.png', 192)
    achicar('icono-512.png', 'icono-180.png', 180)
    (APP / 'manifest.webmanifest').write_text(json.dumps(MANIFEST, ensure_ascii=False, indent=1), encoding='utf-8')
    (APP / 'sw.js').write_text(SW, encoding='utf-8')
    s = BETA.read_text(encoding='utf-8')
    assert s.count('</title>') == 1 and s.count('</body>') == 1
    s = s.replace('</title>', '</title>\n' + CABEZA)
    s = s.replace('</body>', REGISTRO + '</body>')
    (APP / 'index.html').write_text(s, encoding='utf-8')
    print('carpeta app/ lista:', ', '.join(sorted(p.name for p in APP.iterdir())))

if __name__ == '__main__':
    correr()
