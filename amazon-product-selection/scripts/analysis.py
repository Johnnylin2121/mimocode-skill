#!/usr/bin/env python3
"""
亚马逊选品分析脚本
基于卖家精灵导出的关键词数据，执行趋势、机会、利润、综合评分分析。

用法:
    python analysis.py report --input data.xlsx --output report.md
    python analysis.py preprocess --input data.xlsx
    python analysis.py report --input data.xlsx --output report.md --min-search 2000 --min-growth 0.15

依赖:
    pip install pandas openpyxl
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import re
import json


# ============================================================
# 默认参数
# ============================================================

DEFAULT_PARAMS = {
    # 趋势筛选
    "trend_min_search": 1000,
    "trend_min_growth": 0.10,

    # 机会筛选
    "opp_min_dsr": 10,
    "opp_max_reviews": 500,
    "opp_min_search": 500,
    "opp_min_price": 200,

    # 利润筛选
    "profit_min_search": 2000,
    "profit_price_min": 300,
    "profit_price_max": 3000,
    "profit_max_reviews": 800,
    "profit_max_products": 500,

    # 综合评分
    "score_min_search": 1000,
    "score_min_dsr": 5,
    "score_max_reviews": 1000,
    "score_min_price": 200,
    "weight_search": 0.30,
    "weight_dsr": 0.30,
    "weight_growth": 0.20,
    "weight_competition": 0.20,

    # 价格段
    "price_bins": [0, 500, 1000, 2000, 5000, float('inf')],
    "price_labels": ["<500", "500-1000", "1000-2000", "2000-5000", "5000+"],

    # 输出
    "top_n": 10,
    "output_dir": r"D:\OneDrive\ObsidianVault\工作\选品报告",
}

# 品类分类规则
CATEGORY_RULES = {
    "充电/电源类": ["cargador", "charger", "usb", "cable", "power bank", "batería", "bateria", "nexode", "carga"],
    "音频类": ["audífono", "audifono", "earbuds", "speaker", "sonido", "audio", "wf-", "sonos", "airpods"],
    "支架/配件类": ["soporte", "mount", "holder", "stand", "tripie", "trípode"],
    "显示/电视类": ["tv", "pantalla", "monitor", "led", "antena", "antenna", "hdmi"],
    "摄影类": ["cámara", "camara", "lente", "lens", "dji", "gopro", "insta"],
    "外设/游戏类": ["teclado", "keyboard", "mouse", "ratón", "gaming", "logitech", "rog"],
    "智能/网络类": ["wifi", "router", "bluetooth", "smart", "ring", "switch"],
    "散热/照明类": ["fan", "ventilador", "cooling", "foco", "lamp", "led strip"],
}


# ============================================================
# 核心函数
# ============================================================

def clean_price(series: pd.Series) -> pd.Series:
    """清洗价格列，去除货币符号和千位分隔符，转为数值"""
    def _clean(x):
        if pd.isna(x):
            return 0.0
        if isinstance(x, (int, float)):
            return float(x)
        x = str(x)
        x = re.sub(r'[A-Z]{2,3}\$', '', x)  # 去除 USD$, MX$ 等
        x = x.replace(',', '').strip()
        try:
            return float(x)
        except ValueError:
            return 0.0
    return series.apply(_clean)


def load_and_preprocess(filepath: str) -> pd.DataFrame:
    """加载并预处理 Excel 数据"""
    df = pd.read_excel(filepath)

    # 清洗价格列
    if '均价' in df.columns:
        df['均价_num'] = clean_price(df['均价'])
    else:
        df['均价_num'] = 0.0

    # 确保数值列类型正确
    numeric_cols = ['月搜索量', '商品数', '需供比', '评分数', '近3个月增长率', '搜索增长率']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    return df


def filter_trending(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """趋势市场筛选：高搜索量 + 高增长率"""
    mask = (
        (df['月搜索量'] > params['trend_min_search']) &
        (df['近3个月增长率'] > params['trend_min_growth'])
    )
    result = df[mask].copy()
    result = result.sort_values('近3个月增长率', ascending=False)
    return result


def filter_opportunity(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """机会市场筛选：高需供比 + 低评论"""
    mask = (
        (df['需供比'] > params['opp_min_dsr']) &
        (df['评分数'] < params['opp_max_reviews']) &
        (df['月搜索量'] > params['opp_min_search']) &
        (df['均价_num'] > params['opp_min_price'])
    )
    result = df[mask].copy()
    result = result.sort_values('需供比', ascending=False)
    return result


def filter_profitable(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """利润空间筛选：高搜索 + 合理价格 + 低竞争"""
    mask = (
        (df['月搜索量'] > params['profit_min_search']) &
        (df['均价_num'] > params['profit_price_min']) &
        (df['均价_num'] < params['profit_price_max']) &
        (df['评分数'] < params['profit_max_reviews']) &
        (df['商品数'] < params['profit_max_products'])
    )
    result = df[mask].copy()
    result = result.sort_values('月搜索量', ascending=False)
    return result


def calculate_composite_score(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """综合评分：多维加权排序"""
    mask = (
        (df['月搜索量'] > params['score_min_search']) &
        (df['需供比'] > params['score_min_dsr']) &
        (df['评分数'] < params['score_max_reviews']) &
        (df['均价_num'] > params['score_min_price'])
    )
    result = df[mask].copy()

    if len(result) == 0:
        return result

    # Min-Max 归一化
    for col in ['月搜索量', '需供比', '近3个月增长率']:
        min_v = result[col].min()
        max_v = result[col].max()
        result[col + '_norm'] = (result[col] - min_v) / (max_v - min_v) if max_v > min_v else 0

    # 评分数反向（越低越好）
    min_r = result['评分数'].min()
    max_r = result['评分数'].max()
    result['低竞争_norm'] = 1 - (result['评分数'] - min_r) / (max_r - min_r) if max_r > min_r else 0

    # 综合评分
    result['综合评分'] = (
        result['月搜索量_norm'] * params['weight_search'] +
        result['需供比_norm'] * params['weight_dsr'] +
        result['近3个月增长率_norm'] * params['weight_growth'] +
        result['低竞争_norm'] * params['weight_competition']
    )

    result = result.sort_values('综合评分', ascending=False)
    return result


def analyze_price_segments(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """价格段分析"""
    bins = params['price_bins']
    labels = params['price_labels']

    df_copy = df.copy()
    df_copy['价格段'] = pd.cut(df_copy['均价_num'], bins=bins, labels=labels, right=False)

    analysis = df_copy.groupby('价格段', observed=True).agg({
        '关键词': 'count',
        '月搜索量': 'mean',
        '需供比': 'mean',
        '评分数': 'mean',
        '近3个月增长率': 'mean'
    }).round(2)

    analysis.columns = ['关键词数', '平均搜索量', '平均需供比', '平均评分数', '平均增长率']
    return analysis


def classify_keywords(df: pd.DataFrame) -> pd.DataFrame:
    """按关键词翻译分类产品方向"""
    def _classify(kw):
        kw_lower = str(kw).lower()
        for cat, keywords in CATEGORY_RULES.items():
            if any(k in kw_lower for k in keywords):
                return cat
        return '其他电子类'

    df_copy = df.copy()
    df_copy['产品方向'] = df_copy['关键词翻译'].apply(_classify)
    return df_copy


def analyze_categories(df: pd.DataFrame) -> pd.DataFrame:
    """品类分析"""
    df_classified = classify_keywords(df)

    results = []
    for cat in df_classified['产品方向'].value_counts().index:
        cat_df = df_classified[df_classified['产品方向'] == cat]
        results.append({
            '品类': cat,
            '关键词数': len(cat_df),
            '平均搜索量': cat_df['月搜索量'].mean(),
            '平均需供比': cat_df['需供比'].mean(),
            '平均评分数': cat_df['评分数'].mean(),
            '平均价格': cat_df['均价_num'].mean(),
            '平均增长率': cat_df['近3个月增长率'].mean(),
        })

    return pd.DataFrame(results)


def get_top_n(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """取前 N 条"""
    return df.head(n)


# ============================================================
# 报告生成
# ============================================================

def generate_report(filepath: str, output_path: str, params: dict) -> str:
    """生成完整的选品分析报告"""
    # 加载数据
    df = load_and_preprocess(filepath)
    now = datetime.now().strftime('%Y-%m-%d')

    # 推断站点和类目
    filename = Path(filepath).stem
    site = "未知"
    category = "未知"
    if "MX" in filename.upper():
        site = "墨西哥"
    elif "US" in filename.upper():
        site = "美国"
    elif "JP" in filename.upper():
        site = "日本"

    # 执行分析
    trending = filter_trending(df, params)
    opportunity = filter_opportunity(df, params)
    profitable = filter_profitable(df, params)
    scored = calculate_composite_score(df, params)
    price_segments = analyze_price_segments(df, params)
    category_analysis = analyze_categories(df)

    n = params['top_n']

    # 构建报告
    report = f"""# {now} {site}站 {category} 选品分析

> 数据来源：卖家精灵关键词研究
> 分析日期：{now}
> 站点：{site}站 | 数据文件：{Path(filepath).name}

---

## 数据概览

| 指标 | 数值 |
|------|------|
| 总关键词数 | {len(df):,} 条 |
| 月搜索量范围 | {df['月搜索量'].min():,.0f} ~ {df['月搜索量'].max():,.0f} |
| 月搜索量中位数 | {df['月搜索量'].median():,.0f} |
| 价格范围 | {df['均价_num'].min():,.0f} ~ {df['均价_num'].max():,.0f} |
| 评分数范围 | {df['评分数'].min():,.0f} ~ {df['评分数'].max():,.0f} |

---

## 一、趋势市场（近3个月增长 > {params['trend_min_growth']:.0%}）

**{len(trending)} 个关键词**在持续增长

### Top {n} 趋势关键词

| 产品方向 | 月搜索量 | 3月增长率 | 需供比 | 均价 | 评论数 | 商品数 |
|---------|---------|----------|-------|------|-------|-------|
"""
    for _, row in get_top_n(trending, n).iterrows():
        report += f"| {row['关键词翻译']} | {row['月搜索量']:,.0f} | **+{row['近3个月增长率']:.0%}** | {row['需供比']:.1f} | {row['均价_num']:,.0f} | {row['评分数']:,.0f} | {row['商品数']:,.0f} |\n"

    report += f"""
---

## 二、机会市场（需供比 > {params['opp_min_dsr']} + 评论 < {params['opp_max_reviews']}）

**{len(opportunity)} 个关键词**供不应求

### Top {n} 蓝海机会

| 产品方向 | 月搜索量 | 需供比 | 评论数 | 均价 | 商品数 |
|---------|---------|-------|-------|------|-------|
"""
    for _, row in get_top_n(opportunity, n).iterrows():
        report += f"| {row['关键词翻译']} | {row['月搜索量']:,.0f} | **{row['需供比']:.0f}** | {row['评分数']:,.0f} | {row['均价_num']:,.0f} | {row['商品数']:,.0f} |\n"

    report += f"""
---

## 三、利润空间（搜索量 > {params['profit_min_search']:,} + 价格 {params['profit_price_min']}-{params['profit_price_max']}）

**{len(profitable)} 个关键词**有利润空间

### Top {n} 利润候选

| 产品方向 | 月搜索量 | 均价 | 评论数 | 需供比 | 3月增长率 |
|---------|---------|------|-------|-------|----------|
"""
    for _, row in get_top_n(profitable, n).iterrows():
        growth = row['近3个月增长率']
        growth_str = f"+{growth:.0%}" if growth > 0 else f"{growth:.0%}"
        report += f"| {row['关键词翻译']} | {row['月搜索量']:,.0f} | {row['均价_num']:,.0f} | {row['评分数']:,.0f} | {row['需供比']:.1f} | {growth_str} |\n"

    report += f"""
---

## 四、综合评分 Top {n}

综合考虑：搜索量({params['weight_search']:.0%}) + 需供比({params['weight_dsr']:.0%}) + 增长率({params['weight_growth']:.0%}) + 低竞争({params['weight_competition']:.0%})

| 排名 | 产品方向 | 综合评分 | 月搜索量 | 需供比 | 评论数 | 均价 |
|-----|---------|---------|---------|-------|-------|------|
"""
    for i, (_, row) in enumerate(get_top_n(scored, n).iterrows(), 1):
        report += f"| {i} | {row['关键词翻译']} | **{row['综合评分']:.3f}** | {row['月搜索量']:,.0f} | {row['需供比']:.1f} | {row['评分数']:,.0f} | {row['均价_num']:,.0f} |\n"

    report += f"""
---

## 五、价格段机会分析

| 价格段 | 关键词数 | 平均需供比 | 平均评论数 | 平均增长率 |
|--------|---------|-----------|-----------|-----------|
"""
    for idx, row in price_segments.iterrows():
        report += f"| {idx} | {row['关键词数']:.0f} | {row['平均需供比']:.2f} | {row['平均评分数']:,.0f} | {row['平均增长率']:.2%} |\n"

    report += f"""
---

## 六、品类趋势

| 品类 | 关键词数 | 平均需供比 | 平均增长率 | 平均价格 |
|-----|---------|-----------|-----------|---------|
"""
    for _, row in category_analysis.iterrows():
        report += f"| {row['品类']} | {row['关键词数']:.0f} | {row['平均需供比']:.2f} | {row['平均增长率']:.2%} | {row['平均价格']:,.0f} |\n"

    report += """
---

## 七、下一步行动建议

### 优先级 1：立即调研
"""
    # 从综合评分 Top 3 提取行动建议
    for _, row in get_top_n(scored, 3).iterrows():
        report += f"- **{row['关键词翻译']}** — 需供比 {row['需供比']:.0f}，评论仅 {row['评分数']:.0f}\n"

    report += """
### 优先级 2：重点跟踪
"""
    # 从品类分析中提取正增长品类
    growing_cats = category_analysis[category_analysis['平均增长率'] > 0]
    for _, row in growing_cats.head(3).iterrows():
        report += f"- **{row['品类']}** — 增长 {row['平均增长率']:.1%}，需供比 {row['平均需供比']:.1f}\n"

    report += """
### 待办事项
- [ ] 针对 Top 3 候选产品做深度竞品分析
- [ ] 测算各候选产品的利润模型
- [ ] 在 1688/阿里巴巴上调研供应链
- [ ] 制定小批量试单计划

---

## 附录：分析方法说明

### 筛选条件汇总
"""
    report += f"""
| 分析步骤 | 条件 |
|---------|------|
| 趋势筛选 | 月搜索量 > {params['trend_min_search']:,} + 近3月增长率 > {params['trend_min_growth']:.0%} |
| 机会筛选 | 需供比 > {params['opp_min_dsr']} + 评论 < {params['opp_max_reviews']} + 搜索量 > {params['opp_min_search']:,} |
| 利润筛选 | 搜索量 > {params['profit_min_search']:,} + 价格 {params['profit_price_min']}-{params['profit_price_max']} + 评论 < {params['profit_max_reviews']} |
| 综合评分 | 搜索量({params['weight_search']:.0%}) + 需供比({params['weight_dsr']:.0%}) + 增长率({params['weight_growth']:.0%}) + 低竞争({params['weight_competition']:.0%}) |
"""

    report += f"""
### 关键指标说明
- **需供比**：月搜索量 / 商品数，越高表示供不应求
- **SPR**：搜索购买比，反映搜索到购买的转化效率
- **综合评分**：多维加权排序，用于跨品类比较

---

*报告生成时间：{now}*
*分析工具：amazon-product-selection skill*
"""

    # 写入文件
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    return output_path


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='亚马逊选品分析工具')
    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # report 子命令
    report_parser = subparsers.add_parser('report', help='生成选品分析报告')
    report_parser.add_argument('--input', '-i', required=True, help='输入 Excel 文件路径')
    report_parser.add_argument('--output', '-o', help='输出报告路径（默认自动生成）')

    # 可选参数
    report_parser.add_argument('--min-search', type=int, help='最低搜索量')
    report_parser.add_argument('--min-growth', type=float, help='最低增长率')
    report_parser.add_argument('--min-dsr', type=float, help='最低需供比')
    report_parser.add_argument('--max-reviews', type=int, help='最高评论数')
    report_parser.add_argument('--price-min', type=float, help='最低价格')
    report_parser.add_argument('--price-max', type=float, help='最高价格')
    report_parser.add_argument('--weight-search', type=float, help='搜索量权重')
    report_parser.add_argument('--weight-dsr', type=float, help='需供比权重')
    report_parser.add_argument('--weight-growth', type=float, help='增长率权重')
    report_parser.add_argument('--weight-competition', type=float, help='低竞争权重')
    report_parser.add_argument('--top-n', type=int, help='每个维度展示前 N 个')
    report_parser.add_argument('--output-dir', help='报告输出目录')

    # preprocess 子命令
    preprocess_parser = subparsers.add_parser('preprocess', help='预处理数据')
    preprocess_parser.add_argument('--input', '-i', required=True, help='输入 Excel 文件路径')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 合并默认参数和用户参数
    params = DEFAULT_PARAMS.copy()
    if args.min_search is not None:
        params['trend_min_search'] = args.min_search
    if args.min_growth is not None:
        params['trend_min_growth'] = args.min_growth
    if args.min_dsr is not None:
        params['opp_min_dsr'] = args.min_dsr
    if args.max_reviews is not None:
        params['opp_max_reviews'] = args.max_reviews
    if args.price_min is not None:
        params['opp_min_price'] = args.price_min
        params['profit_price_min'] = args.price_min
        params['score_min_price'] = args.price_min
    if args.price_max is not None:
        params['profit_price_max'] = args.price_max
    if args.weight_search is not None:
        params['weight_search'] = args.weight_search
    if args.weight_dsr is not None:
        params['weight_dsr'] = args.weight_dsr
    if args.weight_growth is not None:
        params['weight_growth'] = args.weight_growth
    if args.weight_competition is not None:
        params['weight_competition'] = args.weight_competition
    if args.top_n is not None:
        params['top_n'] = args.top_n

    if args.command == 'preprocess':
        df = load_and_preprocess(args.input)
        print(f"预处理完成: {len(df)} 行数据")
        print(f"列: {list(df.columns)}")

    elif args.command == 'report':
        # 确定输出路径
        if args.output:
            output_path = args.output
        else:
            output_dir = args.output_dir or params['output_dir']
            now = datetime.now().strftime('%Y-%m-%d')
            filename = Path(args.input).stem
            output_path = str(Path(output_dir) / f"{now} {filename} 选品分析.md")

        print(f"开始分析: {args.input}")
        print(f"输出路径: {output_path}")

        result_path = generate_report(args.input, output_path, params)
        print(f"报告已生成: {result_path}")


if __name__ == '__main__':
    main()
