import os

root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))



def get_file_path(relative_path):
    # 获取文件的绝对路径
    return os.path.join(root_path, relative_path)


if __name__ == '__main__':
    print(root_path)
    print(get_file_path('aa/aa.py'))