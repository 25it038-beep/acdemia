import httpx, asyncio, re
async def t():
    async with httpx.AsyncClient() as c:
        r = await c.get('http://localhost:3000/')
        html = r.text
        css_links = re.findall(r'href="([^"]+\.css[^"]*)"', html)
        for link in css_links:
            print(f'CSS: {link[:80]}')
        inline_styles = re.findall(r'<style[^>]*>.*?</style>', html, re.DOTALL)
        print(f'Inline style blocks: {len(inline_styles)}')
        for i, s in enumerate(inline_styles):
            if '--foreground' in s or '--background' in s:
                print(f'  Block {i}: HAS CSS VARIABLES')
            else:
                print(f'  Block {i}: {len(s)} bytes')
        # Also check the actual CSS file
        for link in css_links:
            if link.startswith('/'):
                full_url = f'http://localhost:3000{link}'
                r2 = await c.get(full_url)
                if '--foreground' in r2.text:
                    print(f'CSS file has variables: YES')
                    break
asyncio.run(t())
