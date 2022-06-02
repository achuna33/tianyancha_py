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

url_set = set()
assets_dict = {}
url_dict = {}
email_dict = {}
proxies = {
    "http": "http://127.0.0.1:8080",
    "https": "http://127.0.0.1:8080",
}

#占股比例
percent =  50

#通过企业id获取网站网址和备案URL
def record(id):
    record_list = ""
    emailos = ""
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

#通过id查询每家公司的子公司
def assets(id):
    start = timer()
    assert_get = requests.get("https://capi.tianyancha.com/cloud-company-background/company/getShareHolderStructure?gid={}&rootGid={}&operateType=2".format(id,id),headers=headers_1,verify=False)
    end = timer()
    if int(float(end-start)) >=10:
        print(id  + "超时,请手动查找。或者在网速良好的情况下再次运行")
        return 1
    try:
        company_json = json.loads(assert_get.text)
        for i in company_json['data']['children']:
            if i["percent"] != '-' and int(float(i["percent"].split("%")[0])) >= percent :
                assets_dict[i["gid"]] = id + '|' +i["name"] + '|' + i["percent"]
                assets(i["gid"])
                # print(i["gid"] + i["name"] + i["percent"])
    except Exception  as e:
        print('except:', e)
        return 1;

#负责拼接显示数据
def Splicing(id,Space):
    for i in assets_dict.keys():
        assets_list = assets_dict[i].split("|")
        if assets_list[0] == id :
            with open("result/structure_assets.csv", "a+", encoding="UTF-8") as f:
                if assets_list[3] != "":
                    f.write(Space + assets_list[1] + ',' + assets_list[2] + ',' + assets_list[3] + '\n')
                    # print(Space + assets_list[1] + ',' + assets_list[2] + ',' + assets_list[3])
                else:
                    f.write(Space + assets_list[1] + ',' + assets_list[2] + '\n')
            Splicing(i,Space + ",")
            with open("result/structure_CompaniesList.csv", "a+", encoding="UTF-8") as f:
                f.write(assets_list[1] + "\n")

def write_url(company,url):
    urls = url.replace(" ",",")
    with open("result/structure_urls.csv", "a+", encoding="UTF-8") as f:
        f.write(company + "," + urls + "\n")

def write_email(company,email):
    emails = email.replace(" ",",")
    with open("result/structure_emails.csv", "a+", encoding="UTF-8") as f:
        f.write(company + "," + emails + "\n")

def arrange(data):
    for i in assets_dict.keys():
        assets_list = assets_dict[i].split("|")
        ue  = assets_list[3].split(',')
        if len(ue) == 2:
            if len(ue[0])!=0:
                write_url(assets_list[1],ue[0])
            if len(ue[1])!=0:
                write_email(assets_list[1],ue[1])
        elif len(ue) ==1:
            if "@" not in ue[0] and len(ue[0])!=0:
                write_url(assets_list[1], ue[0])
            elif "@" in ue[0] and len(ue[0])!=0:
                write_email(assets_list[1], ue[1])

def center(id):
    Space = ""
    print("[+] 正在爬取所有符合占股{}的子公司".format(percent))
    assets(id)
    print("[+] 正在对应公司的网址")
    for i in assets_dict.keys():
        url_list = record(i)
        print(url_list)
        assets_dict[i] += "|"+url_list
        # print(i, assets_dict[i])
    print("[+] 正在拼接写入数据 ")
    # print(assets_dict)
    arrange(assets_dict)
    Splicing(id,Space)

def main():
#请输入想要company
    print("请输入查询公司的id号：")
    name = sys.stdin.readline()
    center(name)

if __name__ == '__main__':
    main()