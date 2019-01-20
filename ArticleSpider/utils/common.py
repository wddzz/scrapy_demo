import hashlib

# python3中默认所有的字符格式为Unicode
# python2 中存在关键字Unicode


def get_md5(url):
    if isinstance(url,str):
        url = url.encode('utf-8')
    m = hashlib.md5()
    m.update(url)
    return m.hexdigest()


if __name__ == '__main__':
    print(get_md5('https://www.baidu.com'))