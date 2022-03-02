import requests
from script.m3u_parser.m3u_parser import M3uParser
import json
from operator import itemgetter
import re
import logging
from requests.adapters import HTTPAdapter


class M3U:

    def __init__(self, m3u_url, logo_url):
        self.m3u_url = m3u_url
        self.logo_url = logo_url
        self.group_keys = ['CCTV', '卫视', '浙江', 'NewTV', 'SiTV']
        self.logo_data = {}
        self.screen = []
        self.classifies = []
        self.m3u_list = []

    def get_logo(self):
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36'
        }
        resp = requests.get(self.logo_url, headers=header, timeout=2)
        lines = resp.text.strip().split('\n')
        name = [i.split(',')[0].strip() for i in lines]
        logo = [i.split(',')[1].strip() for i in lines]
        line = zip(name, logo)
        self.logo_data = dict(line)
        logging.info('Get logo file... Done!')

    def m3u_check(self):
        '''
        拉取cn.m3u,并进行初筛
        '''
        header = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36'
        m3u_parser = M3uParser(timeout=5, useragent=header)
        m3u_parser.parse_m3u(self.m3u_url)
        m3u_parser.filter_by('status', 'GOOD')
        m3u_parser.sort_by('name')
        # print(m3u_parser.get_list())
        print(len(m3u_parser.get_list()))
        m3u_parser.to_file('./script/cn.json')

    def screening(self):
        '''
        筛选1080P的源
        补充缺失logo地址
        补充EPG对应ID
        '''
        logo = self.logo_data
        with open('./script/cn.json', 'r') as jf:
            file = json.loads(jf.read())
        heigh_1080 = [i for i in file if '1080' in i['name']]
        for heigh in heigh_1080:
            tv_name = re.findall(
                '(.*?)\s\(.*?\)', heigh['name'].replace('-', ''))[0]
            for lg in logo.keys():
                if lg == tv_name:
                    heigh['logo'] = logo[lg]
                    heigh['tvg']['id'] = lg
                    heigh['name'] = lg
                    break
            if self.grouping(tv_name):
                heigh['group-title'] = self.grouping(tv_name)
            else:
                heigh['group-title'] = '其它'
        self.screen = heigh_1080
        logging.info('Screening... Done!')

    def grouping(self, tv_name,):
        for key in self.group_keys:
            if key in tv_name:
                return key

    def classify(self):
        for i in self.screen:
            init = {}
            init['tvg-id'] = ''
            init['tvg-name'] = i['tvg']['id']
            init['tvg-logo'] = i['logo']
            init['group-title'] = i['group-title']
            init['name'] = i['name']
            init['url'] = i['url']
            if self.check(init['name'], init['url']):
                self.m3u_list.append(init)
        self.classifies = sorted(self.m3u_list, key=itemgetter('group-title'))
        logging.info('classify... Done!')

    def check(self, name, url):
        '''
        连通性检测
        '''
        header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36'
        }
        s = requests.Session()
        s.mount('http://', HTTPAdapter(max_retries=5))
        s.mount('https://', HTTPAdapter(max_retries=5))
        try:
            req = s.get(url, headers=header, timeout=2)
            status = req.status_code
            if status == 200:
                logging.info(
                    f'Checking: {name}, {url},\033[0;37;42m Online \033[0m  {str(status)}')
                return True
            else:
                logging.warning(
                    f'检测连通性: {name}, {url},\033[0;31;43m Timeout \033[0m {str(status)}')
                return False
        except requests.exceptions.RequestException:
            logging.error(f'检测连通性: {name}, {url}, \033[0;37;41m Error \033[0m')
            return False

    def to_m3u(self):
        with open('TV.m3u', 'w', encoding='utf8') as fw:
            fw.write(
                '#EXTM3U x-tvg-url="https://cdn.jsdelivr.net/gh/iptv-pro/iptv-pro.github.io@main/epg/epg.xml.gz"'+'\n')
            for i in self.classifies:
                key = list(i.keys())
                line = '#EXTINF:-1 '+f'{key[0]}="{i[key[0]]}" '+f'{key[1]}="{i[key[1]]}" ' + \
                    f'{key[2]}="{i[key[2]]}" '+f'{key[3]}="{i[key[3]]}",' + \
                    f'{i[key[4]]}'+'\n'+f'{i[key[5]]}'+'\n'
                fw.write(line)
        logging.info('Saved to file: TV.m3u')

    def __call__(self):
        self.m3u_check()
        self.get_logo()
        self.screening()
        self.classify()
        self.to_m3u()


if __name__ == "__main__":
    m3u_url = 'https://iptv-org.github.io/iptv/countries/cn.m3u'
    logo_url = 'https://cdn.jsdelivr.net/gh/iptv-pro/iptv-pro.github.io/list.txt'
    m = M3U(m3u_url=m3u_url, logo_url=logo_url)
    m()
