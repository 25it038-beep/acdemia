import httpx, asyncio
async def t():
    async with httpx.AsyncClient() as c:
        r = await c.get('http://localhost:3000/')
        html = r.text
        has_css = 'globals.css' in html or '_next/static/css' in html
        has_dark = 'className="dark"' in html or 'class="dark"' in html
        has_white_text = 'text-white' in html
        print(f'Status: {r.status_code}')
        print(f'CSS loaded: {has_css}')
        print(f'Dark class: {has_dark}')
        print(f'White text: {has_white_text}')
        print(f'Size: {len(html)} bytes')
        # Check for any inline black colors
        import re
        colors = set(re.findall(r'color[=:][\s]*[#\w]+', html[:50000]))
        for c in sorted(colors):
            if 'black' in c.lower() or '#000' in c:
                print(f'BLACK COLOR FOUND: {c}')
asyncio.run(t())
