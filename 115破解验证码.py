import os
import time
import logging
from p115 import P115Client
from typing import Callable, cast
from collections import defaultdict
from concurrenttools import thread_pool_batch

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 从环境变量获取 cookie
cookie = os.getenv("P115_COOKIE")

if not cookie:
    raise ValueError("环境变量 P115_COOKIE 未设置或为空")

client = P115Client(cookie)  # 使用cookie创建115网盘客户端

def crack_captcha(
    client: str | P115Client, 
    sample_count: int = 16, 
    crack: None | Callable[[bytes], str] = None, 
) -> bool:
    global CAPTCHA_CRACK
    if crack is None:
        try:
            crack = CAPTCHA_CRACK
        except NameError:
            try:
                from ddddocr import DdddOcr
            except ImportError:
                from subprocess import run
                from sys import executable
                run([executable, "-m", "pip", "install", "-U", "ddddocr==1.4.11"], check=True)
                from ddddocr import DdddOcr
            crack = CAPTCHA_CRACK = cast(Callable[[bytes], str], DdddOcr(show_ad=False).classification)
    if isinstance(client, str):
        client = P115Client(client)
    while True:
        captcha = crack(client.captcha_code())
        if len(captcha) == 4 and all("\u4E00" <= char <= "\u9FFF" for char in captcha):
            break
    ls: list[defaultdict[str, int]] = [defaultdict(int) for _ in range(10)]
    def crack_single(i, submit):
        try:
            char = crack(client.captcha_single(i))
            if len(char) == 1 and "\u4E00" <= char <= "\u9FFF":
                ls[i][char] += 1
            else:
                submit(i)
        except:
            submit(i)
    thread_pool_batch(crack_single, (i for i in range(10) for _ in range(sample_count)))
    l: list[str] = [max(d, key=lambda k: d[k]) for d in ls]
    try:
        code = "".join(str(l.index(char)) for char in captcha)
    except ValueError:
        return False
    resp = client.captcha_verify(code)
    return resp["state"]

def check_and_crack_captcha():
    logging.info("开始检测和破解验证码")
    resp = client.download_url_web("a")
    if not resp["state"] and ('code' in resp and resp["code"] == 911):
        logging.info("出现验证码，尝试破解")
        while not crack_captcha(client):
            logging.error("破解失败，再次尝试")
        logging.info("破解成功")
    else:
        logging.info("没有检测到需要验证码")

# 程序开始时执行一次
logging.info("程序开始运行")
check_and_crack_captcha()

while True:
    # 每 5 分钟检测一次
    time.sleep(5 * 60)
    check_and_crack_captcha()
