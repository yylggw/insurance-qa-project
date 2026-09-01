# E:\workspace\heima\insurance_qa_project\__001__clawler\extract_disease_from_pdf.py
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
疾病ICD-10医保2.0版PDF提取工具（仅抽取数据，不写入Neo4j）
功能：将疾病分类PDF解析为11列CSV文件
"""

import pdfplumber
import pandas as pd
import os
import time
import gc
from tqdm import tqdm
from pathlib import Path

# =========================================================
#  👇 1. 只需修改这里的 PDF 文件路径
# =========================================================
PDF_PATH = "../__000__data/疾病-ICD-10医保2.0版.pdf"
# =========================================================

# 输出配置
OUTPUT_CSV = "disease_full_data.csv"  # 最终输出的CSV文件名
TEMP_DIR = "./temp_disease_csv"  # 临时文件目录（与药品批次隔离）
BATCH_SIZE = 200  # 每200页存一次临时文件

# 运行模式配置
TEST_MODE = True  # True=只跑前10页测试；False=跑全量
TEST_PAGES = 10  # 测试页数（TEST_MODE=True时生效）
GENERATE_CYPHER = False  # 保持False，我们暂时只拿CSV数据
RESUME_MODE = True  # True=断点续传（跳过已处理的批次）；False=从头开始
GC_EVERY_BATCH = True  # True=每批次后强制释放内存
# =========================================================

# 疾病ICD-10的11列
COLUMNS = [
    "章",          # 1
    "章代码范围",   # 2
    "章的名称",     # 3
    "节代码范围",   # 4
    "节名称",       # 5
    "类目代码",     # 6
    "类目名称",     # 7
    "亚目代码",     # 8
    "亚目名称",     # 9
    "诊断代码",     # 10
    "诊断名称"      # 11
]


def ensure_temp_dir():
    """创建临时目录"""
    Path(TEMP_DIR).mkdir(parents=True, exist_ok=True)


def clean_row(row):
    """清洗单行数据：去空格、跳过表头、补齐列数"""
    if not row:
        return None

    # 补齐列数（防止缺列报错）
    if len(row) < len(COLUMNS):
        row = list(row) + [""] * (len(COLUMNS) - len(row))

    # 去除首尾空格
    cleaned = [str(cell).strip() if cell else "" for cell in row[:len(COLUMNS)]]

    # 跳过表头行（第一列包含"章"或"章节"等关键字）
    first_cell = cleaned[0]
    if first_cell and ("章" in first_cell and "代码" in first_cell):
        return None
    if first_cell and ("类目代码" in first_cell or "诊断代码" in first_cell):
        return None

    # 跳过全空行
    if all(c == "" for c in cleaned):
        return None

    return cleaned


def save_batch(data, batch_num):
    """保存一批临时CSV"""
    if not data:
        return
    df = pd.DataFrame(data, columns=COLUMNS)
    temp_file = os.path.join(TEMP_DIR, f"batch_{batch_num:04d}.csv")
    df.to_csv(temp_file, index=False, encoding='utf-8-sig')
    print(f"  ✅ 已保存临时批次 {batch_num} ({len(data)} 条)")


def get_last_completed_batch():
    """获取已完成的最后一个批次号，用于断点续传"""
    if not RESUME_MODE:
        return 0
    if not os.path.exists(TEMP_DIR):
        return 0
    batch_files = [f for f in os.listdir(TEMP_DIR) if f.startswith("batch_") and f.endswith(".csv")]
    if not batch_files:
        return 0
    batch_nums = [int(f.replace("batch_", "").replace(".csv", "")) for f in batch_files]
    return max(batch_nums) if batch_nums else 0


def merge_temp_files(output_path):
    """合并所有临时CSV为最终文件"""
    all_files = sorted([f for f in os.listdir(TEMP_DIR) if f.startswith("batch_") and f.endswith(".csv")])
    if not all_files:
        print("⚠️ 没有找到临时文件，请先运行提取脚本")
        return None, 0

    print(f"🔄 正在合并 {len(all_files)} 个临时文件...")
    dfs = []
    for f in tqdm(all_files, desc="合并进度"):
        df = pd.read_csv(os.path.join(TEMP_DIR, f), encoding='utf-8-sig')
        dfs.append(df)

    final_df = pd.concat(dfs, ignore_index=True)
    final_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"🎉 合并完成！共 {len(final_df)} 条数据，已保存至 {output_path}")
    return output_path, len(final_df)


def extract_pdf():
    """核心提取函数"""
    if not os.path.exists(PDF_PATH):
        print(f"❌ 错误：找不到PDF文件 {PDF_PATH}")
        print("请修改脚本顶部的 PDF_PATH 变量")
        return None

    print(f"📄 正在打开: {PDF_PATH}")
    file_size = os.path.getsize(PDF_PATH) / (1024 * 1024)
    print(f"📊 文件大小: {file_size:.2f} MB")

    # 断点续传：检查已完成的批次
    last_batch = get_last_completed_batch()
    start_page = last_batch * BATCH_SIZE if last_batch > 0 else 0
    batch_num = last_batch + 1
    total_rows = 0

    if start_page > 0:
        print(f"🔄 【断点续传】从第 {start_page + 1} 页开始（已完成 {last_batch} 个批次）")

    with pdfplumber.open(PDF_PATH) as pdf:
        total_pages = len(pdf.pages)
        print(f"📑 总页数: {total_pages}")

        if TEST_MODE:
            max_pages = min(TEST_PAGES, total_pages)
            print(f"🧪 【测试模式】只解析前 {max_pages} 页")
        else:
            max_pages = total_pages
            print(f"🚀 【全量模式】解析全部 {max_pages} 页")

        pbar = tqdm(total=max_pages - start_page, desc="解析进度", unit="页")

        all_data = []
        for page_num in range(start_page, max_pages):
            try:
                page = pdf.pages[page_num]
                table = page.extract_table()

                if table:
                    for row in table:
                        cleaned = clean_row(row)
                        if cleaned:
                            all_data.append(cleaned)
                            total_rows += 1

                    pbar.set_postfix({"累计": total_rows})
                else:
                    pbar.set_postfix({"累计": total_rows, "提示": "无表格"})

                # 每N页存一次临时文件（防止内存溢出）
                if (page_num + 1) % BATCH_SIZE == 0 and all_data:
                    save_batch(all_data, batch_num)
                    all_data = []
                    batch_num += 1

                    # 强制释放内存
                    if GC_EVERY_BATCH:
                        gc.collect()

                pbar.update(1)

            except Exception as e:
                print(f"\n⚠️ 第 {page_num + 1} 页出错: {e}，继续下一页...")
                pbar.update(1)
                continue

        pbar.close()

        # 保存最后残留的数据
        if all_data:
            save_batch(all_data, batch_num)

        print(f"\n✅ 提取阶段完成！共处理 {max_pages - start_page} 页，提取 {total_rows} 行原始数据")
        return total_rows


def main():
    print("=" * 60)
    print("      基政易答 · 疾病ICD-10 PDF数据抽取工具（只抽不写）")
    print("=" * 60)

    ensure_temp_dir()
    print(f"\n⏰ 开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    start_time = time.time()

    # 第一步：抽取PDF数据
    total_rows = extract_pdf()

    elapsed = time.time() - start_time
    print(f"\n⏱️  抽取耗时: {elapsed:.2f} 秒 ({elapsed / 60:.2f} 分钟)")

    if total_rows is None or total_rows == 0:
        print("⚠️ 未提取到任何数据，请检查PDF文件格式是否正确")
        return

    # 第二步：合并所有临时CSV
    print("\n" + "=" * 60)
    print("         合并临时文件（生成最终CSV）")
    print("=" * 60)
    final_csv, final_count = merge_temp_files(OUTPUT_CSV)

    if final_csv is not None:
        print(f"\n🎉 大功告成！数据已保存至: {final_csv}")
        print(f"📊 总数据量: {final_count} 条")
        print("\n💡 下一步建议：")
        print("   1. 用Excel打开CSV，检查前几行数据是否正确对齐11列")
        print("   2. 重点关注：合并单元格是否被正确拆分、层级字段是否正确填充")
        print("   3. 确认无误后，告诉我数据质量，我帮你调整或生成入库脚本")

    print("\n" + "=" * 60)
    print("【注意】本次运行未生成Cypher脚本，仅输出CSV文件。")
    print(f"临时文件位于 {TEMP_DIR}，确认CSV无误后可手动删除。")
    print("=" * 60)


if __name__ == "__main__":
    main()