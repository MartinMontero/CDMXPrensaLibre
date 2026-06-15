# CDMX Prensa Libre — Guía de Investigación de Corrupción y Vivienda

> Una herramienta práctica y segura para **documentar corrupción y violaciones al
> derecho a la vivienda en la Ciudad de México**, dirigida a abogadas/os, periodistas,
> activistas y personas defensoras de derechos humanos.
>
> *A practical, secure tool to document corruption and right-to-housing violations in
> Mexico City — for lawyers, journalists, activists and human-rights defenders.*

**Versión 2.0 · Verificado a junio de 2026 · Sin rastreo, sin cookies, 100 % estático.**

---

## ¿Qué es esto? / What is this?

Un sitio estático autocontenido que entrega:

1. **Un prompt de IA** (ES/EN) que convierte documentos de investigación en una guía
   estructurada de 9 secciones, bajo un principio estricto de **cero inferencia** (cada
   afirmación lleva su cita o se elimina).
2. **Una guía de uso paso a paso**: cómo preparar y cargar documentos, ejecutar el
   prompt, verificar el resultado y usarlo en campo.
3. **Un marco legal verificado** contra fuentes oficiales mexicanas (junio 2026), con
   correcciones a errores frecuentes.
4. **Seguridad operativa (OPSEC) integrada**, porque las personas usuarias están en
   riesgo real.

El sitio es bilingüe: español (`/`, idioma principal) e inglés (`/en/`).

## Principios de diseño / Design principles

- **Seguridad primero.** Cero recursos de terceros (sin Google Fonts, sin CDN, sin
  analítica), sin cookies, sin almacenamiento de datos sensibles. La visita de una
  persona usuaria no se comparte con nadie. Política de seguridad de contenido (CSP)
  estricta y conjunto completo de encabezados de seguridad.
- **Cero dependencias.** HTML, CSS y JavaScript puro (vanilla). Sin paso de compilación,
  sin `npm install`, sin cadena de suministro que comprometer.
- **Funciona sin conexión** y se imprime limpio (uso en campo).
- **Accesible**: HTML semántico, navegación por teclado, contraste alto, respeta
  `prefers-reduced-motion` y `prefers-color-scheme`.

## Estructura / Layout

```
.
├── index.html              # Sitio en español (principal)
├── en/index.html           # Sitio en inglés
├── assets/
│   ├── styles.css          # Estilos (solo fuentes del sistema)
│   ├── app.js              # Comportamiento (copiar, tema, menú, índice)
│   ├── favicon.svg
│   ├── prompt-es.txt       # Prompt descargable (ES)
│   └── prompt-en.txt       # Prompt descargable (EN)
├── _headers                # Encabezados de seguridad (Netlify / Cloudflare Pages)
├── netlify.toml            # Config de despliegue (mismos encabezados)
├── site.webmanifest
├── robots.txt
├── scripts/validate.py     # Suite de validación (pruebas)
└── .github/workflows/      # CI: corre la validación en cada push
```

## Despliegue / Deployment

El sitio son archivos estáticos. No requiere compilación.

### Opción recomendada: Cloudflare Pages o Netlify (encabezados de seguridad completos)

1. Conecta el repositorio.
2. *Build command:* (vacío). *Publish directory:* `.` (la raíz).
3. El archivo `_headers` aplica automáticamente la CSP y demás encabezados de seguridad.

### GitHub Pages

Funciona, pero **GitHub Pages no admite encabezados HTTP personalizados**, así que la
única protección de CSP será la etiqueta `<meta>` incluida en cada página (sin
`frame-ancestors`, que solo opera como encabezado). El archivo `.nojekyll` ya está
incluido para que se sirvan correctamente los archivos como `_headers`. Para protección
completa, usa Cloudflare Pages o Netlify.

### Servicio Tor (.onion) — recomendado para máxima protección

Como el sitio no carga ningún recurso de terceros, es seguro publicarlo también como
servicio onion v3 (el tráfico nunca sale de Tor). Ver `SECURITY.md`.

## Probar localmente / Run locally

```bash
# Servir el sitio
python3 -m http.server 8000
# Abrir http://localhost:8000

# Correr la suite de validación (pruebas)
python3 scripts/validate.py
```

`scripts/validate.py` verifica que: no se cargue ningún recurso de terceros; la CSP esté
presente y sea estricta; no haya código en línea (handlers/estilos/scripts); todos los
enlaces internos resuelvan; existan los archivos requeridos; y que las correcciones
verificadas (p. ej. TFJA en vez de “TECA”, Transparencia para el Pueblo en vez de INAI)
no hayan regresado.

## Mantenimiento / Keeping it current

El marco legal e institucional cambia. Antes de cada versión:

1. Re-verifica leyes e instituciones en las fuentes oficiales (ver la sección *Marco
   legal y fuentes* del sitio).
2. Actualiza la fecha “Verificado a …” en ambas páginas y en los archivos del prompt.
3. Corre `python3 scripts/validate.py`.
4. La Sección 5 (caja jurídica) del resultado **siempre** debe revisarla una persona
   abogada con experiencia en el foro de la CDMX.

## Aviso / Disclaimer

Esta herramienta **no constituye asesoría jurídica** ni sustituye el criterio
profesional. El marco legal fue verificado a junio de 2026; **verifica siempre el texto
vigente** en la fuente oficial. Lee la sección *Seguridad primero* antes de procesar
cualquier material sensible.

## Licencias / Licenses

- **Código** (HTML/CSS/JS y scripts): [MIT](LICENSE).
- **Contenido** (textos de la guía, prompts): Creative Commons **CC BY-SA 4.0**.

Reportes de seguridad: ver [SECURITY.md](SECURITY.md).
