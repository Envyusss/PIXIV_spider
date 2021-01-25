import re, requests, time
from urllib.parse import urlencode
import pprint
import json
from pathlib import Path
import os
'''
            主要的函数都在这个文件内
'''
# 公用头文件
head = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'
}
def set_leaderboard(content: str, mode: str, R18: bool, date: str) -> list:
    """
    选择进入的排行榜
    不是所有分区都有所有的排行榜模式，如动图区只有今日和本周两个模式
    建议去P站确定各参数后再调用
    :param content: 排行榜的分区，包括综合、插画、动图、漫画
    :param mode: 排行榜的模式，包括今日、本周、新人、受男性欢迎、受女性欢迎
    :param R18: 是否进入R18模式
    :param date: 排行榜具体时间
    :return: 排行榜参数列表，可用在其他函数中
    """

    print("已设置起始榜单为" + date[:4] + "年" + date[4:6] + "月" + date[6:8] + "日" + content + "区" + mode + "榜")

    if content == '综合':
        content = ''
    elif content == '插画':
        content = 'illust'
    elif content == '动图':
        content = 'ugoira'
    elif content == "漫画":
        content = 'manga'

    if mode == '今日':
        mode = 'daily'
    elif mode == '本周':
        mode = 'weekly'
    elif mode == '本月':
        mode = 'monthly'
    elif mode == '新人':
        mode = 'rookie'
    elif mode == '受男性欢迎':
        mode = 'male'
    elif mode == '受女性欢迎':
        mode = 'female'

    if R18:
        mode = mode + '_r18'
    else:
        mode = mode + ''

    return [content, mode, date]


def __login(username: str, password: str) -> requests.sessions.Session:
    """
    登陆函数
    :param username: 用户名
    :param password: 密码
    :return: 该用户名的会话(session)
    """
    # 模拟一下浏览器
    head = {
        "cookie": "__cfduid=d901b3358663ab12435e404af45609f6f1611053156; PHPSESSID=tg20j2kla0gunm9hegg12r5sta032hlq; p_ab_id=4; p_ab_id_2=4; p_ab_d_id=466379043; _ga=GA1.2.64561347.1611053157; _gid=GA1.2.289941561.1611053157; _gat=1; _ga=GA1.3.64561347.1611053157; _gid=GA1.3.289941561.1611053157; _gat_UA-76252338-4=1; __cf_bm=8f26c498679077bacdc4d642af7918c73407f90f-1611053157-1800-AWW9YjhaDiLC4q+faefoEFR8unzTjiTD4WjYS8Zxp7yVDzTWPEJRHlR9tMJP80SL76q/7JE712xGqqijmDntE5N72Z0l4PgfpnMbWI+clyeoCmFWBYOCudguWyFJ6OHzWGNueJZ31oGOxrpq31pD3xRMXMrCCwnEIZxGsXVokPWU",
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'
    }

    # 用requests的session模块记录登录的cookie

    session = requests.session()

    # 首先进入登录页获取post_key，我用的是正则表达式
    # try:
    #     response = session.get('https://accounts.pixiv.net/login?lang=zh')
    # except:
        
    response = session.get('https://accounts.pixiv.net/login?',headers=head,timeout=60)
    post_key = re.findall('<input type="hidden" name="post_key" value=".*?">',
                          response.text)[0]
    post_key = re.findall('value=".*?"', post_key)[0]
    post_key = re.sub('value="', '', post_key)
    post_key = re.sub('"', '', post_key)

    # # 将传入的参数用字典的形式表示出来，return_to可以去掉
    data = {
        'pixiv_id': username,
        'password': password,
        'return_to': 'https://www.pixiv.net/',
        'post_key': post_key,
    }

    # # 将data post给登录页面，完成登录
    session.post("https://accounts.pixiv.net/login?", data=data, headers=head,timeout=60)
    return session



def load_leaderboard(username: str, password: str, set_leaderboard: list) -> list:
    """
    进入榜单
    :param username: 用户名
    :param password: 密码
    :param set_leaderboard: 榜单参数
    :return: 带有图片url等信息的字典组成的列表
    """
    # 使用前确保set_leaderboard()函数已调用，并将其返回的参数列表传入该函数
    response_list = []

    # 先登录用户
    session = __login(username, password)

    # 初始化爬取的页数以及所需传入的参数
    p = 1
    data = {
        'mode': set_leaderboard[1],  # 这些是 set_leaderboard()函数返回的参数
        'content': set_leaderboard[0],
        'date': set_leaderboard[2],
        'p': p,
        'format': 'json'
    }
    print("正在加载" + "https://www.pixiv.net/ranking.php?" + urlencode(data))

    # 如果date是今天，需要去除date项;如果content为综合，需要去除content项。
    # 这是因为P站排行榜的今日榜不需要传入'date'，而综合区不需要传入'content'
    if set_leaderboard[2] == time.strftime("%Y%m%d"):
        data.pop('date')
    if set_leaderboard[0] == '':
        data.pop('content')

    # 开启循环进行翻页
    while True:

        # 翻页并更新data中的'p'参数
        data['p'] = p
        p = p + 1

        # 使用urlencode()函数将data传入url，获取目标文件
        url = "https://www.pixiv.net/ranking.php?" + urlencode(data)
        response = session.get(url)

        # 处理的到的文件并转为字典形式
        # 不加以下这些会报错，似乎是因为eval()不能处理布尔型数据
        global false, null, true
        false = 'False'
        null = 'None'
        true = 'True'
        try:
            response = eval(response.content)['contents']
        except KeyError:
            break
        response_list = response_list + response

    # 返回一个列表，列表元素为字典形式，包括了图片的各个信息
    return response_list


def leaderboard_turn_next_page(set_leaderboard: list) -> list:
    """
    排行榜前一天
    :param set_leaderboard: 排行榜参数列表，来自于set_leaderboard()函数
    :return: 前一天排行榜的参数列表
    """
    date = int(set_leaderboard[2])
    date = date - 1
    set_leaderboard[2] = date
    return set_leaderboard  # 返的是一个列表


def leaderboard_turn_previous_page(set_leaderboard: list) -> list:
    """
    排行榜后一天
    :param set_leaderboard: 排行榜参数列表，来自于set_leaderboard()函数
    :return: 后一天排行榜的参数列表
    """
    date = int(set_leaderboard[2])
    date = date + 1
    set_leaderboard[2] = date
    return set_leaderboard


def get_author_id(response_list: list) -> list:
    """
    得到作者的ID
    :param response_list: 响应列表，来自于load_leaderboard()函数
    :return: 排行榜内作者ID组成的列表
    """
    author_id_list = []
    for element in response_list:
        author_id_list.append(str(element['user_id']))
    return author_id_list


def get_author_img_dic(author_id: str, username: str, password: str) -> dict:
    """
    获取作者的全部作品字典
    :param author_id: 作者ID
    :param username: 用户名
    :param password: 密码
    :return: 作者的全部作品字典
    """
    h={"cookie": "first_visit_datetime_pc=2020-01-14+18%3A07%3A19; p_ab_id=7; p_ab_id_2=0; p_ab_d_id=1075190726; yuid_b=EZeSQAI; _ga=GA1.2.1520641699.1578992842; a_type=0; b_type=1; login_ever=yes; ki_r=; __utmv=235335808.|2=login%20ever=yes=1^3=plan=normal=1^5=gender=male=1^6=user_id=15460916=1^9=p_ab_id=7=1^10=p_ab_id_2=0=1^11=lang=zh=1; _fbp=fb.1.1586843733592.1271148926; __gads=ID=edd0d47cfab0536d:T=1593573721:S=ALNI_Ma2FXCg_38SGDecQJSjsNOdF1-6NA; __utmz=235335808.1597315982.68.2.utmcsr=blog.csdn.net|utmccn=(referral)|utmcmd=referral|utmcct=/h_wulingfei/article/details/62041986; PHPSESSID=15460916_F6oNnaimIcfDiX9fygpoLnOnWNNztk7i; privacy_policy_agreement=2; c_type=50; ki_s=204981%3A0.0.0.0.0%3B208879%3A0.0.0.0.0%3B209879%3A0.0.0.0.0%3B210803%3A0.0.0.0.0%3B211476%3A0.0.0.0.0%3B212334%3A0.0.0.0.2%3B212529%3A0.0.0.0.0; __cfduid=deba55740bfd18124ce9170dadacfb6871609226785; tag_view_ranking=RTJMXD26Ak~Lt-oEicbBr~jH0uD88V6F~uusOs0ipBx~LJo91uBPz4~jhuUT0OJva~eVxus64GZU~pzzjRSV6ZO~tIqkVZurKP~azESOjmQSV~Bd2L9ZBE8q~EUwzYuPRbU~cbmDKjZf9z~LtW-gO6CmS~zyKU3Q5L4C~tgP8r-gOe_~KN7uxuR89w~K8esoIs2eW~RcahSSzeRf~HY55MqmzzQ~_pwIgrV8TB~BU9SQkS-zU~y8GNntYHsi~X_1kwTzaXt~XDEWeW9f9i~PwDMGzD6xn~bXMh6mBhl8~l07o0f32_O~Ie2c51_4Sp~-sp-9oh8uv~pnCQRVigpy~G_f4j5NH8i~0YMUbkKItS~YRDwjaiLZn~tg4cf2wCF6~D0nMcn6oGk~CrFcrMFJzz~9ODMAZ0ebV~_giyO1uU9O~Hry6GxyqEm~jIqY0gKyUp~MSNRmMUDgC~t6fkfIQnjP~PTyxATIsK0~OT4SuGenFI~xZ6jtQjaj9~aKhT3n4RHZ~6rYZ-6JKHq~4TDL3X7bV9~ay54Q_G6oX~iFcW6hPGPU~FH69TLSzdM~-StjcwdYwv~gVfGX_rH_Y~3W4zqr4Xlx~fIMPtFR8GH~h9fEA3tOFb~RNN9CgGExV~pa4LoD4xuT~DkrVZhj3Z3~9V46Zz_N_N~GmCzj7c06U~t2ErccCFR9~kP7msdIeEU~1LN8nwTqf_~eYc98qhabe~SoxapNkN85~w6DOLSTOSN~7Y-OaPrqAv~qpeZSmEVVP~SqVgDNdq49~1bmFwrp_zN~ITqZ5UzdOC~qtVr8SCFs5~UVIPuHXf_y~r4ORkXpr9J~hTpAINkNsN~HLWLeyYOUF~kGYw4gQ11Z~lQdVtncC-e~ePN3h1AXKX~GFExx0uFgX~FtrTKRpgAM~zOv44MN0Wo~x_jB0UM4fe~tqREfrJhLi~KOnmT1ndWG~0q6DGkZagq~4rDNkkAuj_~EGefOqA6KB~KvAGITxIxH~QaiOjmwQnI~OYl5wlor4w~bRA1dBP_6A~jFLb4HjoWf~lUM3Y7NGaw~oZGTLJGlDy~nQRrj5c6w_~cFYMvUloX0~fg8EOt4owo; __utmc=235335808; ki_t=1578993030666%3B1611050926675%3B1611050930360%3B67%3B269; __utma=235335808.1520641699.1578992842.1611050898.1611050927.137; __cf_bm=a4724a4206d113a52e42a6fa6e1727fb0f138413-1611060306-1800-AYd0Jvzh7d8W8Aexqqu+tBG6YUvOk/ESosn3ZClAm+9sn8ckPhN6C7O/OxWRldhvzUftWj0IgjAIv3jdPVvPiCc=",
       'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'}
    # 登录用户
    session = __login(username, password)
    response = session.get('https://www.pixiv.net/ajax/user/' + author_id + '/profile/all',headers=h,timeout=60)
    # data=json.loads(response.text)
    # pprint.pprint(data['body']['illusts'])
    # 不加以下这些会报错，似乎是因为eval()不能处理布尔型数据
    global false, null, true
    false = 'False'
    null = 'None'
    true = 'True'
    author_img_dic = eval(response.content)['body']
    return author_img_dic


def get_author_illusts(author_img_dic: dict) -> list:
    """

    """
    
    author_illusts_dic = author_img_dic['illusts']
    illusts_list = [key for key, value in author_illusts_dic.items()]   
    return illusts_list


def get_author_manga(author_img_dic: dict) -> list:
    """
    获得作者的漫画ID
    :param author_img_dic: 作者的全部作品字典，来自于get_author_img_dic()函数
    :return: 作者的漫画ID列表
    """
    author_manga_dic = author_img_dic['manga']
    manga_list = [key for key, value in author_manga_dic.items()]
    return manga_list


def get_author_mangaSeries(author_img_dic: dict) -> list:
    """
    获取作者的漫画系列ID
    :param author_img_dic: 作者的全部作品字典，来自于get_author_img_dic()函数
    :return: 作者的漫画系列ID列表
    """
    author_mangaSeries_dic = author_img_dic['mangaSeries']
    mangaSeries_list = [key for key, value in author_mangaSeries_dic.items()]
    return mangaSeries_list


def get_img_dic(img_id: str, username: str, password: str) -> dict:  # 传入图片ID，返回该图片ID下的信息，具体信息见注释
    """
    获得某个图片ID下的信息，具体信息见注释
    :param img_id: 图片ID
    :param username: 用户名
    :param password: 密码
    :return: 图片ID下的信息字典
    """
    '''
    图片ID下的信息字典
    img_dic = {
        'illustID' : 插画ID
        'illustTitle' : 插画标题
        'illustDescription' : 插画简介
        'createDate' : 插画创建时间
        'uploadDate' : 插画更新时间
        'tags' : 插画tag,值为列表
        'authorID' : 作者ID
        'authorName' : 作者昵称
        'imgUrl' : 插画原始大小url,值为列表
    }
    '''
    head = {
        "cookie": "__cfduid=ddd127e68a7a92eaf405e03961116175c1609857488; PHPSESSID=76e3uuiihjj2svft7k1b5ijp0bkrpe8t; p_ab_id=9; p_ab_id_2=5; p_ab_d_id=212263852; _ga=GA1.2.840476069.1609857489; _gid=GA1.2.1071985007.1609857489; __cf_bm=98555ab66bae3a1ad4187ba0554c97989902a42b-1609857489-1800-Ab0JaUQuHjcr4ogYHQIlU8gtgkn641F4PzbLdz9w99gt9xRv821hSPIxxiVjn2A2xpOkv+HK4fcRhgIyOPQf8fD5djalLLmhMqTyKt+pJmkN2VxEFBebGfcTaSTqA40JRyNtapk3QotMb1se5zyw540Xy2XReudFhrvScmJIhYLH",
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'
    }
    img_dic = {}
    # 登录用户
    session = __login(username, password)

    # 获取第一个文件的信息，把除了图片url以外的东西先拿到
    url_1 = 'https://www.pixiv.net/ajax/illust/' + img_id
    response_1 = session.get(url_1,headers=head,timeout=60)
    # 不加以下这些会报错，似乎是因为eval()不能处理布尔型数据
    global false, null, true
    false = 'False'
    null = 'None'
    true = 'True'
    response_1 = eval(response_1.content)['body']
    img_dic['illustID'] = response_1['illustId']  # 图片ID
    img_dic['illustTitle'] = response_1['illustTitle']  # 图片标题
    img_dic['illustDescription'] = response_1['illustComment']  # 图片简介
    img_dic['createDate'] = response_1['createDate']  # 创建时间
    img_dic['uploadDate'] = response_1['uploadDate']  # 更新时间
    img_dic['tags'] = []  # 因为有多个tag，所以'tags'的值用列表形式保存
    for tag in response_1['tags']['tags']:
        img_dic['tags'].append(tag['tag'])
    img_dic['authorID'] = response_1['tags']['tags'][0]['userId']
    img_dic['authorName'] = response_1['tags']['tags'][0]['userName']

    # 获取第二个文件的信息，把图片url拿到
    url_2 = 'https://www.pixiv.net/ajax/illust/' + img_id + '/pages'
    response_2 = session.get(url_2,headers=head,timeout=60)
    response_2 = eval(response_2.content)['body']
    img_dic['imgUrl'] = []  # 因为存在好几个插画在同一页面的情况，所以'imgUrl'的值用列表形式保存
    for img_url in response_2:
        img_dic['imgUrl'].append(img_url['urls']['original'].replace('\\', ''))

    return img_dic


def get_img_imformation(img_dic: dict) -> dict:
    """
    提取下载图片所需的信息
    :param img_dic:
    :return: 图片ID下的信息字典，来自get_img_dic()函数
    """
    img_imformation = {}
    img_imformation['img_url'] = img_dic['imgUrl']
    img_imformation['img_id'] = img_dic['illustID']
    img_imformation['img_title'] = img_dic['illustTitle']
    return img_imformation


# 这些是未完成函数，大概是通过搜索获取图片信息的函数
# def set_search(word, s_mode, mode, order, scd, ecd, type, p):
#     data = {
#         'word': word,
#         's_mode': s_mode,
#         'mode': mode,
#         'order': order,
#         'scd': scd,
#         'ecd': ecd,
#         'type': type,
#         'p': p
#     }
#
#     if scd == '' or ecd == '':
#         data.pop('scd')
#         data.pop('ecd')
#     if type == '':
#         data.pop('type')
#
#     return data
#
#
# def load_search(username, password):
#     session = __login(username, password)
#     a = session.get('https://www.pixiv.net/search.php?s_mode=s_tag&word=%E7%B4%94%E6%84%9B%E3%82%B3%E3%83%B3%E3%83%93')
#     print(a.content)

def load_imgid(img_id:str):
    with open('loading.txt','a+',encoding='utf-8')as file:
        file.write(img_id+'\n')
        


def download(img_imformation: dict, address: str,authorName: str,num: int):  # 下载图片，以图片标题命名
    """
    下载图片，以图片标题命名
    :param img_imformation: 图片下载所需信息，来自get_img_imformation()函数
    :param address: 图片保存地址
    """
    n = 0
    head = {
        # "cookie": "first_visit_datetime_pc=2020-01-14+18%3A07%3A19; p_ab_id=7; p_ab_id_2=0; p_ab_d_id=1075190726; yuid_b=EZeSQAI; _ga=GA1.2.1520641699.1578992842; c_type=49; a_type=0; b_type=1; login_ever=yes; ki_r=; module_orders_mypage=%5B%7B%22name%22%3A%22sketch_live%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22tag_follow%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22following_new_illusts%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22recommended_illusts%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22everyone_new_illusts%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22mypixiv_new_illusts%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22spotlight%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22fanbox%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22featured_tags%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22contests%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22user_events%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22sensei_courses%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22booth_follow_items%22%2C%22visible%22%3Atrue%7D%5D; __utmv=235335808.|2=login%20ever=yes=1^3=plan=normal=1^5=gender=male=1^6=user_id=15460916=1^9=p_ab_id=7=1^10=p_ab_id_2=0=1^11=lang=zh=1; _fbp=fb.1.1586843733592.1271148926; __gads=ID=edd0d47cfab0536d:T=1593573721:S=ALNI_Ma2FXCg_38SGDecQJSjsNOdF1-6NA; ki_s=204981%3A0.0.0.0.0%3B208879%3A0.0.0.0.0; __cfduid=ddd13ec3a0f5d2c2b158a2c931cc79a7e1597156127; __utmz=235335808.1597315982.68.2.utmcsr=blog.csdn.net|utmccn=(referral)|utmcmd=referral|utmcct=/h_wulingfei/article/details/62041986; device_token=9f0057ff29ea2e613b373879631f3e37; _gid=GA1.2.434762596.1597506501; tag_view_ranking=RTJMXD26Ak~Lt-oEicbBr~jH0uD88V6F~pzzjRSV6ZO~LJo91uBPz4~tIqkVZurKP~EUwzYuPRbU~K8esoIs2eW~jhuUT0OJva~eVxus64GZU~PWqXCvm7YM~cbmDKjZf9z~q303ip6Ui5~uusOs0ipBx~KN7uxuR89w~Bd2L9ZBE8q~azESOjmQSV~-sp-9oh8uv~XDEWeW9f9i~pnCQRVigpy~zyKU3Q5L4C~tgP8r-gOe_~bXMh6mBhl8~tg4cf2wCF6~EZQqoW9r8g~-98s6o2-Rp~2R7RYffVfj~rezgCfkPbs~-L-4bBqjrT~QzKFCsGzn-~eVBXl1t9y6~y8GNntYHsi~BU9SQkS-zU~_RfiUqtsxe~t6fkfIQnjP~CrFcrMFJzz~6rYZ-6JKHq~G_f4j5NH8i~HY55MqmzzQ~Ltq1hgLZe3~hIbSsZ4_QS~kyGSr8C4CF~dkvvzKpAOm~kP7msdIeEU~OT4SuGenFI~w8ffkPoJ_S~qNQ253s6b0~ofcDCLl35P~I5npEODuUW~qpeZSmEVVP~1bmFwrp_zN~ITqZ5UzdOC~qiO14cZMBI~oCR2Pbz1ly~4rDNkkAuj_~Jg_BKFcFMF~qtVr8SCFs5~2acjSVohem~17jo987GVJ~RjyWcTb8JF~WjRN9ve4kb~wKl4cqK7Gl~e6DJejypJg~YQeoAIQ1YG~-n1sSUYIlS~13HpD_lYAn~EpVpa-EP-D~tz1LwSKlrP~fN0wOjrtt_~gpglyfLkWs~RybylJRnhJ~1HSjrqSB3U~kHJk-sR8-P~v7P1kpep4p~3lUnzrkqpd~sOBG5_rfE2~7Y-OaPrqAv~SoxapNkN85~lbeyIpnnmp~pTxkC2SiPF~3z9G1yhJBC~RKAHEY3QDd~2NKc4vGSgQ~ua2BSn-Kwj~NBK37t_oSE~xZ6jtQjaj9~LtW-gO6CmS~ETjPkL0e6r~FPCeANM2Bm~YRDwjaiLZn~aKhT3n4RHZ~SqVgDNdq49~l5WYRzHH5-~QTtzgGH2pR~xVHdz2j0kF~YRaAF9oZZs~JXmGXDx4tL~B6pigVy8xT~RcahSSzeRf~BSkdEJ73Ii; __utmc=235335808; __utma=235335808.1520641699.1578992842.1597556427.1597559421.79; login_bc=1; PHPSESSID=15460916_q9iw1f5wjffOfx7mjdeUMuEOS0QpcVAR; privacy_policy_agreement=2; __utmb=235335808.4.10.1597559421; ki_t=1578993030666%3B1597557493986%3B1597559810877%3B39%3B132",
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
        'Referer': 'https://www.pixiv.net/artworks/' + img_imformation['img_id']
        # 'Referer': 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + img_imformation['img_id']
    }
    for img_url in img_imformation['img_url']:
        
        my_file = Path("C:/Users/78346/Desktop/test/"+authorName+'/'+img_imformation['img_title']+'.jpg')
        # if my_file.is_file():
        #     print(img_imformation['img_id']+"已经存在，跳过")
        #     continue
        # 指定的文件存在
        time.sleep(1)
        try:
            img_response = requests.get(img_url, headers=head,timeout=60)
            image = img_response.content
            if n == 0:
                # with open(address + '/' + img_imformation['img_id']
                #           + '.jpg', 'wb') as jpg:
                with open(address + '/' + str(num)
                          + '.jpg', 'wb') as jpg:
                    jpg.write(image)
            else:
                # with open(address + '/' + img_imformation['img_id']
                #           + '(' + str(n) + ')' + '.jpg', 'wb') as jpg:
                with open(address + '/' + str(num)
                          + '(' + str(n) + ')' + '.jpg', 'wb') as jpg:
                    jpg.write(image)
        
        except IOError:
             print("download Error\n"+img_imformation['img_id'])
        finally:
             try:
                 
                 jpg.close()
             except:
                 pass
            
        n = n + 1

#获取关注列表作者ID        
def load_following(username: str, password: str) -> list:
    """
    进入榜单
    :param username: 用户名
    :param password: 密码
    :return: 带有图片url等信息的字典组成的列表
    """
    h={"cookie": "first_visit_datetime_pc=2020-01-14+18%3A07%3A19; p_ab_id=7; p_ab_id_2=0; p_ab_d_id=1075190726; yuid_b=EZeSQAI; _ga=GA1.2.1520641699.1578992842; c_type=49; a_type=0; b_type=1; login_ever=yes; ki_r=; module_orders_mypage=%5B%7B%22name%22%3A%22sketch_live%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22tag_follow%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22following_new_illusts%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22recommended_illusts%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22everyone_new_illusts%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22mypixiv_new_illusts%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22spotlight%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22fanbox%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22featured_tags%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22contests%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22user_events%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22sensei_courses%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22booth_follow_items%22%2C%22visible%22%3Atrue%7D%5D; __utmv=235335808.|2=login%20ever=yes=1^3=plan=normal=1^5=gender=male=1^6=user_id=15460916=1^9=p_ab_id=7=1^10=p_ab_id_2=0=1^11=lang=zh=1; _fbp=fb.1.1586843733592.1271148926; __gads=ID=edd0d47cfab0536d:T=1593573721:S=ALNI_Ma2FXCg_38SGDecQJSjsNOdF1-6NA; ki_s=204981%3A0.0.0.0.0%3B208879%3A0.0.0.0.0; __cfduid=ddd13ec3a0f5d2c2b158a2c931cc79a7e1597156127; __utmz=235335808.1597315982.68.2.utmcsr=blog.csdn.net|utmccn=(referral)|utmcmd=referral|utmcct=/h_wulingfei/article/details/62041986; PHPSESSID=15460916_JUvyKqFteeN7VlCAYWCn8jYYYDRkeut7; device_token=9f0057ff29ea2e613b373879631f3e37; privacy_policy_agreement=2; _gid=GA1.2.434762596.1597506501; tag_view_ranking=RTJMXD26Ak~Lt-oEicbBr~jH0uD88V6F~pzzjRSV6ZO~LJo91uBPz4~tIqkVZurKP~EUwzYuPRbU~K8esoIs2eW~jhuUT0OJva~eVxus64GZU~PWqXCvm7YM~cbmDKjZf9z~q303ip6Ui5~uusOs0ipBx~KN7uxuR89w~Bd2L9ZBE8q~azESOjmQSV~-sp-9oh8uv~XDEWeW9f9i~pnCQRVigpy~zyKU3Q5L4C~tgP8r-gOe_~bXMh6mBhl8~tg4cf2wCF6~EZQqoW9r8g~-98s6o2-Rp~2R7RYffVfj~rezgCfkPbs~-L-4bBqjrT~QzKFCsGzn-~eVBXl1t9y6~y8GNntYHsi~BU9SQkS-zU~_RfiUqtsxe~t6fkfIQnjP~CrFcrMFJzz~6rYZ-6JKHq~G_f4j5NH8i~HY55MqmzzQ~Ltq1hgLZe3~hIbSsZ4_QS~kyGSr8C4CF~dkvvzKpAOm~kP7msdIeEU~OT4SuGenFI~w8ffkPoJ_S~qNQ253s6b0~ofcDCLl35P~I5npEODuUW~qpeZSmEVVP~1bmFwrp_zN~ITqZ5UzdOC~qiO14cZMBI~oCR2Pbz1ly~4rDNkkAuj_~Jg_BKFcFMF~qtVr8SCFs5~2acjSVohem~17jo987GVJ~RjyWcTb8JF~WjRN9ve4kb~wKl4cqK7Gl~e6DJejypJg~YQeoAIQ1YG~-n1sSUYIlS~13HpD_lYAn~EpVpa-EP-D~tz1LwSKlrP~fN0wOjrtt_~gpglyfLkWs~RybylJRnhJ~1HSjrqSB3U~kHJk-sR8-P~v7P1kpep4p~3lUnzrkqpd~sOBG5_rfE2~7Y-OaPrqAv~SoxapNkN85~lbeyIpnnmp~pTxkC2SiPF~3z9G1yhJBC~RKAHEY3QDd~2NKc4vGSgQ~ua2BSn-Kwj~NBK37t_oSE~xZ6jtQjaj9~LtW-gO6CmS~ETjPkL0e6r~FPCeANM2Bm~YRDwjaiLZn~aKhT3n4RHZ~SqVgDNdq49~l5WYRzHH5-~QTtzgGH2pR~xVHdz2j0kF~YRaAF9oZZs~JXmGXDx4tL~B6pigVy8xT~RcahSSzeRf~BSkdEJ73Ii; ki_t=1578993030666%3B1597506377871%3B1597508381621%3B38%3B128; __utma=235335808.1520641699.1578992842.1597506337.1597556427.78; __utmt=1; __utmc=235335808; __utmb=235335808.4.10.1597556427",
       'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'}
    # 使用前确保set_leaderboard()函数已调用，并将其返回的参数列表传入该函数
    response_list = []

    # 先登录用户
    session = __login(username, password)
    offset=0

    # # 初始化爬取的页数以及所需传入的参数
    # p = 1
    data = {
        'offset': offset,  # 这些是 set_leaderboard()函数返回的参数
        'limit': '24',
        'rest': 'show'
    }
    # print("正在加载" + "https://www.pixiv.net/ranking.php?" + urlencode(data))

    # # 如果date是今天，需要去除date项;如果content为综合，需要去除content项。
    # # 这是因为P站排行榜的今日榜不需要传入'date'，而综合区不需要传入'content'
    # if set_leaderboard[2] == time.strftime("%Y%m%d"):
    #     data.pop('date')
    # if set_leaderboard[0] == '':
    #     data.pop('content')

    # 开启循环进行翻页
    while True:

        # 翻页并更新data中的'p'参数
        data['offset'] = offset
        # 使用urlencode()函数将data传入url，获取目标文件
        url = "https://www.pixiv.net/ajax/user/15460916/following?" + urlencode(data)
        print (url)
        response = session.get(url,headers=h)

        # 处理的到的文件并转为字典形式
        # 不加以下这些会报错，似乎是因为eval()不能处理布尔型数据
        global false, null, true
        false = 'False'
        null = 'None'
        true = 'True'
        try:
            response = eval(response.content)['body']['users']
            for i in response:
                if i['userId']!=None:
                    response_list.append(i['userId'])
        except KeyError:
            break
        if offset == 24:
            break
        else:
            offset = offset + 24
    # 返回一个列表，列表元素为字典形式，包括了图片的各个信息
    return response_list
