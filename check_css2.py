import httpx, asyncio, re
async def t():
    async with httpx.AsyncClient() as c:
        r = await c.get('http://localhost:3000/')
        html = r.text
        css_links = re.findall(r'href="([^"]+\.css[^"]*)"', html)
        print(f'CSS file: {css_links[0][:50]}')
        url = 'http://localhost:3000' + css_links[0]
        r2 = await c.get(url)
        css = r2.text
        has_vars = '--foreground' in css
        has_bg = '--background' in css
        print(f'Has --foreground: {has_vars}')
        print(f'Has --background: {has_bg}')
        if not has_vars:
            print(f'Response type: {r2.headers.get("content-type")}')
            print(f'CSS starts: {css[:300]}')
        else:
            print('OK - CSS variables found in stylesheet')
asyncio.run(t())
