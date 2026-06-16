import re

with open('opera_dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()

scripts = list(re.finditer(r'<script[^>]*>(.*?)</script>', c, re.DOTALL))
inner = None
for m in scripts:
    tag = m.group(0)
    s = m.group(1)
    if 'application/json' in tag or 'importmap' in tag or len(s) < 1000:
        continue
    inner = s
    break

print(f'Script length: {len(inner)} chars')

# More precise brace tracking with function context
braces = 0
in_str = False
esc = False
str_ch = None
fn_depth = 0
last_fns = []

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

    # Skip comments
    if ch == '/' and j+1 < len(inner):
        if inner[j+1] == '/':
            # Skip to end of line
            nl = inner.find('\n', j)
            if nl > j:
                j = nl
            continue
        if inner[j+1] == '*':
            end = inner.find('*/', j+2)
            if end > j:
                j = end + 1
            continue

    if ch == '{':
        braces += 1
        # Check if this is a function body
        # Look backwards for 'function' keyword
        back = inner[max(0,j-50):j]
        if 'function' in back.split('\n')[-1] and '(' in back.split('\n')[-1]:
            fn_depth += 1
            # Extract function name
            m2 = re.search(r'function\s+(\w+)', back)
            fn_name = m2.group(1) if m2 else 'anon'
            last_fns.append(fn_name)
            if len(last_fns) > 5:
                last_fns.pop(0)
    elif ch == '}':
        if braces == 0:
            ctx = 40
            print(f'EXTRA }} at pos {j}: ...{inner[max(0,j-ctx):j+ctx]}...')
            break
        braces -= 1
        if braces == fn_depth:
            fn_depth -= 1

if braces != 0:
    print(f'FINAL: {braces} unbalanced braces')
    # Find the last function that's open
else:
    print('All balanced!')

# Check specific functions
for fn in ['rIntro', 'init3DSpiral', '_build3D', 'rOverview', 'rRole', 'rNetwork', 'rTheme', 'rNarrative', 'initApp']:
    count_open = inner.count(f'function {fn}(')
    print(f'  {fn}: {count_open} definition(s)')
