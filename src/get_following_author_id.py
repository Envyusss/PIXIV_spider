"""
以下为下载关注列表上所有作者ID的demo
"""
from fuction import set_leaderboard,load_leaderboard,\
                    leaderboard_turn_next_page,get_author_id,load_following

if __name__ == '__main__':
    id_list  = load_following('783461007@qq.com', 'zzc991031')
    # page = 1
    # while page <= 1:  #获得（）天的数据，获得几天就填几，如果填2就是今天与昨天
    #     set = leaderboard_turn_next_page(set) #前一天，也可以改成后一天，不过起始页就得改了
    #     response_list = load_leaderboard('783461007@qq.com', 'zzc991031', set)
    #     id_list = id_list + get_author_id(response_list)
    #     id_list = list({}.fromkeys(id_list).keys()) #列表去重，合并一次去一次重
    #     page = page + 1
    # print(id_list)
    file = open('following_author_id.txt', 'w',encoding='utf-8')
    for id in id_list:
        file.write(id+'\n')
    file.close()