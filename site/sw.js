// Astrid 盘前简报 · Service Worker
// 策略：网络优先（行情实时），失败时回退缓存（离线可打开）
const CACHE = "astrid-v1";
const CORE = ["./", "./index.html", "./manifest.json", "./events.json",
             "./icon-192.png", "./icon-512.png", "./apple-touch-icon.png", "./favicon.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)).catch(()=>{}).then(()=>self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  // 同源静态资源：网络优先，失败回缓存
  if (url.origin === location.origin) {
    e.respondWith(
      fetch(req).then(r => {
        const cp = r.clone();
        caches.open(CACHE).then(c => c.put(req, cp)).catch(()=>{});
        return r;
      }).catch(() => caches.match(req).then(r => r || caches.match("./index.html")))
    );
  }
  // 跨域行情/资讯请求（东财/新浪/华尔街见闻等）：不缓存，直通
});
