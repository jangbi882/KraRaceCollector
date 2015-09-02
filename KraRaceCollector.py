# -*- coding: utf-8 -*-
from flask import Flask, Response
import urllib
import urllib2
from bs4 import BeautifulSoup
import re

app = Flask(__name__)


@app.route('/test')
def hello_world():
    return 'Hello World!'


def get_table(date, race_no, table_no, url, values):
    headers = {
        "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"
    }
    data = urllib.urlencode(values)
    try:
        request = urllib2.Request(url, data, headers)
        response = urllib2.urlopen(request)
        # 마사회 페이지는 euc-kr
        # page = response.read().decode('cp949', 'ignore')
        # 하지만 인코딩을 지정해 주면 오히려 깨진다.
        page = response.read()
        response.close()

        # parser로 lxml을 사용. 별도 설치 필요. 더 빠르고 강력하다.
        # soup = BeautifulSoup(page, "lxml")
        # 여기서 인코딩을 지정해 주어야 한다.
        soup = BeautifulSoup(page, "lxml", from_encoding='cp949')

        try:
            i_table_no = int(table_no) - 1
        except Exception:
            i_table_no = 1

        table = soup.find_all("table")[i_table_no]

        caption = table.find("caption")
        if caption:
            filename = "{}_{}경주_표{}_{}.txt".format(date, race_no, table_no, caption.contents[0].encode('utf8'))
        else:
            filename = "{}_{}경주_표{}.txt".format(date, race_no, table_no)

        headers = [header.text.encode('utf8').strip() for header in table.find_all('th')]
        print "#Header: {}".format(len(headers))
        rows = []
        for row in table.find_all('tr'):
            rows.append([re.sub(u"\s+", " ", val.text.encode('utf8').strip().replace("\n", " ")) for val in row.find_all('td')])
        print "#Row: {}".format(len(rows))

        csv = "|".join(headers)
        csv += "\n"

        for row in rows:
            if len(row) > 0:
                csv += "|".join(row)
                csv += "\n"

    except urllib2.HTTPError, e:
        print e.reason.args[1]
    except urllib2.URLError, e:
        print e.reason.args[1]
    except Exception as e:
        print str(e)

    ret = Response(csv, mimetype='text/plane')
    ret.headers["Content-Disposition"] = "attachment; filename={}".format(filename)

    return ret


# 경기결과
@app.route('/score/<date>/<race_no>/<table_no>')
def get_score(date, race_no, table_no):
    url = 'http://race.kra.co.kr/raceScore/ScoretableDetailList.do'
    values = {
        "nextFlag": "false",
        "meet":"1",
        "realRcDate": date,
        "realRcNo": race_no,
        "Act":"04",
        "Sub":"1",
        "pageIndex":"1",
        "fromDate":"",
        "toDate":""
    }
    return get_table(date, race_no, table_no, url, values)


# 단연복
@app.route('/betting_fit_scm/<date>/<race_no>')
def get_betting_fit_scm(date, race_no):
    url = 'http://race.kra.co.kr/raceScore/ScoretableBettingprofitScm.do'
    values = {
        "Act":"04",
        "Sub":"1",
        "meet":"1",
        "fromDate":"",
        "toDate":"",
        "hrNo":"",
        "jkNo":"",
        "trNo":"",
        "owNo":"",
        "pageIndex":"1",
        "realRcDate":date,
        "realRcNo":race_no
    }
    return get_table(date, race_no, 1, url, values)


# 쌍승식
@app.route('/betting_fit_both/<date>/<race_no>')
def get_betting_fit_both(date, race_no):
    url = 'http://race.kra.co.kr/raceScore/ScoretableBettingprofitBoth.do'
    values = {
        "Act":"04",
        "Sub":"1",
        "meet":"1",
        "realRcDate":date,
        "realRcNo":race_no
    }
    return get_table(date, race_no, 1, url, values)


# 복연승식
@app.route('/betting_fit_bc/<date>/<race_no>')
def get_betting_fit_bc(date, race_no):
    url = 'http://race.kra.co.kr/raceScore/ScoretableBettingprofitBc.do'
    values = {
        "meet":"1",
        "realRcDate":date,
        "realRcNo":race_no,
        "chulNo1":"",
        "Act":"04",
        "Sub":"1"
    }
    return get_table(date, race_no, 1, url, values)


# 삼복승식
@app.route('/betting_fit_3bc/<date>/<race_no>')
def get_betting_fit_3bc(date, race_no):
    url = 'http://race.kra.co.kr/raceScore/ScoretableBettingprofit3Bc.do'
    values = {
        "Act":"04",
        "Sub":"1",
        "meet":"1",
        "realRcDate":date,
        "realRcNo":race_no
    }
    return get_table(date, race_no, 1, url, values)



if __name__ == '__main__':
    app.run()
