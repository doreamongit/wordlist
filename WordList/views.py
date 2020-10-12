from django.http import HttpResponse
from django.shortcuts import render

from bs4 import BeautifulSoup
import requests
import json
import pymysql
from django.views.decorators.csrf import csrf_exempt


def creat_db():
    db = pymysql.connect(host='localhost',
                         port=3306,
                         user='root',
                         password='111111',
                         db='words',
                         charset='utf8')

    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()
    create_tb_cmd = '''
                        CREATE TABLE IF NOT EXISTS words
                        (
                        id int NOT NULL PRIMARY KEY AUTO_INCREMENT,
                        word VARCHAR(64) unique,
                        transfer VARCHAR(128),
                        grasp INT NOT NULL DEFAULT 0
                        );
                        '''

    try:
        # 主要就是上面的语句
        cursor.execute(create_tb_cmd)
    except Exception as e:
        print(e)

    db.close()

def save_words_to_db(words):
    db = pymysql.connect(host='localhost',
                         port=3306,
                         user='root',
                         password='111111',
                         db='words',
                         charset='utf8')

    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()

    sql = "REPLACE INTO words (word, transfer) VALUES (%s,%s) "
    print(sql)
    try:
        # 执行sql语句
        cursor.executemany(sql, words)
        # 提交到数据库执行
        db.commit()
    except Exception as e:
        print(e)
        # 如果发生错误则回滚
        # db.rollback()
    # 关闭数据库连接
    db.close()


def get_words_from_server():
    response = requests.get("http://www.eol.cn/html/en/cetwords/cet4.shtml")
    soup = BeautifulSoup(response.content, 'html.parser')  # 使用lxml解释库
    all_fl = soup.find_all(name='div', attrs={"class": "wordL fl"})

    has_abandon = False
    words = []
    words_DB = []
    for tag in all_fl:
        plist = tag.text.lstrip().split('\n')
        for itemp in plist:
            word_split = itemp.lstrip().split(' ', 1)
            if len(word_split) < 2:
                continue
            word = word_split[0]
            transfer = word_split[1]

            if word == "abandon" :
                if has_abandon == True :
                    continue
                has_abandon = True
            if word == "assport":
                word = "passport"

            word_info = {}
            word_info["word"] = word
            word_info["transfer"] = transfer

            words.append(word_info)

            words_DB.append((word, transfer))
    # 将请求回来的数据保存到数据库
    save_words_to_db(words_DB)
    return words

def get_words():
    db = pymysql.connect(host='localhost',
                         port=3306,
                         user='root',
                         password='111111',
                         db='words',
                         charset='utf8')

    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()
    sql = "select * from words WHERE grasp = 0"

    cursor.execute(sql)
    # 获取所有记录列表
    words = []
    results = cursor.fetchall()
    if len(results) > 0 :
        for row in results:
            word = row[1]  #
            transfer = row[2]

            rowInfo = {}
            rowInfo['word'] = word
            rowInfo['transfer'] = transfer
            words.append(rowInfo)
    else:
        print("从网络请求")
        words = get_words_from_server()
    # 关闭数据库连接
    db.close()
    return words

def wordlist(request):
    context = {}
    creat_db()

    words = get_words()

    context['words'] = json.dumps(words)

    return render(request, 'wordlist.html', context)

@csrf_exempt
def grasp(request):
    dict = {}
    word = request.POST.get('word', '')

    dict["word"] = word

    db = pymysql.connect(host='localhost',
                         port=3306,
                         user='root',
                         password='111111',
                         db='words',
                         charset='utf8')

    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()

    sql = "UPDATE words SET grasp = 1 WHERE word = '{0}'".format(word)
    print(sql)
    try:
        # 执行sql语句
        cursor.execute(sql)
        # 提交到数据库执行
        db.commit()
    except Exception as e:
        print(e)
        # 如果发生错误则回滚
        db.rollback()
    # 关闭数据库连接
    db.close()

    return HttpResponse(json.dumps(dict), content_type="application/json")