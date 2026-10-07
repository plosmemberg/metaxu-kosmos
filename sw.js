/* Service worker de Metaxu: guarda la app para abrirla sin conexión. */
const VERSION="metaxu-v1";
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
