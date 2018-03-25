# -*- coding:utf-8 -*-
import socket
import time
import threading
#import ServerGUI
from Crypto.Cipher import AES
from Tkinter import *
import tkMessageBox
import cPickle

#定义服务器中保存的数据类型
global server
global Shops, UserID, IDMapAddr,IDMapShop,Name,ShopScore,AddrMapID
Shops, UserID = [], []   #用户与商店ID
IDMapAddr = {} # 通过用户ID找到其地址
AddrMapID = {} # 通过用户的地址找到ID
IDMapShop = {} # 由ShopID找到商店实体
Name={} #记录用户名字
ShopScore={} #记录每个商店的评分

# padding算法
BS = 16
pad = lambda s: s + (BS - len(s) % BS) * chr(0)

#解析加密的key
key='1234567890abcdef'
mode=AES.MODE_ECB
cryptor = AES.new(key, mode)


#加密函数
def AESencrypt(plaintext):
	plaintext = pad(plaintext)
	return cryptor.encrypt(plaintext)
#解密函数
def AESdecrypt(ciphertext):
	plaintext = cryptor.decrypt(ciphertext)
	return plaintext.rstrip('\0')


def user_map_mall(UserID):  #寻找用户在哪个商店里
        for shop in Shops:
                if UserID in IDMapShop[shop].customers:
		                return shop
        return False

def shop_exist(UserID):  #判断用户是否已经创建了商店
        if UserID in Shops:
                return True
        else:
                return False


class Server():
        def __init__(self, local_port=21314):
                self.serverstate=False
                self.serveraddr=('localhost',21314)
                self.serverID='1111'
                try:
                        local_IP = 'localhost'
                        local_address = (local_IP, local_port)
                        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        self.s.bind(local_address)
                        window.feedback_message.insert(1.0, 'eMall Server Initialized Successfully!\n')

                except:
                        window.feedback_message.insert(1.0, 'Failed to create Server UDP socket...\n')
                        time.sleep(2)
                        sys.exit()

        # 返回服务器端接收到的消息文本以及源地址
        def receive_message(self):
                mes, addr = self.s.recvfrom(2048)
                text = AESdecrypt(mes)
                window.log_message.insert(1.0,'received: ' + text + ' from ' + str(addr) + '\n')
                return text, addr

        # 服务器向目的地址addr发送mes文本消息
        def send_message(self, mes, addr):
                ciphertext = AESencrypt(mes)
                l=len(ciphertext)
                self.s.sendto(str(l),addr)
                self.s.sendto(ciphertext, addr)
                window.log_message.insert(1.0, mes + ' send to ' + str(addr) + '\n')

        # 处理客户端发来的消息
        def client_command(self, message, address):
                fields = message.split(' ')
                if fields[0] in ['/login', '/shops', '/enter', '/goods', '/customers', '/buy','/leave', '/addgoods', '/grade','/exit']:
                        if fields[0] == '/login':
                                try:
                                        if address in AddrMapID.keys():
                                                self.send_message('There already exist a user', address)
                                        else:
                                                UserID.append(str(address[1]))
                                                IDMapAddr[str(address[1])] = address
                                                AddrMapID[address]=str(address[1])
                                                Name[str(address[1])] = fields[1]
                                                self.send_message('Your ID: ' + str(address[1]) + ' successfully logged in!',address)
                                                window.feedback_message.insert(1.0, fields[1] + ' logged in from ' + str(address) + '\n')
                                except:
                                        self.send_message('Invalid input!\n', address)
                        if fields[0] == '/shops':
                                try:
                                        #AddrMapID[address]
                                        if fields[1] != '+ID':
                                                if len(Shops)==0:
                                                        self.send_message('There has no shop yet,please wait\n',address)
                                                else:
                                                        for i in Shops:
                                                                shop = IDMapShop[i]
                                                                self.send_message('    whith socre' + str(shop.score) + ' criticed by ' + str(shop.critics) + ' people\n',address)
                                                                self.send_message(shop.name + " Belongs to" + Name[shop.name] + '\n', address)
                                        else:
                                                if len(Shops)==0:
                                                        self.send_message('There has no shop yet,please wait\n',address)
                                                else:
                                                        list = sorted(ShopScore.iteritems(), key=lambda asd: asd[1],reverse=False)
                                                        for i in range(0, len(list)):
                                                                shop = IDMapShop[list[i][0]]
                                                                self.send_message('    whith socre' + str(shop.score) + ' criticed by ' + str(shop.critics) + ' people\n',address)
                                                                self.send_message(shop.name + " Blongs to " +Name[shop.name] + '\n', address)
                                except:
                                       self.send_message('Invalid input\n',address)
                        if fields[0] == '/enter':
                                try:
                                        if address in IDMapAddr.values():
                                                if user_map_mall(AddrMapID[address]) ==False:
                                                        if fields[1] in Shops:
                                                                shop=IDMapShop[fields[1]]
                                                                if shop.closed == False:
                                                                        shop=IDMapShop[fields[1]]
                                                                        shop.add_customer(AddrMapID[address])
                                                                        self.send_message('Welcome to '+shop.name+'\n',address)
                                                                        self.send_message('A customer: '+AddrMapID[address]+' entered your shop\n',IDMapAddr[shop.name])
                                                                else:
                                                                        self.send_message('Error:  Shop has been closed..try another',address)
                                                        else:
                                                                self.send_message('Error:  No this room..try another',address)
                                                else:
                                                        self.send_message('Yout have already entered a shop. Leave it first',address)
                                        else:
                                                self.send_message('Login First Please!',address)
                                except:
                                        self.send_message('Invalid input.\n' , address)
                        if fields[0] == '/goods':
                                try:
                                        if user_map_mall(AddrMapID[address]) != False:
                                                shopid = user_map_mall(AddrMapID[address])
                                                thisshop = IDMapShop[shopid]
                                                cshop=cPickle.dumps(thisshop)
                                                self.send_message('Goods',address)
                                                self.send_message(cshop,address)
                                                #top = len(thisshop.goodsNum)
                                                #for i in range(0,top):
                                                #        self.send_message(str(i) + '     ' + thisshop.ID_map_name[i] + '     ' + str(thisshop.ID_map_price[i]) + '     '+str(thisshop.goodsNum[i])+'\n',address)
                                                #self.send_message('ID    Name    Price/$     Number\n', address)
                                                #self.send_message('Goods in this shop are:\n', address)
                                        else:
                                                shopid=AddrMapID[address]
                                                thisshop = IDMapShop[shopid]
                                                cshop = cPickle.dumps(thisshop)
                                                self.send_message('Goods', address)
                                                self.send_message(cshop, address)
                                                #top = len(thisshop.goodsNum)
                                                #for i in range(0, top):
                                                #        self.send_message(str(i) + '     ' + thisshop.ID_map_name[i] + '     ' +str(thisshop.ID_map_price[i]) + '     '+str(thisshop.goodsNum[i])+'\n', address)
                                                #self.send_message('ID    Name    Price/$     Number\n', address)
                                                #self.send_message('Goods in this shop are:\n', address)
                                except:
                                        self.send_message( "You haven't enter a shop yet:\n",address)
                        if fields[0] == '/customers':
                                try:
                                        shopid=user_map_mall(AddrMapID[address])
                                        if shopid in Shops:
                                                thisshop=IDMapShop[shopid]
                                                self.send_message('There are total '+ str(len(thisshop.customers))+ ' customers in'+thisshop.name+ '\n',address)
                                                for i in thisshop.customers:
                                                        if i==self.serverID:
                                                                self.send_message('Administrator \n',address)
                                                        else:
                                                                self.send_message(i + ' with name: ' + Name[i] + '\n',address)
                                        else:
                                                shopid = AddrMapID[address]
                                                thisshop = IDMapShop[shopid]
                                                self.send_message('There are total ' + str(len(thisshop.customers)) + ' customers in ' + thisshop.name + '\n', address)
                                                for i in thisshop.customers:
                                                        if i==self.serverID:
                                                                self.send_message('Administrator \n',address)
                                                        else:
                                                                self.send_message(i + ' with name: ' + Name[i] + '\n',address)
                                except:
                                        self.send_message('You have not enter a shop yet\n',address)
                        if fields[0] == '/buy':
                                try:
                                        shopid=user_map_mall(AddrMapID[address])
                                        thisshop=IDMapShop[shopid]
                                        if thisshop.buy(int(fields[1]),int(fields[2])) == True:
                                                self.send_message('You just bought '+fields[2]+' '+thisshop.ID_map_name[int(fields[1])],address)
                                                self.send_message(Name[AddrMapID[address]]+' just bought '+fields[2]+' '+thisshop.ID_map_name[int(fields[1])],IDMapAddr[shopid])
                                        else:
                                                self.send_message('Failed to buy'+fields[1],address)
                                except:
                                        self.send_message('Enter a shop first',address)
                        if fields[0] == '/leave':
                                try:
                                        shopid=user_map_mall(AddrMapID[address])
                                        shop=IDMapShop[shopid]
                                        shop.leave(AddrMapID[address])
                                        self.send_message('You left '+ str(shopid) +' Welcome next time!',address)
                                except:
                                        self.send_message('Enter a shop first',address)
                        if fields[0] == '/addgoods':
                                try:
                                        shopid=AddrMapID[address]
                                        shop=IDMapShop[shopid]
                                        if shop.addgood(fields[1],fields[2],fields[3])==True:
                                                self.send_message('Add new goods success\n',address)
                                        else:
                                                self.send_message('Goods already exist,update it success\n',address)
                                except:
                                        self.send_message('You do not own a shop\n',address)
                        if fields[0] == '/grade':
                                if shop_exist(fields[1]) == True:
                                        shop = IDMapShop[fields[1]]
                                        shop.critic(int(fields[2]))
                                        self.send_message('You just grade the shop ' + fields[1] + ' with score: ' + fields[2] + '\n',address)
                                else:
                                        self.send_message('Error: No such shop\n',address)
                        if fields[0] == '/exit':
                                if address in IDMapAddr.values():
                                        id=AddrMapID[address]
                                        shopid=user_map_mall(id)
                                        if shopid !=False:
                                                self.client_command('/leave', address)
                                        if id in Shops:
                                                Shops.remove(id)
                                                IDMapShop.pop(id)
                                                ShopScore.pop(id)
                                        AddrMapID.pop(address)
                                        UserID.remove(id)
                                        Name.pop(id)
                                        IDMapAddr.pop(id)
                                else:
                                        self.send_message('Invalid input!\n',address)
                else:
                        self.send_message('Invalid input!', address)

        # 向指定的用户发送通知消息
        def broadcast(self,message,userAddr):
                window.log_message.insert(1.0, 'Broadcasting started\n')
                for addr in userAddr:
                        self.send_message(message, addr)
                window.log_message.insert(1.0, 'Broadcasting... end\n')

        # 处理服务器端输入的消息
        def deal_server_command(self, message):
                window.command_entry.delete(0, END)
                window.error_label['text'] = ''
                fields = message.split(' ')
                if fields[0] in ['/msg', '/opennewshop', '/enter', '/goods', '/customers', '/shops','/users', '/closeshop', '/grade','/leave','/reopen']:
                        if fields[0] == '/msg':
                                try:
                                        i = fields.index(':')
                                        message = ' '.join(fields[i + 1:])
                                        for user in fields[1:i]:
                                                try:
                                                        self.send_message('[Server]:' + message, IDMapAddr[user])
                                                except:
                                                        window.feedback_message.insert(1.0,'Fail to send message to ' + user + '\n')
                                except:
                                        window.error_label['text'] = 'Invalid input.'
                        if fields[0] == '/opennewshop':
                                try:
                                        if shop_exist(fields[1]) == False:
                                                newroom = Shop(fields[1])
                                                if fields[1] not in UserID:
                                                        window.feedback_message.insert(1.0,'Error: there do not exist such a user\n')
                                                else:
                                                        Shops.append(newroom.name)
                                                        IDMapShop[newroom.name]=newroom
                                                        window.feedback_message.insert(1.0,'Successfully created a shop :' + fields[1] + '\n')
                                                        self.send_message('New shop created: ' + fields[1]+' You can manage your shop now' + '\n', IDMapAddr[fields[1]])
                                        else:
                                                window.feedback_message.insert(1.0, 'Error: ' + fields[1] + ' can only open one shop.\n')
                                except:
                                        window.error_label['text'] = 'Invalid input.'
                        if fields[0] == '/enter':
                                try:
                                        if self.serverstate != True:
                                                self.serverstate=True
                                                shop = IDMapShop[fields[1]]
                                                if fields[1] in Shops:
                                                        if shop.closed==False:
                                                                message = 'Administrator joined your shop!'
                                                                address = IDMapAddr[shop.name]
                                                                self.send_message(message, address)
                                                                shop.add_customer(self.serverID)
                                                        else:
                                                                window.error_label[
                                                                        'text'] = 'Error:  Shop has been closed..try another'
                                                else:
                                                        window.error_label[
                                                                'text'] = 'Error:  No this room..try another'
                                        else:
                                                window.error_label['text'] = 'You have joined an shop, leave it first.'
                                except:
                                        window.error_label['text'] = 'Invalid input\n'
                        if fields[0] == '/leave':
                                try:
                                        shopid=user_map_mall(self.serverID)
                                        self.serverstate=False
                                        shop=IDMapShop[shopid]
                                        shop.leave(self.serverID)
                                        self.send_message('Administrator left your shop!\n',IDMapAddr[shop.name])
                                        window.feedback_message.insert(1.0,'You left '+ str(shopid) +' Welcome next time!\n')
                                except:
                                        window.feedback_message.insert(1.0, 'Enter a shop first!\n')
                        if fields[0] == '/goods':
                                try:
                                        shopid=user_map_mall(self.serverID)
                                        thisshop=IDMapShop[shopid]
                                        goods = 'goods in this shop are:\nID    Name    Price/$     Number\n'
                                        top=len(thisshop.goodsNum)
                                        for i in range(0,top):
                                                goods += str(i) + '     ' + thisshop.ID_map_name[i] + '     ' + str(thisshop.ID_map_price[i]) + '         ' + str(thisshop.goodsNum[i]) + '\n'
                                        window.show_info(goods, thisshop.name)
                                except:
                                        window.feedback_message.insert(1.0, "You haven't enter a shop yet.\n")
                        if fields[0] == '/customers':
                                try:
                                        shopid = user_map_mall(self.serverID)
                                        thisshop = IDMapShop[shopid]
                                        window.feedback_message.insert(1.0,'There are total '+ str(len(thisshop.customers))+ ' customers in '+thisshop.name+ '\n')
                                        for i in thisshop.customers:
                                                if i==self.serverID:
                                                        window.feedback_message.insert(1.0, 'Administrator !\n')
                                                else:
                                                        window.feedback_message.insert(1.0, i+' with name: '+Name[i]+'\n')
                                except:
                                        window.feedback_message.insert(1.0, "You haven't enter a shop yet:\n")
                        if fields[0] == '/shops':
                                try:
                                        if fields[1]=='+ID':
                                                if len(Shops)==0:
                                                        window.feedback_message.insert(1.0,'There has no shop yet,please wait\n')
                                                else:
                                                        for i in Shops:
                                                                shop=IDMapShop[i]
                                                                window.feedback_message.insert(1.0,'    whith socre' + str(shop.score) + ' criticed by '+str(shop.critics)+' people\n')
                                                                window.feedback_message.insert(1.0,'Belongto:' + shop.name + " who's name is " +Name[shop.name]+'\n')
                                        else:
                                                if len(Shops)==0:
                                                        window.feedback_message.insert(1.0,'There has no shop yet,please wait\n')
                                                else:
                                                        list=sorted(ShopScore.iteritems(),key=lambda asd:asd[1],reverse=False)
                                                        for i in range(0,len(list)):
                                                                shop = IDMapShop[list[i][0]]
                                                                window.feedback_message.insert(1.0,'    whith socre' + str(shop.score) + ' criticed by ' + str(shop.critics) + ' people\n')
                                                                window.feedback_message.insert(1.0,shop.name + " Belongs to " +Name[shop.name]+'\n')
                                except:
                                        window.feedback_message.insert(1.0,'Invalid input\n')
                        if fields[0] == '/users':
                                if len(UserID) == 0:
                                        window.feedback_message.insert(1.0,'No users yet\n')
                                for user in UserID:
                                        if user_map_mall(user) != False:
                                                window.feedback_message.insert(1.0, user + '('+Name[user]+')' +' is shopping in ' + str(user_map_mall(user)) + '\n')
                                        else:
                                                window.feedback_message.insert(1.0,user + '('+Name[user]+')'+'not enter a shop\n')
                        if fields[0] == '/closeshop':
                                if fields[1] in Shops:
                                        shop=IDMapShop[fields[1]]
                                        shop.close()
                                        window.feedback_message.insert(1.0,'Closing : '+shop.name+'\n')
                                        self.send_message('Your shop shall be closed soon',IDMapAddr[fields[1]])
                                        for i in shop.customers:
                                                if i=='1111':
                                                        self.serverstate = False
                                                        shop.leave(server.serverID)
                                                else:
                                                        self.send_message('Attention : ' + fields[1] + ' is about to close. Please leave soon\n', IDMapAddr[i])
                                                        #shop.leave(i)
                                else:
                                        window.feedback_message.insert(1.0,'This shop do not exist \n')
                        if fields[0] == '/grade':
                                if shop_exist(fields[1]) == True:
                                        shop=IDMapShop[fields[1]]
                                        shop.critic(int(fields[2]))
                                        window.feedback_message.insert(1.0,'You just grade the shop '+fields[1]+' with score: '+fields[2]+'\n')
                                else:
                                        window.feedback_message.insert(1.0,'Error: No such shop\n')
                        if fields[0] == '/reopen':
                                if fields[1] in Shops:
                                        shop=IDMapShop[fields[1]]
                                        if shop.closed==True:
                                                shop.reopen()
                                                window.feedback_message.insert(1.0,'The shop :'+fields[1]+' repopened!\n')
                                                self.send_message('Your shop is reopened!\n',IDMapAddr[fields[1]])
                                        else:
                                                window.feedback_message.insert(1.0,'The shop is open\n')
                                else:
                                        window.feedback_message.insert(1.0,'This shop do not exist\n')
                else:
                        window.error_label['text'] = 'Invalid input!'

class Shop():
        def __init__(self, userID):
                self.name = userID
                self.score = 0
                ShopScore[userID]=self.score
                self.critics = 0
                self.goodsNum = []  #商品ID由0,1,2……统一编号
                self.customers = []
                self.ID_map_name = []
                self.ID_map_price = []
                self.closed = False

        def add_customer(self, user_ID):
                if self.closed==True:
                        return False
                if user_ID not in self.customers:
                        self.customers.append(user_ID)
                        window.feedback_message.insert(1.0, str(user_ID) + ' welcome to ' + self.name + ' Mall\n')
                        return True
                return False

        #赶走商店里的所有顾客
        def remove_customer(self):
                for i in self.customers:
                        self.leave(i)
                        window.feedback_message.insert(1.0, i + ' leave from ' + self.name + '\n')
                return True

        #让指定顾客离开
        def leave(self,userid):
                self.customers.remove(userid)
                window.feedback_message.insert(1.0, userid +' leave from ' + self.name +'\n')

        def critic(self,grade):
                self.score = ((self.score * self.critics) + grade)/(self.critics+1)
                self.critics += 1
                ShopScore[self.name]=self.score

        def buy(self,id,number):
                if id>=len(self.goodsNum):
                        return False
                else:
                        if self.goodsNum[id]<number:
                                return False
                        else:
                                self.goodsNum[id]=self.goodsNum[id]-number
                                return True

        def addgood(self,name,number,price):
                if name in self.ID_map_name:
                        return False
                else:
                        self.goodsNum.append(int(number))
                        self.ID_map_name.append(name)
                        self.ID_map_price.append(int(price))
                        return True

        def close(self):
                self.closed=True

        def reopen(self):
                self.closed=False

# 服务器端图形交互界面
class MainGui():
    def __init__(self):
        self.root = Tk()
        self.root.geometry('400x550+150+100')
        self.root.title('eMall-ServerMode')
        frame=Frame(self.root)
        self.help_button = Button(self.root, text='Help',command=self.show_tips)
        self.help_button.pack()

        self.slogan = Label(self.root, text='Input your command below:',fg='blue')
        self.slogan.pack()
        frame.pack()
        self.command_entry = Entry(frame,bg='LavenderBlush')
        self.command_entry.pack(side=LEFT)

        self.input_button = Button(frame, text='OK',
								   command=lambda: server.deal_server_command(self.command_entry.get()))
        self.input_button.pack(side=RIGHT)

        self.error_label = Label(self.root, text='',fg='red')
        self.error_label.pack()

        self.feedback_message = Text(self.root, height=10, width=40)
        self.feedback_message.pack()

        self.log_label = Label(self.root, text='Application log',fg='BlueViolet')
        self.log_label.pack()

        self.log_message = Text(self.root, height=12, width=40,bg='Ivory')
        self.log_message.pack()

        self.clear_log_button = Button(self.root, text='Clear',
									   command=lambda: self.log_message.delete(1.0, END))
        self.clear_log_button.pack()

        self.exit_button = Button(self.root, text='Exit', command=lambda: sys.exit())
        self.exit_button.pack()

    def show_info(self,message,shopname):
        tkMessageBox.showinfo('Welcom to '+shopname,message)

    def show_tips(self):
        tips = r'''
Commands you should input:
- /msg userID1 userID2 *** : message
    send a message to users you want
- /opennewshop userID
    open a shop for a user
- /enter shopName
    enter a shop already exists
- /goods
    list ID,Name,Price,Number of goods in
	the current shop
- /customers
    list ID,Name of users in current shop
- /shops [+mode]
	shops +ID (show info by ID order)
	shops +S  (show info by Score order)
- /users
    list ID,Name and state of users
- /closeshop shopName
    close a running shop
- /reopen shopName
    and you can reopen a closed shop
- /grade  shopName XX
	critic a shop(/grade 1001 10)
	give shop '1001' with 10 score
Author: ZZB
Version: 3.0'''
        tkMessageBox.showinfo('AuctionOnline-help', tips)

class ListenerThread(threading.Thread):
	def run(self):
		while True:
			data, address = server.receive_message()
			server.client_command(data, address)


window = MainGui()
server = Server()

if __name__ == '__main__':
	listener_thread = ListenerThread()
	listener_thread.setDaemon(True)
	listener_thread.start()
	window.root.mainloop()