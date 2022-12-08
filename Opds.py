import requests
from bs4 import BeautifulSoup
import re
import urllib.parse


class Opds:
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0'}
    book_type = ['application/fb2', 'application/fb2+zip','application/txt+zip', 'application/rtf+zip'\
                'application/epub+zip', 'application/x-mobipocket-ebook', 'application/djvu']


    def __init__(self, url:str):
        self.main_menu = dict()
        self.hop_menu = dict()
        self.old_menu = list()
        self.book_menu = dict()
        self.have_next_hop = True
        r = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(r.text, 'xml')
        main_data = soup.findAll('entry')
        self.main_url = re.match(r'http(s)?://\w*.\w*', url)[0]
        find_searc_url = soup.find('link', href=re.compile(r'.*{searchTerms}'))
        if find_searc_url:
            self.search_url = find_searc_url.get('href').split('{')[0]
            self.have_search = True
        else:
            self.have_search = False


        for data in main_data:
            title = data.find('title').text
            next_url = data.find('link').get('href')
            self.main_menu[title] = next_url

        if self.have_search:
            self.main_menu['search'] = self.search_url

        self.hop_menu = {**self.main_menu}


    def next_hop(self, hop_name:str):
        end_url = str(self.hop_menu.get(hop_name))

        if re.match(r'http(s)?://\w*.\w*', end_url):
            url = end_url
        else:
            url = self.main_url + end_url


        if end_url != None:
            r = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(r.text, 'xml')
            data_entry = soup.findAll('entry')


            self.old_menu.append(self.hop_menu)
            self.hop_menu = dict()
            for data in data_entry:
                title = data.find('title').text
                next_url_all = data.findAll('link')
                if len(next_url_all) > 1:
                    book_url_set = set()
                    for book in next_url_all:
                        if book.get('type') in self.book_type:
                            book_url_set.add((book.get('type').split('/')[1], self.main_url + book.get('href')))


                    if data.find('content') != None and data.find('content').get('type') == 'text':
                        self.hop_menu[title] = next_url_all[0].get('href')

                    if len(book_url_set) > 0:
                        self.book_menu[title] = dict(book_url_set)
                        self.have_next_hop = False

                elif len(next_url_all) == 1:
                    next_url = next_url_all[0].get('href')
                    self.hop_menu[title] = next_url

            return True

        else:
            return False


    def back_hop(self):
        if len(self.old_menu) <= 1:
            self.hop_menu = dict()
            self.old_menu = list()
            self.hop_menu = {**self.main_menu}
        else:
            old = self.old_menu[-1]
            if old == self.hop_menu:
                self.old_menu.pop()
                old = self.old_menu.pop()
                self.hop_menu = dict()
                self.hop_menu = {**old}
            else:
                self.hop_menu = dict()
                self.hop_menu = {**old}

        if self.book_menu != {}:
            self.book_menu = dict()

        self.have_next_hop = True


    def search(self, text:str):
        r_text = urllib.parse.quote_plus(text)
        if re.match(r'http(s)?://\w*.\w*', self.search_url):
            url = self.search_url + r_text
        else:
            url = self.main_url + self.search_url + r_text


        r = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(r.text, 'xml')
        main_data = soup.findAll('entry')

        self.old_menu.append(self.hop_menu)
        self.hop_menu = dict()

        for data in main_data:
            title = data.find('title').text
            next_url = data.find('link').get('href')
            self.hop_menu[title] = next_url


def serch(text):
    url = 'http://opds.su/opds'
    opds = Opds(url)

    opds.search(text)

    while True:
        print(opds.old_menu)
        if opds.have_next_hop:
            next_hop_list = []
            for n, hop in enumerate(opds.hop_menu.keys()):
                next_hop_list.append(hop)
                print(n, hop, opds.hop_menu[hop])

            print('q для выхода и b для возврата')
            next_input = input('следующий шаг: ')

            if next_input == 'q':
                break

            elif next_input == 'b':
                opds.back_hop()
                continue
            else:
                hop_name = next_hop_list[int(next_input)]
                opds.next_hop(hop_name)

        else:
            for name, url in opds.book_menu.items():
                print(name, url)

            print('q для выхода и b для возврата')
            next_input = input('следующий шаг: ')

            if next_input == 'q':
                break

            if next_input == 'b':
                opds.back_hop()
                continue




def main(url):
    opds = Opds(url)

    while True:
        print(len(opds.old_menu))
        if opds.have_next_hop:
            next_hop_list = []
            for n, hop in enumerate(opds.hop_menu.keys()):
                next_hop_list.append(hop)
                print(n, hop)

            print('q для выхода и b для возврата')
            next_input = input('следующий шаг: ')

            if next_input == 'q':
                break

            elif next_input == 'b':
                opds.back_hop()
                continue
            else:
                hop_name = next_hop_list[int(next_input)]
                opds.next_hop(hop_name)

        else:
            for name, url in opds.book_menu.items():
                print(name, url)

            print('q для выхода и b для возврата')
            next_input = input('следующий шаг: ')

            if next_input == 'q':
                break

            if next_input == 'b':
                opds.back_hop()
                continue



if __name__ == '__main__':
    #url = 'http://opds.su/opds'
    url = 'http://flibusta.net/opds'
    text = 'Пушкин'
    #serch(text)
    #opds = Opds(url)
    main(url)


