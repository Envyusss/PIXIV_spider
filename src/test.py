import requests
import re
import pprint

head = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:52.0) Gecko/20100101 Firefox/52.0'
    }
session = requests.session()

    # 首先进入登录页获取post_key，我用的是正则表达式   
response = session.get('https://accounts.pixiv.net/login?lang=zh')
post_key = re.findall('<input type="hidden" name="post_key" value=".*?">',
                          response.text)[0]
post_key = re.findall('value=".*?"', post_key)[0]
post_key = re.sub('value="', '', post_key)
post_key = re.sub('"', '', post_key)

    # 将传入的参数用字典的形式表示出来，return_to可以去掉
data = {
    'pixiv_id': '783461007@qq.com',
    'password': 'zzc991031',
    'return_to': 'https://www.pixiv.net/',
    'post_key': post_key,
    }
    # 将data post给登录页面，完成登录
rep=session.post("https://accounts.pixiv.net/login?lang=zh", data=data, headers=head)
pprint.pprint(rep.cookies)
# with open('1.text', 'wb') as f:
#     f.write(rep.cookies)
# f.close()