import re

with open('opera_dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()

scripts = list(re.finditer(r'<script[^>]*>(.*?)</script>', c, re.DOTALL))
for i, m in enumerate(scripts):
    tag = m.group(0)
    inner = m.group(1)
    if 'application/json' in tag or 'importmap' in tag:
        continue
    if len(inner) > 100:
        braces = 0
        in_str = False
        esc = False
        str_ch = None
        last_pos = 0
        for j, ch in enumerate(inner):
            if esc:
                esc = False
                continue
            if ch == '\\':
                esc = True
                continue
            if in_str:
                if ch == in_str:
                    in_str = False
                continue
            if ch in "\"'`":
                in_str = ch
                continue
            if ch == '{':
                braces += 1
            elif ch == '}':
                braces -= 1
                if braces < 0:
                    ctx = 30
                    print(f'Script {i}: extra }} at pos {j}: ...{inner[max(0,j-ctx):j+ctx]}...')
                    break
        if braces == 0:
            print(f'Script {i}: {len(inner)} chars - OK')
        else:
            print(f'Script {i}: {len(inner)} chars - {braces} unbalanced braces')
            break
