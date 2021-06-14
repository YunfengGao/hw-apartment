from datetime import datetime, timedelta, timezone
import requests
import sqlite3
import sys
import matplotlib.pyplot as plt


class Data(object):
    def __init__(self, uid, password):
        self.uid = uid
        self.password = password

    def __login(self):
        login_url = 'http://uniportal.huawei.com/uniportal/login.do'
        headers = {}
        login_body = {
            'uid': self.uid,
            'password': self.password,
            'actionFlag': 'loginAuthenticate',
            'lang': 'en'
        }
        session = requests.session()
        response = session.post(login_url, data=login_body, headers=headers, verify=False)
        if 'Your logon site is loading' not in response.content.decode('utf-8'):
            raise Exception('login fail')
        print('login success')
        return session

    def get_apartment(self):
        session = self.__login()
        apartment_url = 'http://app.huawei.com/iadmin/internet/services/forward/dispatch/doPost'
        headers = {'Content-Type': 'application/json'}
        apartment_body = {
            'method': 'GET',
            'url': '/mobile/dispatch/apartment/queryApplyCount/1'
        }
        response = session.post(apartment_url, json=apartment_body, headers=headers, verify=False).json()
        if response is not None and response['returnCode'] == '100':
            return response['dataList']
        raise Exception('get apartment fail')


class Dao(object):
    __db_name = 'hw-apartment.db'

    def create_table(self):
        con = sqlite3.connect(self.__db_name)
        cur = con.cursor()
        cur.execute('create table apartment_details (name text, type text, count integer, date text)')
        cur.close()
        con.commit()
        con.close()

    def insert(self, data):
        con = sqlite3.connect(self.__db_name)
        cur = con.cursor()
        utc_8 = timezone(timedelta(hours=8))
        create_time = datetime.now(tz=utc_8).strftime('%Y-%m-%d %H:%M:%S')
        for row in data:
            cur.execute('insert into apartment_details values (?,?,?,?)',
                        (row['groupName'], row['typeName'], row['orderCount'], create_time))
        cur.close()
        con.commit()
        con.close()

    def get_apartment_status(self, apartment_name, apartment_type):
        con = sqlite3.connect(self.__db_name)
        cur = con.cursor()
        cur.execute('select date, count from apartment_details where name = ? and type = ? order by date',
                    (apartment_name, apartment_type))
        result = cur.fetchall()
        cur.close()
        con.commit()
        con.close()
        return result


class Drawer(object):
    def draw(self, x, y, color, label):
        plt.title('Number of people in line at apartment')
        plt.plot(x, y, color=color, label=label)
        plt.legend()

        plt.xlabel('date')
        plt.ylabel('count')
        plt.savefig('pic.png')
        # plt.show()


def sync_data(argv):
    apartment = Data(argv[1], argv[2]).get_apartment()
    Dao().insert(apartment)


def display_data():
    bcy_normal = Dao().get_apartment_status('百草园公寓', '普通公寓房')
    x = [(bcy_normal[i][0]).split(' ')[0] for i in range(len(bcy_normal))]
    y = [bcy_normal[i][1] for i in range(len(bcy_normal))]
    Drawer().draw(x, y, 'green', 'bcy_normal')


def main(argv):
    # argv[1]:uid
    # argv[2]:password
    if len(argv) <= 1:
        print('usage: python main.py uid password')
        return
    sync_data(argv)
    display_data()


if __name__ == '__main__':
    main(sys.argv)
