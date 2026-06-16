#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从 opera_data.json 生成精简的仪表板数据文件
- opera_dashboard.json: 嵌入HTML的聚合统计数据（<200KB）
- opera_index.json: 剧本索引（供搜索使用，由HTML fetch加载）
"""

import json
from collections import Counter, defaultdict

def main():
    print("正在读取 opera_data.json...")
    with open('opera_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    operas = data['operas']
    print(f"共 {len(operas)} 个剧本")

    # ===== 角色分类映射 =====
    role_category_map = {
        '生': ['老生', '小生', '武生', '红生', '生'],
        '旦': ['正旦', '青衣', '花旦', '武旦', '刀马旦', '老旦', '彩旦', '旦', '小旦', '花衫', '闺门旦'],
        '净': ['净', '铜锤花脸', '架子花脸', '武花脸', '大花脸', '二花脸', '花脸'],
        '丑': ['丑', '文丑', '武丑', '小丑', '方巾丑', '袍带丑', '丑旦'],
        '其他': ['外', '末', '杂', '贴', '副', '众'],
    }
    role_normalize = {
        '青衣': '正旦', '花衫': '旦', '闺门旦': '旦', '小旦': '旦',
        '铜锤花脸': '净', '架子花脸': '净', '武花脸': '净', '大花脸': '净', '二花脸': '净', '花脸': '净',
        '文丑': '丑', '武丑': '丑', '小丑': '丑', '方巾丑': '丑', '袍带丑': '丑', '丑旦': '丑',
        '娃娃生': '小生', '红生': '老生', '武生': '生', '刀马旦': '武旦', '彩旦': '旦',
        '末': '老生', '外': '老生', '副': '净', '杂': '其他', '贴': '旦',
    }

    def get_category(rt):
        rt = role_normalize.get(rt, rt)
        for cat, types in role_category_map.items():
            if rt in types:
                return cat
        return '其他'

    # ==========================================
    # Part 1: 聚合统计数据（嵌入HTML）
    # ==========================================

    # 全局概览
    overview = {
        'total_operas': len(operas),
        'total_characters': sum(o['character_count'] for o in operas),
        'total_sources': len(set(o['source'] for o in operas)),
        'total_directories': len(set(o['directory'] for o in operas)),
        'avg_scenes': round(sum(o['scene_count'] for o in operas) / len(operas), 1),
        'avg_characters': round(sum(o['character_count'] for o in operas) / len(operas), 1),
        'max_scenes': max(o['scene_count'] for o in operas),
        'max_characters': max(o['character_count'] for o in operas),
    }

    # 来源分布
    source_dist = Counter(o['source'] for o in operas)
    source_data = [{'name': s, 'value': c} for s, c in source_dist.most_common(20)]

    # 目录分布
    dir_dist = Counter(o['directory'] for o in operas)

    # 目录分类推断
    dir_category_guess = {}
    for d in dir_dist:
        first_two = d[:2]
        if first_two == '01':
            dir_category_guess[d] = '戏考·传统剧目'
        elif first_two == '02':
            dir_category_guess[d] = '戏考·历史剧目'
        elif first_two == '03':
            dir_category_guess[d] = '戏考·家庭伦理'
        elif first_two == '04':
            dir_category_guess[d] = '戏考·公案剧目'
        elif first_two == '05':
            dir_category_guess[d] = '戏考·其他'
        elif first_two == '70':
            dir_category_guess[d] = '京剧汇编'
        elif first_two == '80':
            dir_category_guess[d] = '名家演出本'
        elif first_two == '90' or first_two == '94':
            dir_category_guess[d] = '昆曲/其他剧种'
        else:
            dir_category_guess[d] = f'其他分类'

    dir_data = [{'name': d, 'value': c, 'category': dir_category_guess.get(d, '未知')}
                for d, c in dir_dist.most_common()]

    # 行当统计
    role_cat_counter = Counter()
    role_type_counter = Counter()
    for o in operas:
        for c in o['characters']:
            cat = get_category(c['role_type'])
            role_cat_counter[cat] += 1
            role_type_counter[c['role_type']] += 1

    role_cat_data = [{'name': k, 'value': v} for k, v in role_cat_counter.most_common()]
    role_type_data = [{'name': k, 'value': v} for k, v in role_type_counter.most_common(30)]

    # 目录-行当交叉
    top_dirs = [d for d, _ in dir_dist.most_common(15)]
    role_cats = ['生', '旦', '净', '丑', '其他']
    dir_role_cross = defaultdict(Counter)
    for o in operas:
        d = o['directory']
        for c in o['characters']:
            cat = get_category(c['role_type'])
            dir_role_cross[d][cat] += 1
    dir_role_data = {
        'directories': [dir_category_guess.get(d, d) for d in top_dirs],
        'categories': role_cats,
        'data': [[dir_role_cross[d].get(c, 0) for c in role_cats] for d in top_dirs],
    }

    # 主题统计
    theme_counter = Counter()
    for o in operas:
        for t in o['themes']:
            theme_counter[t] += 1
    theme_data = [{'name': k, 'value': v} for k, v in theme_counter.most_common()]

    # 主题组合
    theme_combo_counter = Counter()
    for o in operas:
        combo = ' + '.join(sorted(o['themes'])) if o['themes'] else '未分类'
        theme_combo_counter[combo] += 1
    theme_combo_data = [{'name': k, 'value': v} for k, v in theme_combo_counter.most_common(12)]

    # 唱腔统计
    style_counter = Counter()
    for o in operas:
        for style, count in o['singing_styles'].items():
            style_counter[style] += count
    style_data = [{'name': k, 'value': v} for k, v in style_counter.most_common()]

    # 场次分布
    scene_counter = Counter(o['scene_count'] for o in operas)
    scene_data = [{'scenes': k, 'count': v} for k, v in sorted(scene_counter.items()) if k > 0]

    # 角色数分布
    char_counter = Counter(o['character_count'] for o in operas)
    char_dist_data = [{'chars': k, 'count': v} for k, v in sorted(char_counter.items()) if k > 0]

    # 剧本长度分布
    length_bins = [('短篇(<1K)', 0, 1000), ('中短篇(1K-3K)', 1000, 3000),
                   ('中篇(3K-6K)', 3000, 6000), ('中长篇(6K-10K)', 6000, 10000),
                   ('长篇(10K-20K)', 10000, 20000), ('超长篇(>20K)', 20000, 999999)]
    length_dist_data = []
    for label, lo, hi in length_bins:
        cnt = sum(1 for o in operas if lo <= o['body_length'] < hi)
        length_dist_data.append({'range': label, 'count': cnt})

    # 关键词云
    all_keywords = Counter()
    for o in operas:
        for kw in o['keywords']:
            all_keywords[kw['word']] += kw['weight']
    wordcloud_data = [{'name': w, 'value': round(v, 2)} for w, v in all_keywords.most_common(150)]

    # 角色网络（精简版）
    char_name_counter = Counter()
    for o in operas:
        names_seen = set()
        for c in o['characters']:
            if c['name'] not in names_seen:
                char_name_counter[c['name']] += 1
                names_seen.add(c['name'])

    top_chars = char_name_counter.most_common(80)
    top_char_names = set(name for name, _ in top_chars)

    edges_counter = Counter()
    for o in operas:
        names_in_opera = [c['name'] for c in o['characters'] if c['name'] in top_char_names]
        for i in range(len(names_in_opera)):
            for j in range(i+1, len(names_in_opera)):
                edges_counter[(names_in_opera[i], names_in_opera[j])] += 1

    network_edges = []
    for (src, tgt), weight in edges_counter.most_common(250):
        if weight >= 2:
            network_edges.append({'source': src, 'target': tgt, 'weight': weight})

    network_nodes = [{'name': name, 'count': count, 'symbolSize': min(count * 2, 60)}
                     for name, count in top_chars]

    character_network = {'nodes': network_nodes, 'edges': network_edges}

    # 数据集目录分布（用于旭日图）
    sunburst_data = []
    cat_counter = Counter()
    for d in dir_data:
        cat = d['category']
        cat_counter[cat] += d['value']
    for cat, total in cat_counter.most_common():
        children = []
        for d in dir_data:
            if d['category'] == cat:
                children.append({'name': d['name'], 'value': d['value']})
        sunburst_data.append({'name': cat, 'children': children})

    # 来源-主题交叉分析
    source_theme_cross = defaultdict(Counter)
    for o in operas:
        for t in o['themes']:
            source_theme_cross[o['source']][t] += 1
    top_themes_for_heatmap = [t for t, _ in theme_counter.most_common(10)]
    source_theme_data = {
        'sources': [s for s, _ in source_dist.most_common(12)],
        'themes': top_themes_for_heatmap,
        'data': [[source_theme_cross[s].get(t, 0) for t in top_themes_for_heatmap]
                 for s in [x['name'] for x in source_data[:12]]],
    }

    # ===== 组装Dashboard数据 =====
    dashboard = {
        'overview': overview,
        'source_distribution': source_data,
        'directory_distribution': dir_data,
        'sunburst_data': sunburst_data,
        'role_category_distribution': role_cat_data,
        'role_type_distribution': role_type_data,
        'dir_role_cross': dir_role_data,
        'theme_distribution': theme_data,
        'theme_combo_distribution': theme_combo_data,
        'source_theme_cross': source_theme_data,
        'style_distribution': style_data,
        'scene_distribution': scene_data,
        'char_distribution': char_dist_data,
        'length_distribution': length_dist_data,
        'character_network': character_network,
        'wordcloud': wordcloud_data,
    }

    print("正在保存 opera_dashboard.json...")
    with open('opera_dashboard.json', 'w', encoding='utf-8') as f:
        json.dump(dashboard, f, ensure_ascii=False)

    import os
    size_kb = os.path.getsize('opera_dashboard.json') / 1024
    print(f"opera_dashboard.json 已保存 ({size_kb:.0f} KB)")

    # ==========================================
    # Part 2: 剧本索引（供搜索/表格）
    # ==========================================
    # 目录→来源推断
    dir_src_map = {'01':'戏考','02':'戏考','03':'戏考','04':'戏考','05':'戏考','70':'京剧汇编','80':'名家演出本','90':'昆曲/其他'}
    def infer_source(src, d):
        if src and src != '未知': return src
        prefix = d[:2] if d else ''
        return dir_src_map.get(prefix, f'分类{d}')

    opera_index = []
    for o in operas:
        opera_index.append({
            'id': o['id'],
            'title': o['title'],
            'aliases': '、'.join(o['aliases']) if o['aliases'] else '',
            'source': infer_source(o['source'], o['directory']),
            'directory': o['directory'],
            'dir_category': dir_category_guess.get(o['directory'], '未知'),
            'character_count': o['character_count'],
            'scene_count': o['scene_count'],
            'themes': o['themes'],
            'body_length': o['body_length'],
            'plot_brief': o['plot_summary'][:120],
            'characters': [f"{c['name']}:{c['role_type']}" for c in o['characters'][:15]],
        })

    print("正在保存 opera_index.json...")
    with open('opera_index.json', 'w', encoding='utf-8') as f:
        json.dump(opera_index, f, ensure_ascii=False)

    size_kb2 = os.path.getsize('opera_index.json') / 1024
    print(f"opera_index.json 已保存 ({size_kb2:.0f} KB)")
    print(f"\n总计: dashboard {size_kb:.0f}KB + index {size_kb2:.0f}KB")


if __name__ == '__main__':
    main()
