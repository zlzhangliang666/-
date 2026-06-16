#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ChinaVis 2026 京剧剧本数据解析脚本
解析 merged_content.txt，生成结构化 JSON 和 Excel 统计文件
"""

import re
import json
import os
from collections import Counter, defaultdict
import jieba
import jieba.analyse
import pandas as pd

# ============ 配置 ============
INPUT_FILE = "merged_content.txt"
OUTPUT_JSON = "opera_data.json"
OUTPUT_XLSX = "opera_statistics.xlsx"

# 京剧行当分类体系
ROLE_CATEGORIES = {
    '生': ['老生', '小生', '武生', '红生', '娃娃生', '生'],
    '旦': ['正旦', '青衣', '花旦', '武旦', '刀马旦', '老旦', '彩旦', '闺门旦', '旦', '小旦', '花衫'],
    '净': ['净', '铜锤花脸', '架子花脸', '武花脸', '大花脸', '二花脸', '花脸'],
    '丑': ['丑', '文丑', '武丑', '小丑', '方巾丑', '袍带丑', '丑旦'],
    '其他': ['外', '末', '杂', '贴', '副', '众'],
}

# 行当标准化映射
ROLE_NORMALIZE = {
    '青衣': '正旦', '花衫': '旦', '闺门旦': '旦', '小旦': '旦',
    '铜锤花脸': '净', '架子花脸': '净', '武花脸': '净', '大花脸': '净', '二花脸': '净', '花脸': '净',
    '文丑': '丑', '武丑': '丑', '小丑': '丑', '方巾丑': '丑', '袍带丑': '丑', '丑旦': '丑',
    '娃娃生': '小生', '红生': '老生', '武生': '生',
    '刀马旦': '武旦', '彩旦': '旦',
    '末': '老生', '外': '老生', '副': '净', '杂': '其他', '贴': '旦',
}

# 剧本主题关键词列表（用于主题分类）
THEME_KEYWORDS = {
    '忠义爱国': ['忠', '义', '报国', '救国', '抗敌', '御敌', '杀敌', '卫国', '殉国', '忠臣', '忠良', '报效', '尽忠', '捐躯'],
    '爱情婚姻': ['姻缘', '婚姻', '夫妻', '相思', '爱', '情', '配', '婚', '嫁', '娶', '媒', '缘', '相思', '红娘', '鸳鸯', '良缘'],
    '家庭伦理': ['教子', '母子', '父子', '兄弟', '孝', '侍奉', '养老', '家庭', '家', '堂', '母', '父', '子', '儿女', '亲', '认亲'],
    '官场公案': ['审', '案', '冤', '官', '断', '判', '法', '诉', '告', '状', '清官', '知府', '知县', '御史', '巡按', '伸冤', '昭雪', '贪官'],
    '战争军事': ['战', '征', '伐', '兵', '军', '阵', '将', '破', '攻', '守', '胜', '败', '围', '伐', '讨', '厮杀', '征讨'],
    '神怪奇幻': ['仙', '妖', '鬼', '神', '怪', '龙', '狐', '梦', '幻', '变', '化', '灵', '魂', '魄', '天堂', '地狱', '佛祖', '菩萨', '道', '法术'],
    '侠义英雄': ['侠', '英', '豪', '杰', '义士', '好汉', '打抱不平', '锄奸', '除暴', '安良', '英雄', '好汉'],
    '历史典故': ['三国', '隋唐', '宋', '明', '清', '春秋', '战国', '汉', '唐', '史记', '演义', '传'],
    '宫廷权谋': ['帝', '王', '皇', '宫', '殿', '妃', '嫔', '太子', '篡', '谋', '篡位', '夺权', '朝', '权臣', '宦官'],
    '民间生活': ['耕种', '渔', '樵', '柴', '米', '酒', '茶', '市', '村', '乡', '民', '百姓', '田', '农'],
    '才子佳人': ['才子', '佳人', '书生', '小姐', '赶考', '科举', '状元', '秀才', '举人', '读书', '诗', '文', '琴', '棋', '书', '画'],
    '因果报应': ['报应', '因果', '积德', '行善', '作恶', '报', '善有善报', '恶有恶报', '天理', '轮回'],
}

# ============ 工具函数 ============

def clean_text(text):
    """清洗文本：移除URL、PDF工具信息等"""
    # 移除URL
    text = re.sub(r'https?://\S+', '', text)
    # 移除日期标记
    text = re.sub(r'\d{4}-\d{2}-\d{2}\s*$', '', text, flags=re.MULTILINE)
    # 移除PDF工具信息
    text = re.sub(r'Powered by TCPDF.*', '', text)
    # 移除页码标记（如"中国京剧戏考 《空城计》 1"）
    text = re.sub(r'中国京剧戏考 《[^》]+》 \d+\s*', '', text)
    # 移除多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def normalize_role_type(role_type):
    """标准化行当名称"""
    role_type = role_type.strip()
    if role_type in ROLE_NORMALIZE:
        return ROLE_NORMALIZE[role_type]
    return role_type


def get_role_category(role_type):
    """获取行当大类"""
    role_type = normalize_role_type(role_type)
    for cat, types in ROLE_CATEGORIES.items():
        if role_type in types:
            return cat
    return '其他'


def extract_themes(plot_text):
    """从情节文本中提取主题"""
    themes = []
    plot_lower = plot_text
    for theme, keywords in THEME_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in plot_lower)
        if score >= 2:
            themes.append(theme)
    return themes if themes else ['其他']


def extract_keywords_tfidf(text, topk=10):
    """使用jieba提取TF-IDF关键词"""
    if not text or len(text) < 20:
        return []
    try:
        keywords = jieba.analyse.extract_tags(text, topK=topk, withWeight=True)
        return [{'word': w, 'weight': round(weight, 4)} for w, weight in keywords]
    except:
        return []


def count_scenes(script_body):
    """统计场次数量"""
    scenes = re.findall(r'【第[一二三四五六七八九十百千万\d]+场】', script_body)
    return len(scenes)


def detect_singing_styles(script_body):
    """检测唱腔类型"""
    styles = Counter()
    style_patterns = {
        '西皮': r'西皮',
        '二黄': r'二黄',
        '反二黄': r'反二黄',
        '四平调': r'四平调',
        '南梆子': r'南梆子',
        '高拨子': r'高拨子',
        '吹腔': r'吹腔',
        '昆曲': r'昆曲',
    }
    for style, pattern in style_patterns.items():
        count = len(re.findall(pattern, script_body))
        if count > 0:
            styles[style] = count
    return dict(styles)


# ============ 主解析逻辑 ============

def parse_merged_file(filepath):
    """解析合并的文本文件"""
    print(f"正在读取文件: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"文件大小: {len(content)} 字符")

    # 按分隔符切分各剧本
    # 分隔符格式: ==========...\n文件: ...\n==========...
    pattern = r'={50,}\s*\n文件:\s*(.+?)\n={50,}\s*\n'
    parts = re.split(pattern, content)

    # parts[0] 是第一个分隔符之前的内容（空），然后交替出现 [文件路径, 剧本内容, 文件路径, 剧本内容, ...]
    scripts = []
    for i in range(1, len(parts), 2):
        if i+1 < len(parts):
            file_path = parts[i].strip()
            script_content = parts[i+1].strip()
            scripts.append((file_path, script_content))

    print(f"共找到 {len(scripts)} 个剧本文件")

    opera_list = []
    parse_errors = 0

    for idx, (file_path, raw_content) in enumerate(scripts):
        try:
            # 清洗内容
            cleaned = clean_text(raw_content)

            # 提取标题
            title_match = re.search(r'《(.+?)》', cleaned)
            title = title_match.group(1) if title_match else "未知"

            # 提取别名
            alias_match = re.search(r'（一名：《(.+?)》）', cleaned)
            aliases = [alias_match.group(1)] if alias_match else []
            # 可能有多个别名
            alias_matches = re.findall(r'（一名：《(.+?)》）', cleaned)
            if len(alias_matches) > 1:
                aliases = alias_matches

            # 提取主要角色
            role_section_match = re.search(r'主要角色\s*\n(.*?)(?:\n情节|\n注释|\n根据)', cleaned, re.DOTALL)
            characters = []
            if role_section_match:
                role_text = role_section_match.group(1).strip()
                for line in role_text.split('\n'):
                    line = line.strip()
                    if '：' in line or '：' in line.replace('：', ':'):
                        parts_role = re.split('[：:]', line, maxsplit=1)
                        if len(parts_role) == 2:
                            char_name = parts_role[0].strip()
                            role_type = parts_role[1].strip()
                            if char_name and role_type:
                                characters.append({
                                    'name': char_name,
                                    'role_type': role_type,
                                    'role_normalized': normalize_role_type(role_type),
                                    'role_category': get_role_category(role_type),
                                })

            # 提取情节
            plot_match = re.search(r'情节\s*\n(.*?)(?:\n注释|\n根据|$)', cleaned, re.DOTALL)
            plot_summary = plot_match.group(1).strip() if plot_match else ""

            # 提取注释
            notes_match = re.search(r'注释\s*\n(.*?)(?:\n根据《|$)', cleaned, re.DOTALL)
            notes = notes_match.group(1).strip() if notes_match else ""

            # 提取来源
            source_match = re.search(r'根据《(.+?)》整理', cleaned)
            source = source_match.group(1) if source_match else "未知"

            # 提取剧本正文（从第一场开始）
            body_match = re.search(r'(【第[一二三四五六七八九十百千万\d]+场】.*)', cleaned, re.DOTALL)
            script_body = body_match.group(1) if body_match else cleaned

            # 统计信息
            scene_count = count_scenes(script_body)
            singing_styles = detect_singing_styles(script_body)
            body_length = len(script_body)
            character_count = len(characters)

            # 目录分类
            dir_match = re.search(r'京剧剧本[\\/]([^\\/]+)', file_path)
            directory = dir_match.group(1) if dir_match else "未知"

            # 提取主题
            themes = extract_themes(plot_summary)

            # 提取关键词
            full_text_for_keywords = plot_summary + ' ' + (notes or '')
            keywords = extract_keywords_tfidf(full_text_for_keywords, topk=8)

            opera = {
                'id': idx + 1,
                'file_path': file_path,
                'directory': directory,
                'title': title,
                'aliases': aliases,
                'source': source,
                'characters': characters,
                'character_count': character_count,
                'plot_summary': plot_summary,
                'notes': notes,
                'scene_count': scene_count,
                'body_length': body_length,
                'singing_styles': singing_styles,
                'themes': themes,
                'keywords': keywords,
            }
            opera_list.append(opera)

            if (idx + 1) % 200 == 0:
                print(f"  已处理 {idx + 1}/{len(scripts)} 个剧本...")

        except Exception as e:
            parse_errors += 1
            if parse_errors <= 5:
                print(f"  解析错误 ({file_path}): {e}")

    print(f"解析完成: {len(opera_list)} 个成功, {parse_errors} 个失败")
    return opera_list


# ============ 生成统计和Excel ============

def generate_statistics(opera_list):
    """生成各种统计"""

    # 全局统计
    all_characters = []
    for opera in opera_list:
        for char in opera['characters']:
            all_characters.append({
                'opera_id': opera['id'],
                'opera_title': opera['title'],
                'opera_directory': opera['directory'],
                'opera_source': opera['source'],
                **char
            })

    df_chars = pd.DataFrame(all_characters)

    # 角色行当统计
    role_type_stats = df_chars['role_normalized'].value_counts().reset_index()
    role_type_stats.columns = ['行当类型', '出现次数']

    role_category_stats = df_chars['role_category'].value_counts().reset_index()
    role_category_stats.columns = ['行当大类', '出现次数']

    # 来源分布
    source_counts = Counter(o['source'] for o in opera_list)
    df_source = pd.DataFrame(source_counts.items(), columns=['来源', '剧本数量'])
    df_source = df_source.sort_values('剧本数量', ascending=False)

    # 目录分布
    dir_counts = Counter(o['directory'] for o in opera_list)
    df_dir = pd.DataFrame(dir_counts.items(), columns=['目录编号', '剧本数量'])
    df_dir = df_dir.sort_values('剧本数量', ascending=False)

    # 主题统计
    all_themes = []
    for o in opera_list:
        for t in o['themes']:
            all_themes.append(t)
    theme_counts = Counter(all_themes)
    df_themes = pd.DataFrame(theme_counts.items(), columns=['主题', '剧本数量'])
    df_themes = df_themes.sort_values('剧本数量', ascending=False)

    # 主题组合统计
    theme_combos = Counter()
    for o in opera_list:
        combo = ' + '.join(sorted(o['themes'])) if o['themes'] else '未分类'
        theme_combos[combo] += 1
    df_theme_combos = pd.DataFrame(theme_combos.items(), columns=['主题组合', '剧本数量'])
    df_theme_combos = df_theme_combos.sort_values('剧本数量', ascending=False)

    # 唱腔统计
    all_styles = Counter()
    for o in opera_list:
        for style, count in o['singing_styles'].items():
            all_styles[style] += count
    df_styles = pd.DataFrame(all_styles.items(), columns=['唱腔类型', '出现总次数'])
    df_styles = df_styles.sort_values('出现总次数', ascending=False)

    # 场次分布
    scene_dist = Counter(o['scene_count'] for o in opera_list)
    df_scenes = pd.DataFrame(scene_dist.items(), columns=['场次数', '剧本数量'])
    df_scenes = df_scenes.sort_values('场次数')

    # 角色数量分布
    char_dist = Counter(o['character_count'] for o in opera_list)
    df_char_dist = pd.DataFrame(char_dist.items(), columns=['角色数量', '剧本数量'])
    df_char_dist = df_char_dist.sort_values('角色数量')

    # 关键词汇总统计
    all_keywords = Counter()
    for o in opera_list:
        for kw in o['keywords']:
            all_keywords[kw['word']] += 1
    df_all_keywords = pd.DataFrame(all_keywords.most_common(100), columns=['关键词', '出现剧本数'])

    # 角色关系共现矩阵（基于同一剧本中出现）
    # 统计最常出现的角色名
    char_name_counts = Counter()
    for o in opera_list:
        names = [c['name'] for c in o['characters']]
        char_name_counts.update(names)
    top_char_names = [name for name, _ in char_name_counts.most_common(200)]

    # 行当共现矩阵
    role_category_cooccurrence = defaultdict(Counter)
    for o in opera_list:
        categories = list(set(c['role_category'] for c in o['characters']))
        for i, cat1 in enumerate(categories):
            for cat2 in categories[i:]:
                role_category_cooccurrence[cat1][cat2] += 1
                if cat1 != cat2:
                    role_category_cooccurrence[cat2][cat1] += 1

    return {
        'role_type_stats': role_type_stats,
        'role_category_stats': role_category_stats,
        'source_stats': df_source,
        'directory_stats': df_dir,
        'theme_stats': df_themes,
        'theme_combo_stats': df_theme_combos,
        'style_stats': df_styles,
        'scene_stats': df_scenes,
        'char_dist_stats': df_char_dist,
        'keyword_stats': df_all_keywords,
        'df_characters': df_chars,
        'top_char_names': top_char_names,
        'role_category_cooccurrence': dict(role_category_cooccurrence),
    }


def save_to_excel(opera_list, stats, filepath):
    """保存到Excel文件"""
    print(f"正在生成Excel文件: {filepath}")

    # 剧本总览
    overview_data = []
    for o in opera_list:
        overview_data.append({
            'ID': o['id'],
            '标题': o['title'],
            '别名': '、'.join(o['aliases']) if o['aliases'] else '',
            '来源': o['source'],
            '目录分类': o['directory'],
            '角色数量': o['character_count'],
            '场次数量': o['scene_count'],
            '剧本长度(字符)': o['body_length'],
            '主题标签': '、'.join(o['themes']),
            '唱腔类型': '、'.join(o['singing_styles'].keys()),
            '情节摘要': o['plot_summary'][:200] + '...' if len(o['plot_summary']) > 200 else o['plot_summary'],
        })
    df_overview = pd.DataFrame(overview_data)

    # 角色明细
    role_data = []
    for o in opera_list:
        for c in o['characters']:
            role_data.append({
                '剧本ID': o['id'],
                '剧本标题': o['title'],
                '角色名': c['name'],
                '行当原标注': c['role_type'],
                '行当标准化': c['role_normalized'],
                '行当大类': c['role_category'],
                '来源': o['source'],
                '目录': o['directory'],
            })
    df_roles = pd.DataFrame(role_data)

    # 主题-剧本关联
    theme_opera_data = []
    for o in opera_list:
        theme_opera_data.append({
            '剧本ID': o['id'],
            '标题': o['title'],
            '来源': o['source'],
            '目录': o['directory'],
            '主题': '、'.join(o['themes']),
            '场次数': o['scene_count'],
            '角色数': o['character_count'],
            '关键词': '、'.join(kw['word'] for kw in o['keywords'][:5]),
        })
    df_theme_opera = pd.DataFrame(theme_opera_data)

    # 写入Excel
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        df_overview.to_excel(writer, sheet_name='剧本总览', index=False)
        df_roles.to_excel(writer, sheet_name='角色行当明细', index=False)
        stats['role_type_stats'].to_excel(writer, sheet_name='行当类型统计', index=False)
        stats['role_category_stats'].to_excel(writer, sheet_name='行当大类统计', index=False)
        stats['source_stats'].to_excel(writer, sheet_name='来源分布', index=False)
        stats['directory_stats'].to_excel(writer, sheet_name='目录分类统计', index=False)
        stats['theme_stats'].to_excel(writer, sheet_name='主题统计', index=False)
        stats['theme_combo_stats'].to_excel(writer, sheet_name='主题组合统计', index=False)
        stats['style_stats'].to_excel(writer, sheet_name='唱腔统计', index=False)
        stats['scene_stats'].to_excel(writer, sheet_name='场次分布', index=False)
        stats['char_dist_stats'].to_excel(writer, sheet_name='角色数量分布', index=False)
        stats['keyword_stats'].to_excel(writer, sheet_name='关键词统计', index=False)
        df_theme_opera.to_excel(writer, sheet_name='主题-剧本关联', index=False)

        # 行当-目录交叉分析
        cross_dir_role = pd.crosstab(
            stats['df_characters']['opera_directory'],
            stats['df_characters']['role_category']
        )
        cross_dir_role.to_excel(writer, sheet_name='行当-目录交叉分析')

        # 行当-来源交叉分析
        cross_source_role = pd.crosstab(
            stats['df_characters']['opera_source'],
            stats['df_characters']['role_category']
        )
        cross_source_role.to_excel(writer, sheet_name='行当-来源交叉分析')

    print(f"Excel文件已保存: {filepath}")


# ============ 主函数 ============

def main():
    # 解析数据
    opera_list = parse_merged_file(INPUT_FILE)

    # 生成统计
    print("正在生成统计数据...")
    stats = generate_statistics(opera_list)

    # 保存JSON
    print(f"正在保存JSON文件: {OUTPUT_JSON}")
    output_data = {
        'total_operas': len(opera_list),
        'operas': opera_list,
    }
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"JSON文件已保存: {OUTPUT_JSON}")

    # 保存Excel
    save_to_excel(opera_list, stats, OUTPUT_XLSX)

    # 打印摘要
    print("\n" + "="*60)
    print("数据解析摘要")
    print("="*60)
    print(f"总剧本数: {len(opera_list)}")
    print(f"总角色记录数: {len(stats['df_characters'])}")
    print(f"独特行当类型数: {len(stats['role_type_stats'])}")
    print(f"来源数: {len(stats['source_stats'])}")
    print(f"目录分类数: {len(stats['directory_stats'])}")
    print(f"主题数: {len(stats['theme_stats'])}")
    print(f"\n行当大类分布:")
    for _, row in stats['role_category_stats'].head(10).iterrows():
        print(f"  {row['行当大类']}: {row['出现次数']} 次")
    print(f"\nTop 10 来源:")
    for _, row in stats['source_stats'].head(10).iterrows():
        print(f"  {row['来源']}: {row['剧本数量']} 个")
    print(f"\nTop 10 主题:")
    for _, row in stats['theme_stats'].head(10).iterrows():
        print(f"  {row['主题']}: {row['剧本数量']} 个")


if __name__ == '__main__':
    main()
