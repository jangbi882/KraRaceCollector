# -*- coding: utf-8 -*-
import urllib
import urllib2
from bs4 import BeautifulSoup
import re
import sys
import locale
import os.path

os_encoding = locale.getpreferredencoding()
file_base = os.path.basename(__file__)

option_data = {
    "seoul_parti": {
        "desc" : u"서울 출전상세정보",
        "url": 'http://race.kra.co.kr/chulmainfo/chulmaDetailInfoChulmapyo.do',
        "values" : {
            "rcDate": '{date}',
            "rcNo": '{race_no}',
            "Sub":"1",
            "Act":"02",
            "meet":"1"
        },
        "data_table_no" : 2,
        "split_column_list" : [(6, r"(\d+)\((\d+)\)", 0), (7, r"\((.*)\)(.*)", 1)]
    }
}

def get_table(option, date, race_no, table_no):

    try:
        info = option_data[option]
    except KeyError:
        return None

    url = info["url"]
    values = info["values"]
    for key in values.keys():
        val = values[key]
        if val == '{date}': values[key] = date
        elif val == '{race_no}' : values[key] = race_no

    # 데이터가 있는 테이블 번호; 0에서 시작
    data_table_no = info["data_table_no"]
    # 둘로 나눌 컬럼 리스트; 0에서 시작
    # (col_no, pattern, def_col)
    split_column_list = info["split_column_list"]

    headers = {
        "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"
    }
    data = urllib.urlencode(values)
    try:
        request = urllib2.Request(url, data, headers)
        response = urllib2.urlopen(request)
        # 마사회 페이지는 euc-kr
        # page = response.read().decode('euc-kr', 'ignore')
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
            if data_table_no:
                i_table_no = data_table_no;
            else:
                i_table_no = 0

        all_table = soup.find_all("table")
        if i_table_no >= len(all_table):
            i_table_no = len(all_table) - 1
        elif i_table_no < 0:
            i_table_no = 0

        table_no = i_table_no+1
        table = all_table[i_table_no]

        if option == "score" :
            caption = table.find("caption")
            if caption:
                filename = u"{}_race{}{}_{}.txt".format(date, race_no, u"_table{}".format(table_no) if table_no else "",
                                                      caption.contents[0])
            else:
                filename = u"{}_race{}{}.txt".format(date, race_no, u"_table{}".format(table_no) if table_no else "")
        else:
            filename = u"{}_race{}_{}.txt".format(date, race_no, option)


        headers = [header.text.encode("utf-8").strip() for header in table.find_all('th')]
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

        rows = []
        for row in table.find_all('tr'):
            cols = row.find_all('td')
            col_data =[re.sub(u"\s+", " ", val.text.encode("utf-8").strip().replace("\n", " ")) for val in cols]
            if len(cols) <= 0:
                continue
            if split_column_list:
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

            rows.append(col_data)

        csv = "|".join(headers)
        csv += "\n"

        for row in rows:
            if len(row) > 0:
                csv += "|".join(row)
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
        print str(e)
        return False

    return filename


#############
def help(add_val):
    print "USAGE   :\t{}{} <option> <date> <race_no> [<table_no>]".format("python " if add_val==1 else "", file_base)
    print "EXAMPLE :\t{}{} seoul_parti 20150719 1".format("python " if add_val==1 else "", file_base)
    print "EXAMPLE :\t{}{} scm 20150719 1".format("python " if add_val==1 else "", file_base)
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

    option = sys.argv[1]
    date = sys.argv[2]
    race_no = sys.argv[3]
    if 4 < len(sys.argv):
        table_no = sys.argv[4]
    else:
        table_no = None
    '''
    option = "seoul_parti"
    date = "20150822"
    race_no = "1"
    table_no = None
    '''

    command_list = option_data.keys()
    if option not in command_list:
        print "Invalid option: {}".format(option)
        help(by_python)

    filename = get_table(option, date, race_no, table_no if option=="score" else None)

    if filename:
        print("Result file {} is created.".format(filename.encode(os_encoding)))
    else:
        print("An error occurred!")