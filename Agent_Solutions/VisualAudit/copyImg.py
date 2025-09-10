import os
import re
import shutil

# 定义文件夹路径
report_dir = "report"
report_img_dir = "reportImg"
output_base_dir = "input"  # 输出文件夹根目录

# 如果输出目录不存在，则创建
if not os.path.exists(output_base_dir):
    os.makedirs(output_base_dir)

# 遍历 report 文件夹中的所有 PDF 文件
for report_file in os.listdir(report_dir):
    if not report_file.lower().endswith('.pdf'):
        continue

    # 示例文件名：报告详情_1010001_1010001-北京-丰台万达店_【门店】打烊检查表_2025-03-24.pdf
    # 提取报告文件中的门店编码
    match_report = re.search(r'报告详情_([0-9]+)_', report_file)
    if not match_report:
        print(f"无法从 {report_file} 中提取门店编码，跳过")
        continue

    store_code = match_report.group(1)
    print(f"提取到报告文件 {report_file} 的门店编码：{store_code}")

    # 在 reportImg 文件夹中查找所有匹配该编码的图片
    matching_imgs = []
    store_name = None

    for img_file in os.listdir(report_img_dir):
        # 只处理图片文件（假设扩展名为 jpeg、jpg、png）
        if not img_file.lower().endswith(('.jpeg', '.jpg', '.png')):
            continue

        # 判断图片文件名是否以门店编码开头
        if not img_file.startswith(store_code):
            continue

        matching_imgs.append(img_file)
        # 只从第一个匹配的图片中提取门店名称
        if store_name is None:
            # 示例图片格式：1020017-广州-白云机场T2安检内店--牟秋月--2025-03-24(1).jpeg
            match_img = re.search(r'^([0-9]+)-(.+?)--', img_file)
            if match_img:
                store_name = match_img.group(2)

    # 如果找到了匹配图片，则复制报告和所有图片到新的文件夹中
    if matching_imgs:
        # 构造新文件夹名称（如果未提取到门店名称，则仅用门店编码）
        new_folder_name = f"{store_code}-{store_name}" if store_name else store_code
        new_folder_path = os.path.join(output_base_dir, new_folder_name)
        if not os.path.exists(new_folder_path):
            os.makedirs(new_folder_path)
        print(f"创建文件夹：{new_folder_name}")

        # 复制报告PDF文件
        src_pdf_path = os.path.join(report_dir, report_file)
        dst_pdf_path = os.path.join(new_folder_path, report_file)
        shutil.copy2(src_pdf_path, dst_pdf_path)
        print(f"复制报告文件：{report_file} 到 {new_folder_name}")

        # 复制所有匹配的图片文件
        for img in matching_imgs:
            src_img_path = os.path.join(report_img_dir, img)
            dst_img_path = os.path.join(new_folder_path, img)
            shutil.copy2(src_img_path, dst_img_path)
            print(f"复制图片文件：{img} 到 {new_folder_name}")
    else:
        print(f"没有找到与编码 {store_code} 匹配的图片，跳过 {report_file}")