import datetime
import requests
import re
import json
import getpass
from bs4 import BeautifulSoup


class UriHook:
    BASE_URL = "https://www.urionlinejudge.com.br"
    RANK = "/judge/pt/users/me"
    LOGIN = "/judge/pt/login"
    HOME = "/judge/pt/"
    UNIVERSITY = ""
    PROFILE = ""
    PROBLEMS = "judge/pt/problems/all"
    PROBLEM = "/judge/pt/problems/index/"
    VIEWS = "/judge/pt/problems/view/"
    ADD = "/judge/pt/runs/add/"
    SUBMISSIONS = "/judge/pt/runs"
    CODE = "/judge/pt/runs/code/"

    def __init__(self, email=None, passw=None):
        self.email = email
        self.passw = passw
        self.session = requests.Session()

    def user_information(self):
        request = self.session.get(self.BASE_URL + self.HOME)
        soup = BeautifulSoup(request.text, "html.parser")
        progress = soup.find('h2').contents[0].replace("%", "")
        request = self.session.get(self.BASE_URL + self.PROFILE)
        soup = BeautifulSoup(request.text, "html.parser")
        name_user = soup.find('div', {'class': 'pb-username'}).find('a').contents[0]
        rankuser = soup.find('ul', {'class': 'pb-information'}).find_all('li')[0].contents[2].strip() \
            .replace('\u00ba', '').replace(',', '').replace('.', '')
        university = soup.find('ul', {'class': 'pb-information'}).find_all('li')[2].find('a').contents[0]
        self.UNIVERSITY = soup.find('ul', {'class': 'pb-information'}).find_all('li')[2].find('a').get('href')
        solved = soup.find('ul', {'class': 'pb-information'}).find_all('li')[4].contents[2].strip()
        trying = soup.find('ul', {'class': 'pb-information'}).find_all('li')[5].contents[2].strip()
        submitted = soup.find('ul', {'class': 'pb-information'}).find_all('li')[6].contents[2].strip()
        request = self.session.get(self.BASE_URL + self.UNIVERSITY)
        soup = BeautifulSoup(request.text, "html.parser")
        rank = soup.find('tr', {'class': 'you-here'})
        rank_value = rank.find(soup.find('tr', {'class': 'medium'}))
        rank_university = rank_value.contents[0]
        result_json = {"user": name_user,
                       "rankUser": int(rankuser),
                       "university": university,
                       "rankUniversity": int(rank_university),
                       "progress": float(progress),
                       "solved": int(solved),
                       "trying": int(trying),
                       "submitted": int(submitted)
                       }
        return json.dumps(result_json)

    def login_uri(self):
        request = self.session.get(self.BASE_URL + self.RANK)
        soup = BeautifulSoup(request.text, "html.parser")
        csrf_token = soup.find('input', {'name': '_csrfToken'}).get('value')
        token_fields = soup.find('input', {'name': '_Token[fields]'}).get('value')
        data = {"_method": "POST",
                "_csrfToken": csrf_token,
                "email": self.email,
                "password": self.passw,
                "remember_me": "0",
                "_Token[fields]": token_fields,
                "_Token[unlocked]": ""
                }
        self.session.post(self.BASE_URL + self.LOGIN, data=data)
        request = self.session.get(self.BASE_URL + self.HOME)
        soup = BeautifulSoup(request.text, "html.parser")
        self.PROFILE = soup.find('ul', {'id': 'menu'}).find_all('a')[1].get('href')
        #TODO Change to Exit
        if 'forum' in self.PROFILE:
            return False
        else:
            return True
    def post_code(self, id_problem, code, language=5):
        request = self.session.get(self.BASE_URL + self.ADD + str(id_problem))
        soup = BeautifulSoup(request.text, "html.parser")
        csrf_token = soup.find('input', {'name': '_csrfToken'}).get('value')
        token_fields = soup.find('input', {'name': '_Token[fields]'}).get('value')
        data = {"_method": "POST",
                "_csrfToken": csrf_token,
                "problem_id":id_problem,
                "language_id":language,
                "template":1,
                "source_code":code,
                "_Token[fields]": token_fields,
                "_Token[unlocked]": ""
                }
        request = self.session.post(self.BASE_URL + self.ADD + str(id_problem), data=data)
        soup = BeautifulSoup(request.text, "html.parser")
        success =  soup.find('div', {'class': 'flash-success'}).contents[0]
        str_date = request.headers['Date'].replace(',','')[:-4]
        date = datetime.datetime.strptime(str_date, "%a %d %b %Y %H:%M:%S")
        return success, date
        
    def is_autenticated(self):
        request = self.session.get(self.BASE_URL + self.HOME)
        soup = BeautifulSoup(request.text, "html.parser")
        self.PROFILE = soup.find('ul', {'id': 'menu'}).find_all('a')[1].get('href')
        if 'forum' in self.PROFILE:
            return False
        else:
            return True

    def get_problem(self, id_problem, json_format=True):
        request = self.session.get(self.BASE_URL + self.PROBLEM + str(id_problem))
        soup = BeautifulSoup(request.text, "html.parser")
        data = list()
        finish = int(soup.find('div', {'id': 'table-info'}).contents[0][-1])
        for i in range(1, finish+1):
            for item in soup.find('tbody').find_all('tr'):
                if'colspan' in str(item):
                    break
                temp_data = {"id": int(item.find('td').find('a').contents[0]),
                             "name": item.find('td', {'class': 'large'}).find('a').contents[0],
                             "subject": item.find_all('td', {'class': 'large'})[1].contents[0].strip(),
                             "resolved": int(item.find('td', {'class': 'small'}).contents[0].strip().replace(',', '').replace('.', '')),
                             "level": str(item.find_all('td', {'class': 'tiny'})[1].contents[0]),
                             "done": len(item.find('td', {'class': 'tiny'}).contents) > 1
                             }
                data.append(temp_data)
            if i < finish:
                request = self.session.get(self.BASE_URL + self.PROBLEM + str(id_problem) + "?page=" + str(i+1))
                soup = BeautifulSoup(request.text, "html.parser")
        if json_format:
            return json.dumps(data, indent=4, ensure_ascii=False)
        else:
            return data

    def get_all_problem(self):
        data = list()
        for i in range(1, 9):
            data.extend(self.get_problem(i, False))
        return json.dumps(data, ensure_ascii=False, indent=4)


    def get_submissions_id(self, id_problem, json_format=True):
        request = self.session.get(self.BASE_URL + self.SUBMISSIONS)
        soup = BeautifulSoup(request.text, "html.parser")
        data = list()
        tablePages = int(soup.find('div', {'id': 'table-info'}).contents[0][-1])
        for i in range(1, tablePages+1):
            for item in soup.find('tbody').find_all('tr'):
                idMatch = int(item.find_all('td', {'class': 'tiny'})[0].find('a').contents[0])
                sub_date = str(item.find_all('td', {'class': 'center'})[1].contents[0]).strip()
                if'colspan' in str(item):
                    break
                if(idMatch == id_problem):
                    temp_data = {"id": int(item.find('td').find('a').contents[0]),
                                 "problemId": idMatch,
                                 "problemName": str(item.find('td', {'class': 'wide'}).find('a').contents[0]),
                                 #"answer": str(item.find('td', {'class': 'semi-wide answer a-1'}).find('a').contents[0]),
                                 "language": str(item.find_all('td', {'class': 'center'})[0].contents[0]),
                                 "time": float(item.find_all('td', {'class': 'tiny'})[1].contents[0]),
                                 "date": sub_date
                             }
                    data.append(temp_data)
            if i < tablePages:
                request = self.session.get(self.BASE_URL + self.SUBMISSIONS)
                soup = BeautifulSoup(request.text, "html.parser")
        if json_format:
            return json.dumps(data, ensure_ascii=False,indent=4)
        else:
            return data
        
    def get_submissions(self, id_problem, timestamp, json_format=True):
        request = self.session.get(self.BASE_URL + self.SUBMISSIONS)
        soup = BeautifulSoup(request.text, "html.parser")
        data = list()
        tablePages = int(soup.find('div', {'id': 'table-info'}).contents[0][-1])
        for i in range(1, tablePages+1):
            for item in soup.find('tbody').find_all('tr'):
                idMatch = int(item.find_all('td', {'class': 'tiny'})[0].find('a').contents[0])
                id_sub = int(item.find('td').find('a').contents[0])
                sub_date = str(item.find_all('td', {'class': 'center'})[1].contents[0]).strip()
                answer = str( item.find_all( 'a', {'href': self.CODE + str(id_sub) })[1].contents[0])
                if'colspan' in str(item):
                    break
                if(idMatch == id_problem):
                    temp_data = {"id": id_sub,
                                 "problemId": idMatch,
                                 "problemName": str(item.find('td', {'class': 'wide'}).find('a').contents[0]),
                                 "answer": answer,
                                 "language": str(item.find_all('td', {'class': 'center'})[0].contents[0]).strip(),
                                 "time": float(item.find_all('td', {'class': 'tiny'})[1].contents[0]),
                                 "date": sub_date
                             }
                    return json.dumps(temp_data, indent=4, ensure_ascii=False)
            if i < tablePages:
                request = self.session.get(self.BASE_URL + self.SUBMISSIONS)
                soup = BeautifulSoup(request.text, "html.parser")
        
    def get_code(self, file):
        f = open(file, 'r')
        return f.read()
if __name__ == '__main__':
    TEST = True
    if TEST:
        user = UriHook("erickmenezes93@hotmail.com", "teste123")
        user.login_uri()
        print('Conectado')
        print('Pegar Problemas Iniciates')
        print(user.get_problem(1))
        print('Postar Código Errado')
        code = user.get_code('E1001.py')
        print(code)
        message, date = user.post_code(1001, code)
        print(message)
        date = date.strftime("%d/%m/%y %H:%M:%S")
        print(user.get_submissions(1001,date))
        print('Postar Código Correto')
        code = user.get_code('1001.py')
        print(code)
        message, date = user.post_code(1001, code)
        print(message)
        date = date.strftime("%d/%m/%y %H:%M:%S")
        print(user.get_submissions(1001,date))  
