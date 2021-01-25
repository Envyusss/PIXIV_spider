import re, requests, time
from urllib.parse import urlencode

def __login(username: str, password: str) -> requests.sessions.Session:
    """
    登陆函数
    :param username: 用户名
    :param password: 密码
    :return: 该用户名的会话(session)
    """
    # 模拟一下浏览器
    head = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:52.0) Gecko/20100101 Firefox/52.0'
    }

    # 用requests的session模块记录登录的cookie

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
        'pixiv_id': username,
        'password': password,
        'return_to': 'https://www.pixiv.net/',
        'post_key': post_key,
    }

    # 将data post给登录页面，完成登录
    session.post("https://accounts.pixiv.net/login?lang=zh", data=data, headers=head)
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
    for i in response_list:
        print(i)

    # 返回一个列表，列表元素为字典形式，包括了图片的各个信息
    # return response_list
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

if __name__ == '__main__':
    set = set_leaderboard('插画', '今日', False, '20190729') #设置起始页
    response_list = load_leaderboard('783461007@qq.com', 'zzc991031', set)
    