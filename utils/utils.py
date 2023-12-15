import random
import string


# 定义一个函数，用于生成指定长度的随机字符串
def random_string(length):
    # 定义一个字符串，包含字母和数字
    characters = string.ascii_letters + string.digits
    # 返回指定长度的随机字符串
    return ''.join(random.choice(characters) for _ in range(length))
