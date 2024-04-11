import os
import datetime
import re
import glob
import sys
import csv


def check_existing_files():
    # 从环境变量获取配置信息
    tmp_path = os.environ.get('TMP_PATH', '/app/working_dir/tmp/')
    save_path = os.environ.get('SAVE_PATH', '/app/working_dir/save/source_file.txt')
    overwrite_flag = int(os.environ.get('OVERWRITE_FLAG', 0))

    # 检查临时文件路径是否存在
    if not os.path.exists(tmp_path):
        print("文件路径不存在，请检查后重新输入。")
        sys.exit()

    # 获取保存路径下所有的文本文件
    existing_files = glob.glob(os.path.join(save_path, '*.txt'))
    if existing_files:
        # 从文件名中提取日期，并找到最大的日期
        dates = [datetime.datetime.strptime(os.path.splitext(os.path.basename(f))[0].split('@')[0], "%m-%d-%Y") for f in existing_files]
        max_date = max(dates)
        print(f"保存目录下最大的时间戳为：{max_date.strftime('%m-%d-%Y')}")

        # 根据覆盖标志删除文件或设置忽略日期
        if overwrite_flag == 1:
            for f in existing_files:
                os.remove(f)
            ignore_date = datetime.datetime.min
        else:
            ignore_date = max_date - datetime.timedelta(days=2)
    else:
        ignore_date = datetime.datetime.min

    # 调用函数处理文本文件
    process_txt_file(ignore_date)


def process_txt_file(ignore_date):
    # 从环境变量获取配置信息
    tmp_path = os.environ.get('TMP_PATH', '/app/working_dir/tmp/')
    save_path = os.environ.get('SAVE_PATH', '/app/working_dir/save/source_file.txt')

    # 读取临时文件
    with open(save_path, 'r') as f:
        lines = f.read().split('\n')

    current_date = None
    current_file = None
    current_text = ""
    new_files = []

    # 遍历文件的每一行
    for line in lines:
        match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (.*)", line)
        if match:
            # 将之前累积的文本写入文件
            if current_file is not None and current_text:
                current_file.write(current_text)
                current_text = ""  # 清空当前文本以准备下一部分

            timestamp_str, text = match.groups()
            timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            # 对时间戳进行调整，如果小于3小时，则归到前一天
            if timestamp.hour < 3:
                timestamp -= datetime.timedelta(days=1)
            date_str = timestamp.strftime("%m-%d-%Y")
            
            # 如果日期变了且大于忽略日期，则准备新文件
            if date_str != current_date and datetime.datetime.strptime(date_str, "%m-%d-%Y") > ignore_date:
                if current_file is not None:
                    current_file.close()
                current_date = date_str
                source_file_name = os.path.splitext(os.path.basename(save_path))[0]
                new_file_name = f"{current_date}@{source_file_name}.txt"
                new_files.append(new_file_name)
                current_file = open(os.path.join(tmp_path, new_file_name), 'w')
            
            # 添加当前行到要写入的文本中，包括时间戳和文本
            current_text = f"{timestamp_str} {text}\n"
            if current_file is not None:
                current_file.write(current_text)
                current_text = ""  # 再次清空以准备下一行

        else:
            # 如果行不匹配，就累积到当前文本
            current_text += line + '\n'

    # 确保最后的内容也被写入文件
    if current_file is not None and current_text:
        current_file.write(current_text)
    if current_file is not None:
        current_file.close()

    if new_files:
        print(', '.join(new_files))

# 注意：这段代码需要定义ignore_date
# 例如，使用datetime.datetime.min作为ignore_date开始处理


def process_chat_log_to_csv():
    # 从环境变量获取配置信息
    input_dir_path = os.environ.get('TMP_PATH', '/app/working_dir/tmp/')
    output_dir_path = os.environ.get('CSV_OUTPUT_PATH', '/app/working_dir/csv/')

    # 确保输出目录存在
    if not os.path.exists(output_dir_path):
        os.makedirs(output_dir_path)

    # 遍历目录下的所有.txt文件
    for input_file_path in glob.glob(os.path.join(input_dir_path, '*.txt')):
        # 基于输入文件名创建输出文件名
        base_name = os.path.splitext(os.path.basename(input_file_path))[0]
        output_file_path = os.path.join(output_dir_path, f"{base_name}.csv")

        # 读取聊天日志文件
        with open(input_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        processed_lines = []
        current_speaker = None
        current_message = []
        timestamp = None  # 确保timestamp被初始化
        for line in lines:
            match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (.+)', line)
            if match:
                if current_speaker is not None:
                    processed_lines.append([timestamp, current_speaker, '\n'.join(current_message)])
                timestamp, content = match.groups()
                if '\n' in content:
                    current_speaker, message = content.split('\n', 1)
                    current_message = [message]
                else:
                    current_speaker = content
                    current_message = []
            elif line.strip() == '':
                if current_speaker is not None:
                    processed_lines.append([timestamp, current_speaker, '\n'.join(current_message)])
                    current_speaker = None
                    current_message = []
            else:
                current_message.append(line.strip())

        if current_speaker is not None:
            processed_lines.append([timestamp, current_speaker, '\n'.join(current_message)])

        # 写入CSV文件
        with open(output_file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['时间', '发言人', '内容'])
            writer.writerows(processed_lines)

        print(f"Processed {input_file_path} into {output_file_path}")


# 主程序逻辑
check_existing_files()
process_chat_log_to_csv()
