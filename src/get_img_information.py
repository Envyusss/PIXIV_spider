"""
以下为通过作者ID下载该作者所有图片的一个demo
"""
from fuction import get_author_img_dic,get_author_illusts,\
                    get_img_dic,get_img_imformation,download,load_imgid
import os
import pprint
import re
if __name__ == '__main__':
    #打开作者ID的txt文件，一个ID为一行
    num=0
    file = open('following_author_id.txt',encoding='utf-8')
    while True:
        author_id = file.readline().replace('\n','')
        author_img_dic = get_author_img_dic(author_id,'username','password')
        illusts_list = get_author_illusts(author_img_dic)
        for img_id in illusts_list:
            try:
                img_dic = get_img_dic(img_id,'username','password')
                authorName=img_dic['authorName'].replace('/','').replace("\\",'')
                address = 'your path' + authorName
            except:
                print("login Error"+img_dic['illustID'])
            else:
                pass

            try:
                os.mkdir(address)
            except:
                img_imformation = get_img_imformation(img_dic)
                # download(img_imformation, address,img_dic['authorName'])
                download(img_imformation, address,img_dic['authorName'],num)
                num=num+1
            else:
                img_imformation = get_img_imformation(img_dic)
                # download(img_imformation, address,img_dic['authorName'])
                download(img_imformation, address,img_dic['authorName'],num)
                num=num+1
                load_imgid(img_dic['illustID'])
            finally:
                print(img_dic['illustID'])
        # with open ('following_author_id.txt','r',encoding="utf-8")as f1,open ('following_author_id1.txt','w',encoding="utf-8")as f2:
        #     for line in f1:
        #         author_id=author_id+'\n'
        #         f2.write(re.sub(author_id,'',line))
        #     os.remove('following_author_id.txt')
        #     os.rename('following_author_id1.txt','following_author_id.txt')
        zzc=input(int)
        print("GG")      
        if author_id == '':
            break
    file.close()