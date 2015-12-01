# -*- coding: utf-8 -*-
import urllib
import urllib2
from bs4 import BeautifulSoup
import re
import sys
import locale
import os.path
import time

os_encoding = locale.getpreferredencoding()
file_base = os.path.basename(__file__)
time_re = re.compile(r"^(\d+)\:(\d+).(\d+)$")

option_data = {
    "contestant": {
        "desc" : u"출전상세정보",
        "url": 'http://race.kra.co.kr/chulmainfo/chulmaDetailInfoChulmapyo.do',
        "values" : {
            "rcDate": '{date}',
            "rcNo": '{race_no}',
            "Sub":"1",
            "Act":"02",
            "meet": '{city}'
        },
        "data_table_no" : 2,
        "split_column_list" : [(6, r"(\d+)\((\-*\d+\.*\d*)\)", 0), (7, r"\((.*)\)(.*)", 1)]
    },
    "record": {
        "desc" : u"전적",
        "url": 'http://race.kra.co.kr/chulmainfo/chulmaDetailInfoRecord.do',
        "values" : {
            "rcDate": '{date}',
            "rcNo": '{race_no}',
            "Sub":"1",
            "Act":"02",
            "meet": '{city}'
        },
        "data_table_no" : 2,
        "split_column_list" : [(2, r"(\d+)\((\d+)\/(\d+)\)", 0), (3, r"(.*)\%", 0), (4, r"(.*)\%", 0)
            ,(5, r"(\d+)\((\d+)\/(\d+)\)", 0), (6, r"(.*)\%", 0), (7, r"(.*)\%", 0)]
    },
    "course_rec": {
        "desc" : u"해당거리전적",
        "url": 'http://race.kra.co.kr/chulmainfo/chulmaDetailInfoDistanceRecord.do',
        "values" : {
            "rcDate": '{date}',
            "rcNo": '{race_no}',
            "Sub":"1",
            "Act":"02",
            "meet": '{city}'
        },
        "data_table_no" : 2,
        "split_column_list" : [(2, r"(\d+)\((\d+)\/(\d+)\)", 0), (3, r"(.*)\%", 0), (4, r"(.*)\%", 0)
            ,(5, r"(\d+\:\d+.\d+).+", 0), (6, r"(\d+\:\d+.\d+).+", 0), (7, r"(\d+\:\d+.\d+).+", 0)]
    },
    "near10_rec": {
        "desc" : u"최근10회전적",
        "url": 'http://race.kra.co.kr/chulmainfo/chulmaDetailInfo10Score.do',
        "values" : {
            "rcDate": '{date}',
            "rcNo": '{race_no}',
            "Sub":"1",
            "Act":"02",
            "meet": '{city}'
        },
        "data_table_no" : 2,
        "split_column_list" : [(14, r"(.+)\((.+)\)", 0)],
        "skip_column_list" : [15, 16, 17]
    },
}

def get_table(option, date, race_no, table_no, city):

    try:
        info = option_data[option]
    except KeyError:
        return None

    if city == "seoul": i_city = 1
    elif city == "jeju" : i_city = 2
    elif city == "busan" : i_city = 3
    else: i_city = 1

    url = info["url"]
    values = info["values"]
    for key in values.keys():
        val = values[key]
        if val == '{date}': values[key] = date
        elif val == '{race_no}' : values[key] = race_no
        elif val == '{city}' : values[key] = i_city

    # 데이터가 있는 테이블 번호; 0에서 시작
    data_table_no = info["data_table_no"]
    # 둘로 나눌 컬럼 리스트; 0에서 시작
    # (col_no, pattern, def_col)
    split_column_list = info["split_column_list"]

    # 무시 컬럼 리스트
    if "skip_column_list" in info:
        skip_column_list = info["skip_column_list"]
    else:
        skip_column_list = None

    # 해더를 잘 적어 주지 않으면 시스템이 비정상 호출로 거부 당한다.
    headers = {
        "Accept-Encoding" : "gzip, deflate, sdch"
        ,"Accept-Language" : "ko,en-US;q=0.8,en;q=0.6"
        ,"Upgrade-Insecure-Requests" : "1"
        ,"User-Agent" : "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"
        ,"Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        ,"Referer" : url
        # 쿠키는 변경된 가능성을 확인해야 한다.
        ,"Cookie" : "WMONID=Nz7aZM1C3N0; NRACE_JSESSIONID=Of-NDgpECnNTA7a91UDqWQ7Nw-9Yvyy_Pp3PO1DsIFt9DAHhBzkO!-1826629772; itoken=null"
        ,"Connection" : "keep-alive"
    }
    data = urllib.urlencode(values)
    try:
        # 데이터가 한 번에 나오지 않는 경우가 있어 NUM_RETRY회까지 재요청하게 구조 수정
        NUM_RETRY = 20

        for num_iter in range(NUM_RETRY):
            request = urllib2.Request(url, data, headers)
            response = urllib2.urlopen(request)
            # 마사회 페이지는 euc-kr
            # page = response.read().decode('euc-kr', 'ignore')
            # page = response.read().decode('cp949', 'ignore')
            # 하지만 인코딩을 지정해 주면 오히려 깨진다.
            page = response.read()
            response.close()

            with open("dump.html", "w") as out_file:
                out_file.write(page)

            # parser로 lxml을 사용. 별도 설치 필요. 더 빠르고 강력하다.
            # soup = BeautifulSoup(page, "lxml")
            # 여기서 인코딩을 지정해 주어야 한다.

            ## lxml 파서의 경우 html을 파싱하다 잘리는 경우가 많이 발견되어 html.parser로 변경
            # soup = BeautifulSoup(page, "lxml", from_encoding='cp949')
            soup = BeautifulSoup(page, 'html.parser', from_encoding='cp949')

            ######
            # 파일이름 정하기
            filename = u"{0}_{1}_{2}_race{3:02d}.txt".format(city, option, date, int(race_no))

            ######
            # 대상 테이블 찾기
            try:
                i_table_no = int(table_no) - 1
            except Exception:
                if data_table_no:
                    i_table_no = data_table_no
                else:
                    i_table_no = 0

            all_table = soup.find_all("table")
            num_all_table = len(all_table)

            if num_all_table > 0 or num_iter+1 >= NUM_RETRY:
                break

            print ("Retrying...")
            time.sleep(2)


        if i_table_no >= num_all_table:
            i_table_no = num_all_table - 1
        elif i_table_no < 0:
            i_table_no = 0

        #결국 못 얻어온 경우
        if i_table_no < 0:
            print ("FAIL!!!")
            return False


        headers = []
        rows = []
        for i_table_no in range(i_table_no, (i_table_no)+1 if option != "near10_rec" else len(all_table)):

            table = all_table[i_table_no]

            ######
            tr_rows = []

            # 컬럼 헤더 만들기
            for tr in table.find_all('tr'):
                ths = tr.select("th")
                if len(ths) > 0:
                    tr_rows.append(tr)

            # 최근10회전적 예외 처리
            horse_name = None
            if option == "near10_rec":
                if len(tr_rows) > 0:
                    anchor = tr_rows[0].select("a")[0]
                    horse_name = anchor.text.encode("utf-8").strip()
                    del tr_rows[0]
                else:
                    horse_name = "Unknown"

            if len(headers) <= 0:
                if len(tr_rows) == 1:
                    headers = [header.text.encode("utf-8").strip() for header in tr_rows[0].select("th")]
                elif len(tr_rows) == 2:
                    tr1 = tr_rows[0].select("th")
                    tr2 = tr_rows[1].select("th")
                    tr2_ptr = 0
                    for th1 in tr1:
                        try:
                            rowspan = int(th1['rowspan'])
                        except KeyError:
                            rowspan = 1

                        try:
                            colspan = int(th1['colspan'])
                        except KeyError:
                            colspan = 1

                        th1_str = th1.text.encode("utf-8").strip()
                        if colspan == 1:
                            headers.append(th1_str)
                        else:
                            for i in range(tr2_ptr, tr2_ptr+colspan):
                                th2 = tr2[i]
                                th2_str = th2.text.encode("utf-8").strip()
                                headers.append(th1_str+"_"+th2_str)
                            tr2_ptr += colspan

                # 무시 컬럼 처리
                if skip_column_list:
                    skip_column_list.sort(reverse=True)
                    for col_no in skip_column_list:
                        if len(headers) > col_no:
                            del(headers[col_no])

                # 둘로 나눠야 하는 컬럼 추가
                if split_column_list:
                    split_column_list.sort(reverse=True)
                    for logic in split_column_list:
                        col_no = logic[0]
                        r = re.compile(logic[1])
                        num_cal = r.groups
                        org_col_name = headers[col_no]
                        headers[col_no] = org_col_name+"_1"
                        for n in range(1, num_cal):
                            headers.insert(col_no+n, org_col_name+"_{}".format(n+1))

                # 최근10회전적 예외처리
                if horse_name:
                    headers.insert(0, "마명")

            ######
            # 데이터 넣기
            for row in table.find_all('tr'):
                cols = row.find_all('td')
                col_data =[re.sub(u"\s+", " ", val.text.encode("utf-8").strip().replace("\n", " ")) for val in cols]
                if len(cols) <= 0:
                    continue

                # 무시 컬럼 데이터 제거
                if skip_column_list:
                    for col_no in skip_column_list:
                        if len(col_data) > col_no:
                            del(col_data[col_no])

                if split_column_list:
                    # 여러 컬럼으로 분라하거나 특수문자 제거
                    for logic in split_column_list:
                        col_no = logic[0]
                        r = re.compile(logic[1])
                        num_cal = r.groups
                        def_cal = logic[2]
                        org_val = col_data[col_no]
                        del col_data[col_no]

                        match = r.search(org_val)
                        if match:
                            vals = match.groups()
                            vals = reversed(vals)
                            for val in vals:
                                col_data.insert(col_no, val)
                        else:
                            for i in range(num_cal-1, -1 , -1):
                                if i == def_cal:
                                    col_data.insert(col_no, org_val)
                                else:
                                    col_data.insert(col_no, '')

                # 시간을 변환하여야 하는 것이 있는지 확인
                for i, val in enumerate(col_data):
                    res = time_re.search(val)
                    if res:
                        col_data[i] = str(int(res.group(1))*60 + float(res.group(2)+"."+res.group(3)))

                # 최근10회전적 예외처리
                if horse_name:
                    col_data.insert(0, horse_name)
                
                # 빈 자료를 NA로 변경
                col_data = ["NA" if d == "" else d for d in col_data]

                rows.append(col_data)

        csv = ",".join(headers)
        csv += "\n"

        ######
        # 파일에 쓰기
        for row in rows:
            if len(row) > 0:
                csv += ",".join(row)
                csv += "\n"

        with open(filename, "w") as out_file:
            out_file.write(csv)


    except urllib2.HTTPError, e:
        print e.reason.args[1]
        return False
    except urllib2.URLError, e:
        print e.reason.args[1]
        return False
    except Exception as e:
        # print str(e)
        # return False
        raise e


    return filename


#############
def help(add_val):
    print "USAGE   :\t{}{} <city> <option> <date> <race_no> [<table_no>]".format("python " if add_val==1 else "", file_base)
    print "EXAMPLE :\t{}{} busan contestant 20150719 1".format("python " if add_val==1 else "", file_base)
    print
    print "\n== Option List =="
    for cmd in option_data.keys():
        print u"{}\t:\t{}".format(cmd, option_data[cmd]["desc"])
    exit()


if __name__ == '__main__':
    by_python = 0

    if len(sys.argv) < 1:
        help(by_python)
    if sys.argv[0] == file_base:
        by_python = 1

    if len(sys.argv) < 3+by_python:
        help(by_python)

    city = sys.argv[1]
    option = sys.argv[2]
    date = sys.argv[3]
    race_no = sys.argv[4]
    if 5 < len(sys.argv):
        table_no = sys.argv[5]
    else:
        table_no = None

    '''
    city = "busan"
    option = "near10_rec"
    date = "20151129"
    race_no = "5"
    table_no = None
    '''

    command_list = option_data.keys()
    if option not in command_list:
        print "Invalid option: {}".format(option)
        help(by_python)

    filename = get_table(option, date, race_no, table_no if option=="score" else None, city)

    if filename:
        print("Result file {} is created.".format(filename.encode(os_encoding)))
    else:
        print("An error occurred!")