# Modelo de seguridad / Security model

Este sitio sirve a personas en riesgo real (periodistas, defensoras/es de derechos
humanos, activistas de vivienda en México). La premisa de seguridad es simple:

> **El sitio nunca debe convertirse en un instrumento de des-anonimización.**
> Una sola IP, un referer o una huella digital filtrada pueden traducirse en daño físico.

## Garantías del sitio / Guarantees

1. **Cero recursos de terceros.** No se carga ninguna fuente, hoja de estilo, script,
   imagen, iframe, widget ni analítica externa. El navegador de quien visita solo
   contacta a este origen. (Cargar Google Fonts o un CDN filtraría la IP del visitante
   a esos terceros; por eso todo es local.)
2. **Sin cookies y sin almacenamiento sensible.** La única preferencia persistente es
   el tema claro/oscuro (`localStorage`, no sensible). No hay sesiones ni identificadores.
3. **Sin código en línea.** Todo el CSS y JS están en archivos externos del mismo
   origen; no hay `onclick=`, `<style>` ni `<script>` en línea. Esto permite una CSP
   estricta sin `'unsafe-inline'`.
4. **Sin compilación ni dependencias.** HTML/CSS/JS puro: no hay cadena de suministro
   (`npm`) que comprometer.

## Encabezados de seguridad / Security headers

Definidos en [`_headers`](_headers) y [`netlify.toml`](netlify.toml):

```
Content-Security-Policy: default-src 'none'; script-src 'self'; style-src 'self';
  img-src 'self'; font-src 'self'; connect-src 'self'; manifest-src 'self';
  object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none';
  upgrade-insecure-requests
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
Referrer-Policy: no-referrer
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Permissions-Policy: camera=(), microphone=(), geolocation=(), ... (todo deshabilitado)
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
Cross-Origin-Resource-Policy: same-origin
X-XSS-Protection: 0
```

Cada página incluye además una CSP en `<meta>` como respaldo (útil en GitHub Pages, que
no admite encabezados personalizados). Nota: `frame-ancestors` solo opera como encabezado
HTTP, no en `<meta>`; por eso se recomienda un host que honre `_headers`.

## Recomendaciones de hospedaje / Hosting

Objetivo de despliegue: **Cloudflare Pages** (honra `_headers`).

- Usa un host donde **no se registren las IP** de visitantes (o puedas desactivar el
  registro de acceso) y donde controles la configuración de encabezados. Evita
  plataformas que inyecten su propia analítica o scripts.
- **⚠️ En Cloudflare, NO actives funciones que inyecten JavaScript**, porque romperían
  la CSP y la garantía de cero recursos de terceros: **Web Analytics / automatic beacon
  injection** (`static.cloudflareinsights.com`), **Rocket Loader**, **Email Obfuscation /
  Scrape Shield**, **Mirage**. La CSP estricta las bloquearía igualmente, pero no deben
  habilitarse. `Auto Minify` y `Brotli` son seguros.
- **Fuerza HTTPS** (Cloudflare: *Always Use HTTPS*) y considera enviar `Onion-Location`.
- **Servicio Tor (.onion) v3:** dado que el sitio no carga recursos externos, es seguro
  publicarlo también como servicio onion. El tráfico nunca sale de la red Tor y no se
  expone una IP pública. Suprime los banners de versión del servidor (`Server`).

## Para quien usa el sitio / For visitors at risk

Si tu seguridad depende de no ser identificada/o, accede con **Tor Browser**
(torproject.org) o desde **Tails** (tails.net). Lee la sección *Seguridad primero* del
sitio. Recuerda: ninguna medida de red protege un dispositivo ya comprometido.

## Reportar una vulnerabilidad / Reporting

Si encuentras una falla de seguridad o de privacidad en este sitio (una fuga de datos,
un recurso de terceros que se haya colado, un error en los encabezados), repórtala de
forma responsable mediante un *issue* (sin incluir datos sensibles) o por el canal de
contacto del proyecto. Agradecemos la divulgación coordinada.

## Verificación / Verification

Corre la suite de validación, que falla si se introduce cualquier recurso de terceros,
código en línea o CSP débil:

```bash
python3 scripts/validate.py
```
