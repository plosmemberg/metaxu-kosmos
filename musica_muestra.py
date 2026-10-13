"""Graba una muestra de la música de la app en salida/.
El motor vive en metaxu_beta.html, entre las marcas MUSICA; esta herramienta lo toma de ahí.
Uso: python3 musica_muestra.py [segundos] [semilla]      (por omisión: 180 7, la muestra aprobada)
Requiere Playwright con Chromium y ffmpeg."""
import sys, base64, wave, re, subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parent.parent
seg = float(sys.argv[1]) if len(sys.argv) > 1 else 180
sem = int(sys.argv[2]) if len(sys.argv) > 2 else 7
html = (RAIZ / 'metaxu_beta.html').read_text(encoding='utf-8')
motor = re.search(r'/\* MUSICA: inicio \*/(.*?)/\* MUSICA: fin \*/', html, re.S).group(1)
salida = RAIZ / 'salida'; salida.mkdir(exist_ok=True)
wav, mp3 = salida / 'metaxu_musica_muestra.wav', salida / 'metaxu_musica_muestra.mp3'

with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    pg.set_content('<html><body><script>' + motor + '</script></body></html>')
    d = pg.evaluate("""async ([seg, sem]) => {
      const sr = 44100, ctx = new OfflineAudioContext(2, Math.floor(sr*seg), sr);
      MetaxuMusica.crear(ctx, ctx.destination, {semilla: sem, volumen: 0.85, reloj: false}).programarHasta(seg);
      const buf = await ctx.startRendering(), L = buf.getChannelData(0), R = buf.getChannelData(1), n = L.length;
      const pcm = new Int16Array(n*2);
      for (let i=0;i<n;i++){pcm[2*i]=Math.max(-1,Math.min(1,L[i]))*32767;pcm[2*i+1]=Math.max(-1,Math.min(1,R[i]))*32767;}
      const by = new Uint8Array(pcm.buffer); let s=''; for (let i=0;i<by.length;i+=0x8000) s+=String.fromCharCode.apply(null, by.subarray(i,i+0x8000));
      return btoa(s);
    }""", [seg, sem])
    b.close()
w = wave.open(str(wav), 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(44100); w.writeframes(base64.b64decode(d)); w.close()
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(wav), '-af',
                f'afade=t=out:st={max(0, seg-8)}:d=8,loudnorm=I=-16:TP=-1.5:LRA=11',
                '-c:a', 'libmp3lame', '-b:a', '192k', str(mp3)], check=True)
wav.unlink()
print('listo:', mp3)
