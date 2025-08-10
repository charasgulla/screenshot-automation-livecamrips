import asyncio, argparse, os, time, re, xml.etree.ElementTree as ET
from urllib.parse import urlparse
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright
import requests

def slugify(url: str) -> str:
    u = urlparse(url)
    s = re.sub(r'[^a-zA-Z0-9\-._]', '_', (u.netloc + u.path + ('?' + u.query if u.query else '')))
    return s.strip('_') or 'page'

async def capture_url(browser, url, outdir, prefix="", wait=0, timeout=60000, scale="device"):
    ctx = await browser.new_context(device_scale_factor=1 if scale=="device" else 2)
    page = await ctx.new_page()
    page.set_default_timeout(timeout)
    try:
        await page.goto(url, wait_until="networkidle")
        if wait > 0:
            await page.wait_for_timeout(wait*1000)
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        name = f"{prefix}{slugify(url)}_{ts}.png"
        path = os.path.join(outdir, name)
        await page.screenshot(path=path, full_page=True)
        print(f"✔ Saved: {path}")
    except Exception as e:
        print(f"✖ Failed: {url} -> {e}")
    finally:
        await ctx.close()

async def run(args):
    os.makedirs(args.output, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            if args.mode == "range":
                for n in range(args.start, args.end+1):
                    url = args.template.format(n=n)
                    await capture_url(browser, url, args.output, prefix=args.prefix, wait=args.wait, timeout=args.timeout, scale=args.scale)
                    if args.delay>0: await asyncio.sleep(args.delay)
            elif args.mode == "sitemap":
                r = requests.get(args.sitemap, timeout=60)
                r.raise_for_status()
                root = ET.fromstring(r.content)
                ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                urls = [loc.text for loc in root.findall('.//sm:url/sm:loc', ns)]
                if args.max_urls: urls = urls[:args.max_urls]
                for url in urls:
                    await capture_url(browser, url, args.output, prefix=args.prefix, wait=args.wait, timeout=args.timeout, scale=args.scale)
                    if args.delay>0: await asyncio.sleep(args.delay)
            elif args.mode == "list":
                with open(args.file, 'r', encoding='utf-8') as f:
                    urls = [ln.strip() for ln in f if ln.strip()]
                if args.max_urls: urls = urls[:args.max_urls]
                for url in urls:
                    await capture_url(browser, url, args.output, prefix=args.prefix, wait=args.wait, timeout=args.timeout, scale=args.scale)
                    if args.delay>0: await asyncio.sleep(args.delay)
        finally:
            await browser.close()

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Full-page screenshot automation")
    sub = ap.add_subparsers(dest="mode", required=True)

    # Mode 1: range
    r = sub.add_parser("range", help="Capture numbered pages from a template")
    r.add_argument("--template", required=True, help="URL template with {n}, e.g. https://example.com/list?page={n}")
    r.add_argument("--start", type=int, required=True)
    r.add_argument("--end", type=int, required=True)

    # Mode 2: sitemap
    sm = sub.add_parser("sitemap", help="Capture URLs from an XML sitemap")
    sm.add_argument("--sitemap", required=True, help="https://example.com/sitemap.xml")
    sm.add_argument("--max-urls", type=int, default=0)

    # Mode 3: list
    ls = sub.add_parser("list", help="Capture URLs from a text file (one per line)")
    ls.add_argument("--file", required=True)
    ls.add_argument("--max-urls", type=int, default=0)

    # common
    for p in (r, sm, ls):
        p.add_argument("--output", default="shots")
        p.add_argument("--prefix", default="")
        p.add_argument("--wait", type=int, default=0, help="Extra seconds to wait after load")
        p.add_argument("--timeout", type=int, default=60000)
        p.add_argument("--delay", type=float, default=0.5, help="Delay seconds between pages")
        p.add_argument("--scale", choices=["device","retina"], default="device")

    args = ap.parse_args()
    asyncio.run(run(args))
    
    async def capture_url(browser, url, outdir, prefix="", wait=0, timeout=60000, scale="device"):
    print(f"Capturing screenshot for: {url}")  # Debug line to check which URL is being processed
    ctx = await browser.new_context(device_scale_factor=1 if scale=="device" else 2)
    page = await ctx.new_page()
    page.set_default_timeout(timeout)
    try:
        await page.goto(url, wait_until="networkidle")
        if wait > 0:
            await page.wait_for_timeout(wait*1000)
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        name = f"{prefix}{slugify(url)}_{ts}.png"
        path = os.path.join(outdir, name)
        await page.screenshot(path=path, full_page=True)
        print(f"✔ Saved: {path}")  # Debug line to confirm screenshot was saved
    except Exception as e:
        print(f"✖ Failed: {url} -> {e}")
    finally:
        await ctx.close()

