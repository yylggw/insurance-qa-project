"""
将CSV数据转为txt文件，供知识图谱抽取脚本使用。
- medicine_full_data.csv 太大，只取前5条
- 其余mock CSV全量转换
- disease_full_data.csv 取前10条（PDF提取的数据）
"""
import pandas as pd
import os

BASE = os.path.dirname(os.path.abspath(__file__))  # __001__clawler

# 配置：(csv文件名, 目标文件夹名, 最大行数)
TASKS = [
    ("policy_doc.csv",        "政策文件",  None),
    ("reimburse_rule.csv",    "报销规则",  None),
    ("insure_type.csv",       "参保类型",  None),
    ("treat_item.csv",        "诊疗项目",  None),
    ("agency.csv",            "经办机构",  None),
    ("medicine_full_data.csv", "药品",     5),
    ("disease_full_data.csv",  "疾病",     10),
]


def row_to_text(row, columns):
    """将一行数据转为可读文本"""
    lines = []
    for col in columns:
        val = str(row[col]).strip() if pd.notna(row[col]) else ""
        if val and val != "nan":
            lines.append(f"{col}：{val}")
    return "\n".join(lines)


for csv_name, folder_name, max_rows in TASKS:
    csv_path = os.path.join(BASE, csv_name)
    if not os.path.exists(csv_path):
        print(f"⚠️ 跳过：{csv_name} 不存在")
        continue

    out_dir = os.path.join(BASE, folder_name)
    os.makedirs(out_dir, exist_ok=True)

    df = pd.read_csv(csv_path, encoding="utf-8-sig", nrows=max_rows)
    count = 0
    for idx, row in df.iterrows():
        text = row_to_text(row, df.columns)
        if not text.strip():
            continue
        file_path = os.path.join(out_dir, f"{idx+1:04d}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)
        count += 1

    print(f"✅ {csv_name} → {folder_name}/ ({count} 个txt文件)")

print("\n🎉 全部转换完成！")
