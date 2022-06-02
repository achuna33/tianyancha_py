import json
import sys
import requests
import re
from timeit import default_timer as timer
import urllib3
urllib3.disable_warnings()

#登录天眼查后，寻找cookie 为 auth_token的参数填入下方，acw_sc__v2参数是必须的 这个参数在/company/id 的包中有
auth_token = ""
aliyungf_tc = ""
acw_tc = ""

headers  = {
    "Host":"www.tianyancha.com",
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)",
    "Cookie": "auth_token="+ auth_token + ";aliyungf_tc=" + aliyungf_tc + "; acw_tc= "+ acw_tc +";"
}

headers_1 = {
"Host": "capi.tianyancha.com",
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0",
"X-AUTH-TOKEN": auth_token,
"version": "TYC-Web",
"Origin": "https://dis.tianyancha.com",
}

proxies = {
    "http": "http://127.0.0.1:8080",
    "https": "http://127.0.0.1:8080",
}

enterprise_dict = {}
result_dict = {}

def find_key(id):
    uuid = re.findall("groupUUID\":\"(.+?)\"",requests.get("https://www.tianyancha.com/company/{}".format(id), headers=headers, verify=False,
                 allow_redirects=False).text)[0]
    print(uuid)
    assert_get = requests.get("https://www.tianyancha.com/group/123/{}".format(uuid), headers=headers, verify=False)
    enterprise = (re.findall("<span class='rt'>(.+?)<",assert_get.text))
    print("全部企业共：{}家".format(enterprise[0]))
    print("核心企业共：{}家".format(enterprise[1]))
    print("上市企业共：{}家".format(enterprise[2]))
    if len(enterprise[1]):
        for i in range(1,int(float(enterprise[1])/10+0.99)+1):
            assert_get = requests.get("https://www.tianyancha.com/company/groupPagination.html?uuid={}&type=1&page={}".format(uuid,i),
                                      headers=headers, verify=False)
            tlist = re.findall("company(.*\n.*\n.+?)<",assert_get.text)
            for j in tlist:
                e_name = (re.findall(">(.*)",j))
                e_id = (re.findall("/(.+?)\"",j))
                if e_name[0]:
                    print(e_name[0])
                    print(e_id[0])
                    enterprise_dict[e_name[0]] = e_id[0]

#通过企业id获取网站网址和备案URL
def record(id):
    record_list = ""
    emailos = ""
    url_set = set()
    flag = 1
    while flag:
        record_get = requests.get("https://www.tianyancha.com/pagination/icp.xhtml?TABLE_DIM_NAME=icp&ps=100&pn=1&id={}".format(id),headers=headers,verify=False)
        if 'acw_sc__v2' in record_get.text:
            print('触发验证了，请登录天眼查账号后访问 https://www.tianyancha.com/company/{} 来获取JS最新生成的acw_sc__v2 '.format(id))
            print('请输入最新的acw_sc__v2:')
            acw_sc__v2 = sys.stdin.readline().strip()
            headers[
                'Cookie'] = "auth_token=" + auth_token + ";aliyungf_tc=" + aliyungf_tc + "; acw_tc= " + acw_tc + " ; acw_sc__v2=" + acw_sc__v2
            flag = 1
        else:
            left_col = re.findall("left-col\"(.+?)</",record_get.text)
            for i in left_col:
                if "span" not in i and i.split(">")[1]:
                    url_set.add(i.split(">")[1])
                    record_list += i.split(">")[1] +" "
            flag = 0

    flag = 1
    while flag:
        print("[+] 正在爬取编号{}的域名".format(id))
        weburl_get = requests.get("https://www.tianyancha.com/company/{}".format(id), headers=headers, verify=False,
                                  allow_redirects=False)
        if weburl_get.status_code == 302:
            print('触发验证了，请在登录天眼查账号的网页中手动访问下面的链接来验证！\n {}'.format(re.findall("<a href=\"(.*)\">",weburl_get.text)[0]))
            print('访问完请在命令行回车哦！')
            name = sys.stdin.readline()
            flag = 1
        elif 'acw_sc__v2' in weburl_get.text:
            print('触发验证了，请登录天眼查账号后访问 https://www.tianyancha.com/company/{} 来获取JS最新生成的acw_sc__v2 '.format(id))
            print('请输入最新的acw_sc__v2:')
            acw_sc__v2 = sys.stdin.readline().strip()
            headers['Cookie'] = "auth_token="+ auth_token + ";aliyungf_tc=" + aliyungf_tc + "; acw_tc= "+ acw_tc +" ; acw_sc__v2=" + acw_sc__v2
            flag = 1
        else:
            weburl_col = re.findall("target=http.+?nofollow noreferrer\">(.+?)<",weburl_get.text)
            print(weburl_col)
            email_temp = (re.findall('"emailList":\["(.+?)\]',weburl_get.text))
            if email_temp:
                emailos = email_temp[0].replace('"','').replace(","," ")
            flag = 0

    if weburl_col:
        weburl = weburl_col[0]
        if emailos:
            print("weburl:" + weburl)
            print(record_list[0:-1] + ' ' + weburl + ',' +  emailos)
            return record_list[0:-1] + ' ' + weburl + ',' +  emailos
        else:
            return record_list[0:-1] + ' '+weburl
    elif emailos:
        return record_list[0:-1] + ',' + emailos

    return record_list[0:-1]

def Splicing(company):
    with open("result/group_CompaniesList.csv", "a+", encoding="UTF-8") as f:
        f.write(company + "\n")

def write_url(company,url):
    print(company)
    urls = url.replace(" ",",")
    print(urls)
    with open("result/group_urls.csv", "a+", encoding="UTF-8") as f:
        f.write(company + "," + urls + "\n")

def write_email(company,email):
    emails = email.replace(" ",",")
    with open("result/group_emails.csv", "a+", encoding="UTF-8") as f:
        f.write(company + "," + emails + "\n")

def write_all(gs,ue):
    if len(ue) == 2:
        if len(ue[0]) != 0:
            write_url(gs, ue[0])
        if len(ue[1]) != 0:
            write_email(gs, ue[1])
    elif len(ue) == 1:
        if "@" not in ue[0] and len(ue[0]) != 0:
            write_url(gs, ue[0])
        elif "@" in ue[0] and len(ue[0]) != 0:
            write_email(gs, ue[1])
    Splicing(gs)

def main():
    print("请输入查询集团下任意公司的id:")
    id = sys.stdin.readline()
    find_key(id.strip())
    print(enterprise_dict)
    for i in enterprise_dict.keys():
        result_dict[i] = record(enterprise_dict[i]).split(',')

    print("开始写入数据：")
    for i in result_dict.keys():
        write_all(i,result_dict[i])

if __name__ == '__main__':
    main()


