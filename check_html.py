import re
with open('opera_dashboard.html','r',encoding='utf-8') as f:
    c = f.read()

div_open = len(re.findall(r'<div[ >]', c))
div_close = len(re.findall(r'</div>', c))
section_open = len(re.findall(r'<section', c))
section_close = len(re.findall(r'</section>', c))
script_open = len(re.findall(r'<script', c))
script_close = len(re.findall(r'</script>', c))
style_open = len(re.findall(r'<style', c))
style_close = len(re.findall(r'</style>', c))
main_open = len(re.findall(r'<main', c))
main_close = len(re.findall(r'</main>', c))
header_open = len(re.findall(r'<header', c))
header_close = len(re.findall(r'</header>', c))
footer_open = len(re.findall(r'<footer', c))
footer_close = len(re.findall(r'</footer>', c))

print(f'div: {div_open} open, {div_close} close')
print(f'section: {section_open} open, {section_close} close')
print(f'script: {script_open} open, {script_close} close')
print(f'style: {style_open} open, {style_close} close')
print(f'main: {main_open} open, {main_close} close')
print(f'header: {header_open} open, {header_close} close')
print(f'footer: {footer_open} open, {footer_close} close')

# Check specific elements
for elem in ['role-panel', 'tl-panel', 'dash-data', 'allSections', 'mainNav']:
    count = c.count(elem)
    print(f'{elem}: {count} occurrences')

# Check CSS for role-panel
idx = c.find('role-panel')
if idx >= 0:
    print(f'role-panel found at pos {idx}: {c[idx:idx+80]}')
