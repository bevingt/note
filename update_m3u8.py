import requests
from requests.adapters import HTTPAdapter


def download_iptv_m3u8(url):
    '''
    从iptv-org处下载m3u8文件
    '''
    header = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36'
    }
    resp = requests.get(url, headers=header)
    with open('cn.m3u8', 'wb') as m3u8_file:
        m3u8_file.write(resp.content)


def read_m3u8():
    '''
    读取m3u8文件，并筛选1080P的列表，转成字典
        '''
    with open('cn.m3u8', 'r', encoding='utf8') as m3u8:
        lines = m3u8.read()
    lines_list = lines.split('\n')
    file_split = {lines_list[i]: lines_list[i+1]
                  for i in range(1, len(lines_list)-1, 2)}
    for key in list(file_split.keys()):
        if '1080' not in key:
            file_split.pop(key)
    return file_split


def classify(head, url, key, group_name):
    '''
    对播放清单进行分类
    '''
    new_head = []
    new_url = []
    for i, v1 in enumerate(head):
        head_split = v1.split(',')
        if key in head_split[1]:
            group = head_split[0].strip().split(' ')
            for j, v2 in enumerate(group):
                if ('group-title=' in v2) or (v2 in ''):
                    group[j] = f'group-title="{group_name}"'
                elif len(group) == 1:
                    group.append(f'group-title="{group_name}"')
                else:
                    continue
            new_group = [' '.join(group)]
            new_group.append(head_split[1])
            new_head.append(','.join(new_group))
            new_url.append(url[i])
    return new_head, new_url


def combo(file_split, keys, groups):
    '''
    多个关键字生成的组分类合并
    '''
    head = list(file_split)
    url = list(file_split.values())
    heads = []
    urls = []
    for i, v in enumerate(keys):
        new_head, new_url = classify(head, url, v, groups[i])
        heads += new_head
        urls += new_url
    combo_heads_urls = zip(heads, urls)
    return dict(combo_heads_urls)


def check(head,url):
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
            print(f'检测连通性:',head,url, '\033[0;30;42m Online \033[0m', status)
            return True
        else:
            print(f'检测连通性:',head,url, '\033[0;30;43m Timeout \033[0m', status)
            
            return False
    except requests.exceptions.RequestException:
        print(f'检测连通性:',head,url, '\033[0;30;41m Error \033[0m')
        
        return False


def main(url):
    download_iptv_m3u8(url)
    file_split = read_m3u8()
    head_keys = ['CCTV', '卫视', '浙江', 'NewTV', 'SiTV']
    groups = ['央视', '卫视', '本地台', 'NewTV', 'SiTV']
    combo_dict = combo(file_split, head_keys, groups)
    with open('TV.m3u8', 'w', encoding='utf8') as fw:
        fw.write('#EXTM3U'+'\n')
        for key in list(combo_dict.keys()):
            if check(key.split(',')[1],combo_dict[key]):
                fw.write(key+'\n'+combo_dict[key]+'\n')
            else:
                continue


if __name__ == "__main__":
    url = 'https://iptv-org.github.io/iptv/countries/cn.m3u'
    main(url)
