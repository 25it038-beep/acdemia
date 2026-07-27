import httpx, asyncio, re
async def t():
    async with httpx.AsyncClient() as c:
        r = await c.get('http://localhost:3000/')
        html = r.text
        css_links = re.findall(r'href="([^"]+\.css[^"]*)"', html)
        url = 'http://localhost:3000' + css_links[0]
        r2 = await c.get(url)
        css = r2.text
        idx = css.find(':root')
        print(css[idx:idx+300])
        print('---')
        # Check body color
        if 'body' in css:
            bidx = css.find('body{')
            print(css[bidx:bidx+200])
asyncio.run(t())
