import requests
try:
    import cookielib
except:
    import http.cookiejar as cookielib
import re

session = requests.session()
session.cookies = cookielib.LWPCookieJar(filename='cookies.txt')
try:
    session.cookies.load(ignore_discard=True)
except:
    print('cookie未能加载')

agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
header = {
    'HOST': 'www.zhihu.com',
    'Referer':'https://www.zhihu.com',
    'User-Agent': agent
}

def get_xsrf():
    # 获取xsrf_code
    response = session.get('https://www.zhihu.com', headers=header)
    match_obj = re.match('.*name="_xsrf" value="(.*?)"',response)
    if match_obj:
        return match_obj.group(1)
    else:
        return ''

def is_login():
    # 通过个人中心页面返回状态码来判断是否为登录状态
    inbox_url = 'https://www.zhihu.com/inbox'
    response = session.get(inbox_url,headers=header,allow_redirects=False)
    if response.status_code != 200:
        return False
    else:
        return True


def get_captcha():
    import time
    t = str(int(time.time()*1000))
    captcha_url = "https://www.zhihu.com/captcha.gif?r={0}&type=login".format(t)
    t = session.get(captcha_url, headers=header)
    with open('captcha.jpg', 'wb') as f:
        f.write(t.content)
        f.close()
    from PIL import Image
    try:
        im = Image.open('captcha.jpg')
        im.show()
        im.close()
    except:
        pass

    captcha = input('请输入验证码：')
    return captcha


def zhihu_login(account,password):
    # 知乎登录
    if re.match("^1\d{10}", account):
        print("手机号登录")
        post_url = 'https:www.zhihu.com/login/phone_num'
        post_data = {
            '_crsf': get_xsrf(),
            'phone':account,
            'password':password,
            'captcha':get_captcha()
        }
    else:
        if '@' in account:
            print('邮箱方式登录')
            post_url = 'https:www.zhihu.com/login/email'
            post_data = {
                '_crsf': get_xsrf(),
                'phone': account,
                'password': password
            }
    response_text = session.post(post_url, data=post_data, headers=header)
    session.cookies.save()