"""
Copyright 2018 YoongiKim

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""


from tkinter import filedialog
from tkinter import *
import os
import requests
import shutil
from multiprocessing import Pool
import argparse
from collect_links import CollectLinks
import imghdr


class Sites:
    GOOGLE = 1
    NAVER = 2
    GOOGLE_FULL = 3
    NAVER_FULL = 4
    DAUM = 5
    DAUM_FULL = 6

    @staticmethod
    def get_text(code):
        #인스턴스 변수와 비교하여 code에 해당하는 사이트를 문자열로 반환
        if code == Sites.GOOGLE: #if문을 통해 비교 후 문자열 반환
            return 'google'
        elif code == Sites.NAVER:
            return 'naver'
        elif code == Sites.GOOGLE_FULL:
            return 'google'
        elif code == Sites.NAVER_FULL:
            return 'naver'
        elif code == Sites.DAUM or code == Sites.DAUM_FULL:
            return 'daum'

    @staticmethod
    def get_face_url(code):
        #인스턴스 변수와 비교하여 code에 해당하는 사이트의 얼굴 검색을
        #할 수 있는 url을 문자열로 반환
        if code == Sites.GOOGLE or Sites.GOOGLE_FULL: # if문을 통해 비교 후 반환
            return "&tbs=itp:face"
        if code == Sites.NAVER or Sites.NAVER_FULL:
            return "&face=1"
        if code == Sites.DAUM or Sites.DAUM_FULL:
            return "&FaceType=y"


class AutoCrawler:
    def __init__(self, skip_already_exist=True, n_threads=4, do_google=True, do_naver=True, do_daum=True, download_path='download',
                 full_resolution=False, face=False, maxNum=100):
        """
        :param skip_already_exist: Skips keyword already downloaded before. This is needed when re-downloading.
        :param n_threads: Number of threads to download.
        :param do_google: Download from google.com (boolean)
        :param do_naver: Download from naver.com (boolean)
        :param download_path: Download folder path
        :param full_resolution: Download full resolution image instead of thumbnails (slow)
        :param face: Face search mode
        """

        #매개변수로 인스턴스 변수 초기화
        self.skip = skip_already_exist
        self.n_threads = n_threads
        self.do_google = do_google
        self.do_naver = do_naver
        self.do_daum = do_daum # 추가코드
        self.download_path = download_path
        self.full_resolution = full_resolution
        self.face = face
        self.maxNum = maxNum

        #download_path에 입력된 경로로 디렉토리 생성
        if self.download_path =='download':
            os.makedirs('./{}'.format(self.download_path), exist_ok=True)
            print(self.download_path)
        else:
            print(self.download_path)
    @staticmethod
    def all_dirs(path):
        paths = [] # 리스트를 생성한다.
        for dir in os.listdir(path): # path 내의 파일 리스트로 반복문을 수행
            if os.path.isdir(path + '/' + dir): # 해당 파일이 디렉토리라면,
                paths.append(path + '/' + dir) # 리스트에 append

        return paths # 리스트 반환

    @staticmethod
    def all_files(path):
        paths = [] # 리스트를 생성한다.
        
        # path 경로 내의 시작 디렉토리부터 하위 디렉토리까지 반복문 수행
        for root, dirs, files in os.walk(path): 
            for file in files: # files 리스트를 반복문 수행
                if os.path.isfile(path + '/' + file): # file이 파일 이라면,
                    paths.append(path + '/' + file) # 리스트에 append

        return paths # 리스트 반환

    @staticmethod
    def get_extension_from_link(link, default='jpg'):
        splits = str(link).split('.') # link를 '.'을 기준으로 리스트로 분리
        if len(splits) == 0: # 분리된 리스트의 길이가 0이라면, 확장자 명이 적혀있지 않으므로,
            return default # default 반환
        ext = splits[-1].lower() # 분리된 리스트의 가장 끝 인덱스(-1)을 소문자로 변환
        
        # 각 확장자명에 해당하는 문자열을 반환
        if ext == 'jpg' or ext == 'jpeg': # 'jpeg'라면 'jpg'로 반환
            return 'jpg'
        elif ext == 'gif':
            return 'gif'
        elif ext == 'png':
            return 'png'
        else:
            return default # 해당하는 확장자명 없다면 default로 반환

    @staticmethod
    def validate_image(path):
        # imghdr.what() 메소드를 이용하여 이미지 유형 판단
        # 이미지 검사가 성공하면 이미지 유형이 문자열로 반환, 실패하면 None 반환
        ext = imghdr.what(path)
        
        if ext == 'jpeg': # 'jpeg'라면 'jpg'로 변환
            ext = 'jpg'
        return ext # 이미지 유형 반환

    @staticmethod
    def make_dir(dirname):
        # dirname은 인스턴스 변수 download_path에 저장된 경로 내에
        # 입력된 키워드를 이름으로 가지는 디렉토리의 경로이다.
        
        # current_path에 os.getcwd()를 사용하여 현재 디렉토리 경로를 저장한다.
        current_path = os.getcwd()
        # os.path.join을 사용하여 current_path와 dirname 두개의 경로를 병합한다. 
        path = os.path.join(current_path, dirname)
        if not os.path.exists(path): # 해당 경로가 존재하지 않는다면,
            os.makedirs(path) # 해당 경로의 디렉토리를 만든다.

    @staticmethod
    def get_keywords(keywords_file='keywords.txt'):
        
        # 'keywords.txt' 파일을 읽기 모드로 열어서 그 내용을 keywords에 저장한다.
        with open(keywords_file, 'r', encoding='utf-8-sig') as f:
            text = f.read() # 파일을 읽는다.
            lines = text.split('\n') # '\n'을 기준으로 분리한다.
            # lines의 각 항목이 공백이 아니고 None이 아닌 경우를 반환한다.
            lines = filter(lambda x: x != '' and x is not None, lines)
            keywords = sorted(set(lines)) # lines를 집합자료형으로 정렬하여 반환한다.

        # 입력된 키워드의 개수와 목록을 출력한다.
        print('{} keywords found: {}'.format(len(keywords), keywords))

        # 정렬된 키워드로 다시 'keywords.txt'에 저장한다.
        with open(keywords_file, 'w+', encoding='utf-8') as f:
            for keyword in keywords:
                f.write('{}\n'.format(keyword))

        return keywords # keywords를 반환한다.

    @staticmethod
    def save_object_to_file(object, file_path):
        try:
            # file_path를 'wb'로 연다.
            with open('{}'.format(file_path), 'wb') as file:
                # shutil.copyfileobj() 를 이용하여 object.raw(raw 데이터)를 file로 복사한다.
                # shutil.copyfileobj()는 데이터를 chunk로 복사한다.
                shutil.copyfileobj(object.raw, file) 
                
        except Exception as e:
            print('Save failed - {}'.format(e)) # 예외 처리
        

    def download_images(self, keyword, links, site_name):
        # download_path 경로 내에 keyword에 저장된 이름의 디렉토리를 만든다.
        self.make_dir('{}/{}'.format(self.download_path, keyword))
        total = len(links) # links에 길이를 total에 저장한다.

        # links 반복문을 수행한다. enumerate 함수를 사용하였기 때문에, index에는 각각의 순서 인덱스가 저장된다.
        for index, link in enumerate(links): 
            try:
                print('Downloading {} from {}: {} / {}'.format(keyword, site_name, index + 1, total))
                response = requests.get(link, stream=True) # 해당 link를 이용하여 응답 객체를 반환한다.
                ext = self.get_extension_from_link(link) # link로부터 확장자명을 반환한다.
                
                # 파일을 저장할 경로를 만든다. zfill은 문자열 앞을 0으로 채워준다.
                no_ext_path = '{}/{}/{}_{}'.format(self.download_path, keyword, site_name, str(index).zfill(4))
                path = no_ext_path + '.' + ext # no_ext_path 뒤에 ext(확장자명)을 추가하여 path 경로를 만든다.
                self.save_object_to_file(response, path) # save_object_to_file을 수행하여 파일을 다운로드한다.

                del response # response 변수 제거

                ext2 = self.validate_image(path) # validate_image를 수행하여 이미지의 유형을 반환한다.
                if ext2 is None: # 이미지 유형 검사에 실패하였다면(None 이라면),
                    print('Unreadable file - {}'.format(link))
                    os.remove(path) # 해당 경로의 파일을 삭제한다.
                else:
                    if ext != ext2: # 기존에 추출했던 확장자명(ext)과 새로 추출한 확장자명(ext2)가 다르다면,
                        path2 = no_ext_path + '.' + ext2 # path2에 ext2로 확장자명을 가지는 새로운 경로를 만들고
                        os.rename(path, path2) # path를 path2로 이름을 변경해준다.
                        print('Renamed extension {} -> {}'.format(ext, ext2))

            except Exception as e:
                print('Download failed - ', e) 
                continue # 예외가 발생하였다면, 내용을 출력해주고 continue(계속 진행)한다.

    def download_from_site(self, keyword, site_code):
        site_name = Sites.get_text(site_code) # site_code를 이용하여 사이트이름을 반환한다.
        # face 모드가 True였다면 얼굴 검색이 가능한 url을 반환하고, False였다면 공백을 저장한다.
        add_url = Sites.get_face_url(site_code) if self.face else "" 

        try:
            collect = CollectLinks(self.maxNum)  # CollectLinks 객체를 생성한다.
        except Exception as e:
            print('Error occurred while initializing chromedriver - {}'.format(e)) # 예외 발생시 종료
            return

        try:
            print('Collecting links... {} from {}'.format(keyword, site_name))

            # site_code에 해당하는 collect 객체의 메소드를 수행하여 link 데이터를 수집하여 links에 반환한다.
            print('시작')
            if site_code == Sites.GOOGLE:
                links = collect.google(keyword, add_url)

            elif site_code == Sites.NAVER:
                links = collect.naver(keyword, add_url)

            elif site_code == Sites.GOOGLE_FULL:
                links = collect.google_full(keyword, add_url)

            elif site_code == Sites.NAVER_FULL:
                links = collect.naver_full(keyword, add_url)

            elif site_code == Sites.DAUM:
                links = collect.daum(keyword, add_url)

            elif site_code == Sites.DAUM_FULL:
                links = collect.daum_full(keyword, add_url)

            else:
                print('Invalid Site Code')
                links = [] # site_code가 유효하지않다면 links는 비어있다.

            print('종료')
            print('Downloading images from collected links... {} from {}'.format(keyword, site_name))
            # 수집된 데이터 links로 download_images 메소드를 수행하여 이미지를 다운로드 한다.
            self.download_images(keyword, links, site_name) 

            print('Done {} : {}'.format(site_name, keyword)) # 다운로드가 완료된 사이트 명과 검색어를 출력한다.

        except Exception as e:
            print('Exception {}:{} - {}'.format(site_name, keyword, e)) # 예외발생 시 사이트명, 키워드, 예외 내용 출력

                

    def download(self, args):
        # args에 저장된 데이터로 download_from_site 메소드 수행
        self.download_from_site(keyword=args[0], site_code=args[1]) 

    def do_crawling(self):
        keywords = self.get_keywords() # get_keywords 메소드를 수행하여 키워드들을 반환한다.

        tasks = [] # 각 task(하나의 크롤링 수행 단위)들을 저장하는 리스트

        for keyword in keywords: # 각 keyword로 반복문을 수행한다.
            dir_name = '{}/{}'.format(self.download_path, keyword) # download_path와 keyword를 이용하여 경로를 만든다.

            # 해당 경로가 이미 존재하고 skip 옵션이 True라면 continue 한다.
            if os.path.exists(os.path.join(os.getcwd(), dir_name)) and self.skip: 
                print('Skipping already existing directory {}'.format(dir_name))
                continue

            if self.do_google: # do_google이 True
                # full_resolution이 True 또는 False라면 해당하는 검색어와 사이트 코드를 tasks에 넣어준다.
                if self.full_resolution: 
                    tasks.append([keyword, Sites.GOOGLE_FULL])
                else:
                    tasks.append([keyword, Sites.GOOGLE])

            if self.do_naver: # do_naver가 True
                # full_resolution이 True 또는 False라면 해당하는 검색어와 사이트 코드를 tasks에 넣어준다.
                if self.full_resolution: # full 옵션을 확인하여 해당하는 검색어와 사이트 코드를 tasks에 넣어준다.
                    tasks.append([keyword, Sites.NAVER_FULL])
                else:
                    tasks.append([keyword, Sites.NAVER])

            if self.do_daum: # do_daum가 True
                # full_resolution이 True 또는 False라면 해당하는 검색어와 사이트 코드를 tasks에 넣어준다.
                if self.full_resolution: # full 옵션을 확인하여 해당하는 검색어와 사이트 코드를 tasks에 넣어준다.
                    tasks.append([keyword, Sites.DAUM_FULL])
                else:
                    tasks.append([keyword, Sites.DAUM])

        pool = Pool(self.n_threads) # n_threads의 개수를 가지는 프로세스 풀을 생성한다.

        # self.download 메소드와 tasks를 인자로 넘겨주는 map_asynk를 실행하여
        # 프로세스별로 크롤링 및 다운로드를 수행한다.
        pool.map_async(self.download, tasks)
        pool.close() # 리소스 낭비를 방지하기 위해 close
        pool.join() # pool이 다 종료될 때까지(작업이 다 완료될 때까지) 기다린다.
        print('Task ended. Pool join.')

        self.imbalance_check() # imbalance_check 메소드(데이터 불균형 감지)를 수행한다.

        print('End Program') # 프로그램이 종료된다.

    def imbalance_check(self):
        print('Data imbalance checking...')

        dict_num_files = {}

        for dir in self.all_dirs(self.download_path): # download_path의 디렉토리들 반복문 수행
            n_files = len(self.all_files(dir)) # 해당 디렉토리의 파일 개수 저장
            dict_num_files[dir] = n_files # 해당 디렉토리의 파일 개수를 dick_num_files에 저장

        avg = 0
        for dir, n_files in dict_num_files.items(): # dict_num_files 반복문 수행
            avg += n_files / len(dict_num_files) # 디렉토리들의 파일 평균 개수 계산
            print('dir: {}, file_count: {}'.format(dir, n_files))

        dict_too_small = {}

        # 디렉토리의 파일 개수가 평균의 절반보다 낮다면, dict_too_small에 저장
        for dir, n_files in dict_num_files.items(): 
            if n_files < avg * 0.5:
                dict_too_small[dir] = n_files

        if len(dict_too_small) >= 1: # dict_too_small에 저장된 디렉토리가 1개 이상 있다면,
            for dir, n_files in dict_too_small.items():
                print('Data imbalance detected.')
                print('Below keywords have smaller than 50% of average file count.')
                print('I recommend you to remove these directories and re-download for that keyword.')
                print('_________________________________')
                print('Too small file count directories:')
                print('dir: {}, file_count: {}'.format(dir, n_files)) # 불균형 감지된 디렉토리 출력

            print("Remove directories above? (y/n)")
            answer = input() # 해당 디렉토리를 삭제할지 결정('y' 또는 'n' 입력)

            if answer == 'y': # 'y' 입력했다면,
                
                print("Removing too small file count directories...")
                for dir, n_files in dict_too_small.items(): # 각 디렉토리 삭제
                    shutil.rmtree(dir) # shutil.rmtree 이용하여 각 디렉토리와 그 하위 디렉토리 모두 삭제
                    print('Removed {}'.format(dir))

                print('Now re-run this program to re-download removed files. (with skip_already_exist=True)')
        else:
            print('Data imbalance not detected.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser() # 파서 객체 생성

    # 인자에 대한 정보 추가
    parser.add_argument('--skip', type=str, default='true', help='Skips keyword already downloaded before. This is needed when re-downloading.')
    parser.add_argument('--threads', type=int, default=4, help='Number of threads to download.')
    parser.add_argument('--google', type=str, default='true', help='Download from google.com (boolean)')
    parser.add_argument('--naver', type=str, default='true', help='Download from naver.com (boolean)')
    parser.add_argument('--daum', type=str, default='true', help='Download from daum.net (boolean)') # 추가코드
    parser.add_argument('--full', type=str, default='false', help='Download full resolution image instead of thumbnails (slow)')
    parser.add_argument('--face', type=str, default='false', help='Face search mode')
    parser.add_argument('--downNum', type = int, required=True , default = 10000, help = 'Max Number of images to downlad')
    # 명령행을 검사하여 인자 파싱
    args = parser.parse_args()

    # 파싱된 데이터로 옵션에 관한 각 변수 초기화
    _skip = False if str(args.skip).lower() == 'false' else True
    _threads = args.threads
    _google = False if str(args.google).lower() == 'false' else True
    _naver = False if str(args.naver).lower() == 'false' else True
    _daum = False if str(args.daum).lower() == 'false' else True # 추가코드
    _full = False if str(args.full).lower() == 'false' else True
    _face = False if str(args.face).lower() == 'false' else True
    _maxNum = args.downNum

    root = Tk()
    dirname = filedialog.askdirectory()
    re_dirname = dirname.replace("/", "\\")

    
    #download_path= root.dirname, 

    # 선택된 옵션 출력
    print('Options - skip:{}, threads:{}, google:{}, naver:{}, daum:{}, full_resolution:{}, face:{}, downNum:{}'.format(_skip, _threads, _google, _naver, _daum, _full, _face, _maxNum))

    # 옵션에 관한 각 변수로 AutoCrawler 객체 생성
    crawler = AutoCrawler(skip_already_exist=_skip, n_threads=_threads, do_google=_google, do_naver=_naver, do_daum=_daum, download_path= re_dirname, full_resolution=_full, face=_face, maxNum=_maxNum)
    crawler.do_crawling() # do_crawling() 수행
