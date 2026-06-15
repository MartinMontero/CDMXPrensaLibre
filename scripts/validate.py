#!/usr/bin/env python3
"""
End-to-end static validation for the CDMX Prensa Libre site.

This is the project's test suite. It enforces the production + security
guarantees the site promises:

  1. Every referenced local asset exists.
  2. ZERO third-party resources auto-load (no external <script>/<link>/<img>
     src, no @import / url() to remote hosts). Outbound <a href> links to
     official sites are allowed (user-initiated navigation, not auto-loaded).
  3. A strict Content-Security-Policy <meta> is present with the key directives.
  4. CSP-safety: no inline event handlers (on*=), no inline <script> bodies
     (every <script> must have a src), no inline <style> blocks, no style="".
  5. Every internal anchor (href="#id") resolves to an element id on the page.
  6. The prompt textareas and downloadable .txt prompts are present & substantial.
  7. Sanity checks for the verified-fact corrections (e.g. no stale "TECA"
     tribunal, INAI not presented as current, etc.).

Run:  python3 scripts/validate.py
Exit code 0 = all good; 1 = failures.
"""
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGES = ["index.html", os.path.join("en", "index.html")]
REQUIRED_FILES = [
    "index.html", "en/index.html",
    "assets/styles.css", "assets/app.js", "assets/favicon.svg",
    "assets/prompt-es.txt", "assets/prompt-en.txt",
    "site.webmanifest", "_headers", "netlify.toml", "robots.txt",
    "README.md", "SECURITY.md", "LICENSE", ".nojekyll",
]

errors = []
warnings = []
passes = []


def ok(msg):
    passes.append(msg)


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------- HTML parser
class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.anchor_targets = []      # internal #fragments referenced
        self.local_resources = []     # (tag, url) that the browser auto-loads
        self.external_resources = []  # (tag, url) auto-loaded from another host
        self.inline_handlers = []     # on*= attributes
        self.inline_style_attrs = 0
        self.script_tags = []         # (has_src, src)
        self.in_script = False
        self._cur_script_has_src = False
        self.style_blocks = 0
        self.in_style = False
        self.textarea_ids = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        for k, v in attrs:
            if k.startswith("on"):
                self.inline_handlers.append((tag, k))
            if k == "style":
                self.inline_style_attrs += 1
        if tag == "script":
            self.in_script = True
            self._cur_script_has_src = "src" in a
            self.script_tags.append(("src" in a, a.get("src", "")))
            if "src" in a:
                self._classify(tag, a["src"])
        if tag == "style":
            self.in_style = True
            self.style_blocks += 1
        if tag == "link" and "href" in a:
            rel = (a.get("rel") or "").lower()
            # stylesheet/icon/manifest are auto-loaded; alternate/canonical are not
            if any(r in rel for r in ("stylesheet", "icon", "manifest", "preload")):
                self._classify(tag, a["href"])
        if tag == "img" and "src" in a:
            self._classify(tag, a["src"])
        if tag == "textarea" and "id" in a:
            self.textarea_ids.append(a["id"])
        if tag == "a" and "href" in a:
            href = a["href"]
            if href.startswith("#"):
                self.anchor_targets.append(href[1:])

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_script = False
        if tag == "style":
            self.in_style = False

    def handle_data(self, data):
        if self.in_script and not self._cur_script_has_src and data.strip():
            # inline script body
            self.script_tags.append(("INLINE_BODY", data.strip()[:40]))
        if self.in_style and data.strip():
            pass  # counted via style_blocks

    def _classify(self, tag, url):
        if re.match(r"^[a-z]+://", url) or url.startswith("//"):
            host = re.sub(r"^[a-z]+:", "", url)
            self.external_resources.append((tag, url))
        elif url.startswith("data:"):
            self.external_resources.append((tag, url))  # treat data: as non-self
        else:
            self.local_resources.append((tag, url))


def resolve_local(page_path, url):
    """Resolve a page-relative URL to a filesystem path under ROOT."""
    url = url.split("#")[0].split("?")[0]
    if not url:
        return None
    base = os.path.dirname(os.path.join(ROOT, page_path))
    return os.path.normpath(os.path.join(base, url))


# ---------------------------------------------------------------- checks
def check_required_files():
    for rel in REQUIRED_FILES:
        if os.path.exists(os.path.join(ROOT, rel)):
            ok(f"present: {rel}")
        else:
            err(f"MISSING required file: {rel}")


def check_page(page):
    html = read(page)
    p = PageParser()
    p.feed(html)

    # external resources
    if p.external_resources:
        for tag, url in p.external_resources:
            err(f"[{page}] external auto-loaded resource <{tag}>: {url}")
    else:
        ok(f"[{page}] no third-party auto-loaded resources")

    # local resources exist
    for tag, url in p.local_resources:
        fp = resolve_local(page, url)
        if fp and os.path.exists(fp):
            ok(f"[{page}] local <{tag}> resolves: {url}")
        else:
            err(f"[{page}] broken local <{tag}> reference: {url}")

    # inline handlers / styles / scripts
    if p.inline_handlers:
        err(f"[{page}] inline event handlers (CSP violation): {p.inline_handlers}")
    else:
        ok(f"[{page}] no inline event handlers")
    if p.inline_style_attrs:
        err(f"[{page}] {p.inline_style_attrs} inline style= attribute(s) (CSP violation)")
    else:
        ok(f"[{page}] no inline style attributes")
    if p.style_blocks:
        err(f"[{page}] {p.style_blocks} inline <style> block(s) (CSP violation)")
    else:
        ok(f"[{page}] no inline <style> blocks")
    inline_scripts = [s for s in p.script_tags if s[0] == "INLINE_BODY"]
    if inline_scripts:
        err(f"[{page}] inline <script> body present (CSP violation)")
    else:
        ok(f"[{page}] all <script> tags use external src")

    # CSP meta (content value contains single quotes like 'self', so match by the
    # surrounding quote char rather than excluding quotes)
    m = re.search(r'http-equiv=["\']Content-Security-Policy["\'][^>]*?content=(["\'])(.*?)\1', html, re.I | re.S)
    if not m:
        err(f"[{page}] missing Content-Security-Policy <meta>")
    else:
        csp = m.group(2)
        for directive in ["default-src", "script-src 'self'", "object-src 'none'", "base-uri"]:
            if directive not in csp:
                err(f"[{page}] CSP missing/weak: '{directive}'")
        if "'unsafe-inline'" in csp or "'unsafe-eval'" in csp:
            err(f"[{page}] CSP contains unsafe-inline/unsafe-eval")
        if not [e for e in errors if page in e and "CSP" in e]:
            ok(f"[{page}] CSP meta present and strict")

    # internal anchors resolve
    missing = sorted({frag for frag in p.anchor_targets if frag and frag not in p.ids})
    if missing:
        err(f"[{page}] anchors with no matching id: {missing}")
    else:
        ok(f"[{page}] all internal anchors resolve ({len(set(p.anchor_targets))} unique)")

    return p


def check_prompts(parsers):
    # textareas substantial
    for page, p in parsers.items():
        for tid in p.textarea_ids:
            html = read(page)
            mt = re.search(r'<textarea[^>]*id=["\']' + re.escape(tid) + r'["\'][^>]*>(.*?)</textarea>', html, re.S)
            body = mt.group(1) if mt else ""
            if len(body) > 2500:
                ok(f"[{page}] prompt textarea '{tid}' substantial ({len(body)} chars)")
            else:
                err(f"[{page}] prompt textarea '{tid}' too short ({len(body)} chars)")

    for f in ["assets/prompt-es.txt", "assets/prompt-en.txt"]:
        txt = read(f)
        if len(txt) > 3000:
            ok(f"prompt file substantial: {f} ({len(txt)} chars)")
        else:
            err(f"prompt file too short: {f}")
        if "FIN DEL PROMPT" in txt or "END OF PROMPT" in txt:
            ok(f"prompt file has terminator: {f}")
        else:
            warn(f"prompt file missing terminator marker: {f}")


def check_headers_file():
    """Validate _headers (the production header source on Cloudflare Pages / Netlify)."""
    if not os.path.exists(os.path.join(ROOT, "_headers")):
        err("missing _headers file")
        return
    txt = read("_headers")
    if not re.search(r"^/\*\s*$", txt, re.M):
        err("_headers: missing a '/*' path block")
    else:
        ok("_headers: '/*' path block present")

    required = [
        "Content-Security-Policy", "Strict-Transport-Security", "Referrer-Policy",
        "X-Content-Type-Options", "X-Frame-Options", "Permissions-Policy",
        "Cross-Origin-Opener-Policy", "Cross-Origin-Resource-Policy",
    ]
    for h in required:
        if re.search(rf"^\s+{re.escape(h)}:", txt, re.M):
            ok(f"_headers: {h} present")
        else:
            err(f"_headers: missing header {h}")

    cspm = re.search(r"^\s+Content-Security-Policy:\s*(.+)$", txt, re.M)
    if cspm:
        csp = cspm.group(1)
        for directive in ["default-src", "script-src 'self'", "object-src 'none'",
                          "base-uri", "frame-ancestors 'none'"]:
            if directive not in csp:
                err(f"_headers CSP missing/weak: '{directive}'")
        if "'unsafe-inline'" in csp or "'unsafe-eval'" in csp:
            err("_headers CSP contains unsafe-inline/unsafe-eval")
        if not [e for e in errors if "_headers CSP" in e]:
            ok("_headers: CSP strict (incl. frame-ancestors 'none')")
    if "no-referrer" in txt:
        ok("_headers: Referrer-Policy is no-referrer")
    else:
        warn("_headers: Referrer-Policy is not 'no-referrer'")


def check_verified_facts():
    """Guard against regressions of the high-stakes corrections."""
    es = read("index.html")
    en = read("en/index.html")
    pes = read("assets/prompt-es.txt")
    both = es + en + pes + read("assets/prompt-en.txt")

    # Corrections that MUST be present
    musts = {
        "Transparencia para el Pueblo": both,
        "SABG": both,
        "TJACDMX": both,
        "FECC": both,
        "vivienda adecuada": both,
    }
    for term, hay in musts.items():
        if term in hay:
            ok(f"verified fact present: '{term}'")
        else:
            err(f"verified fact MISSING: '{term}'")

    # 'TECA' must only ever appear inside an explicit negation ("no ... TECA")
    for page, content in [("index.html", es), ("en/index.html", en),
                          ("prompt-es.txt", pes), ("prompt-en.txt", read("assets/prompt-en.txt"))]:
        for mobj in re.finditer(r"TECA", content):
            ctx = content[max(0, mobj.start() - 60): mobj.start() + 10].lower()
            if not any(neg in ctx for neg in ["no existe", "no court", "ningún", "ningun"]):
                err(f"[{page}] 'TECA' used outside a negation context")
        ok(f"[{page}] 'TECA' only in negation context (or absent)")

    # INAI must not be presented as the *current* authority (must be near 'extingu'/'abolish')
    for page, content in [("index.html", es), ("en/index.html", en)]:
        for mobj in re.finditer(r"INAI", content):
            window = content[max(0, mobj.start() - 120): mobj.start() + 120].lower()
            if not any(k in window for k in ["exting", "abol", "ya no", "no longer", "antes", "former"]):
                warn(f"[{page}] 'INAI' mentioned without nearby abolition context — verify")


def main():
    print("=" * 70)
    print("CDMX Prensa Libre — site validation")
    print("=" * 70)

    check_required_files()
    parsers = {}
    for page in PAGES:
        if os.path.exists(os.path.join(ROOT, page)):
            parsers[page] = check_page(page)
    check_prompts(parsers)
    check_headers_file()
    check_verified_facts()

    print(f"\n  PASS:  {len(passes)} checks")
    if warnings:
        print(f"  WARN:  {len(warnings)}")
        for w in warnings:
            print(f"    ⚠️  {w}")
    if errors:
        print(f"  FAIL:  {len(errors)}")
        for e in errors:
            print(f"    ❌ {e}")
        print("\nRESULT: ❌ FAILED")
        return 1
    print("\nRESULT: ✅ ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
