#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
将 opera_dashboard.json 数据注入 HTML 模板。
改为使用 <script type="application/json"> + JSON.parse() 方式，
彻底避免 JSON 嵌入为 JS 对象时可能出现的兼容性问题。
"""

import json

def main():
    print("读取 opera_dashboard.json...")
    with open('opera_dashboard.json', 'r', encoding='utf-8') as f:
        dashboard = json.load(f)

    print("读取 index.html 模板...")
    with open('index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 将数据转为 JSON 字符串（用于嵌入 HTML）
    dashboard_json = json.dumps(dashboard, ensure_ascii=False)

    # 替换方案：将 JSON 数据放入 <script type="application/json" id="dash-data"> 标签
    # JS 代码通过 JSON.parse(document.getElementById('dash-data').textContent) 读取
    # 这样 JSON 中的任何字符都不会破坏 JS 解析

    # 找到数据占位符位置，替换为 JSON 数据标签
    if '%DASHBOARD_DATA_PLACEHOLDER%' in html:
        html = html.replace(
            '%DASHBOARD_DATA_PLACEHOLDER%',
            dashboard_json
        )
        print("数据占位符已替换")
    else:
        print("警告：未找到 %DASHBOARD_DATA_PLACEHOLDER% 占位符")

    # 同时替换数据标签方案
    if '%DASHBOARD_JSON_DATA%' in html:
        html = html.replace('%DASHBOARD_JSON_DATA%', dashboard_json)
        print("JSON数据标签已替换")

    # 写入最终 HTML
    output_file = 'opera_dashboard.html'
    print(f"写入 {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    import os
    size_kb = os.path.getsize(output_file) / 1024
    print(f"生成完成: {output_file} ({size_kb:.0f} KB)")


if __name__ == '__main__':
    main()
