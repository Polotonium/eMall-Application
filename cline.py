# -*- coding:utf-8 -*-
import socket
import threading
import random
from Tkinter import *
import tkMessageBox
from Crypto.Cipher import AES
import cPickle

global ShopScore
ShopScore={} #记录每个商店的评分

global client
ServerIP = '127.0.0.1'
ServerPort = 21314

# padding算法
BS = 16
pad = lambda s: s + (BS - len(s) % BS) * chr(0)

#解析加密的key
key='1234567890abcdef'
mode=AES.MODE_ECB
encryptor = AES.new(key, mode)
decryptor = AES.new(key, mode)


#加密函数
def AESencrypt(plaintext):
	plaintext = pad(plaintext)
	return encryptor.encrypt(plaintext)
#解密函数
def AESdecrypt(ciphertext):
	plaintext = decryptor.decrypt(ciphertext)
	return plaintext.rstrip('\0')

global window

class MainGui():
	def __init__(self):
		self.root = Tk()
		self.root.geometry('400x250+150+300')
		self.root.title('eMall-ClientMode')

		self.help_button = Button(self.root, text='Help',command=self.show_tips)
		self.help_button.pack(side=TOP)

		frame=Frame(self.root)

		self.slogan = Label(self.root, text='Input your command below:',fg='blue')
		self.slogan.pack()
		frame.pack()
		self.command_entry = Entry(frame,bg='LavenderBlush')
		self.command_entry.pack(side=LEFT)

		self.send_button = Button(frame, text='Send',
								  command=lambda: client.send_message(self.command_entry.get()))
		self.send_button.pack(side=RIGHT)

		self.server_message = Text(self.root, height=7, width=40,bg='Ivory')
		self.server_message.pack()

		self.exit_button = Button(self.root, text='Exit', command=lambda: self.close())
		self.exit_button.pack()

	def close(self):
		client.send_message('/exit')
		sys.exit()

	def show_info(self,message,shopname):
		tkMessageBox.showinfo('Welcom to '+shopname,message)

	def show_tips(self):

		tips = r'''
Commands you should input:
- /login UserName
	youraddress should not exists in this eMall
- /shops [+mode]
	shops +ID (show info by ID order)
	shops +S  (show info by Score order)
- /enter shopID
	enter a shop already exists
- /goods
	list ID,Name,Price,Number of goods in
		the current shop or your own shop
- /customers
	list ID,Name of users in current shop
	or your own shop
- /buy goodsID number
	buy one kind of good at a time
- /leave
	leave the current shop
- /addgoods Name number price
	add one kind of good at a time
- /grade shopName XX
	critic a shop(/grade 1001 10)
	give shop '1001' with 10 score
Author: ZZB
Version: 3.0'''
		tkMessageBox.showinfo('eMall-help', tips)


window = MainGui()


class Client():
	def __init__(self, server_IP, server_port):
		try:
			self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			client_IP = '127.0.0.1'
			client_port = random.randint(10000, 65535)
			self.s.bind((client_IP, client_port))
			self.server_address = (server_IP, server_port)
			window.server_message.insert(END, 'Client initialized successfully!\n')
		except:
			sys.exit()

	def receive_message(self):
		l, client_address = self.s.recvfrom(1024)
		message,client_address=self.s.recvfrom(int(l))
		plaintext = AESdecrypt(message)
		if plaintext=='Goods':
			l, client_address = self.s.recvfrom(1024)
			shop, client_address = self.s.recvfrom(int(l))
			self.deal(AESdecrypt(shop))
		else:
			window.server_message.insert(1.0, plaintext + '\n')

	def deal(self,sshop):
		shop=cPickle.loads(sshop)
		top = len(shop.goodsNum)
		goods = 'goods in this shop are:\nID    Name    Price/$     Number\n'
		for i in range(0,top):
			goods+=str(i) + '     ' + shop.ID_map_name[i] + '     ' + str(shop.ID_map_price[i]) + '         '+str(shop.goodsNum[i])+'\n'
		window.show_info(goods,shop.name)

	def send_message(self, message):
		ciphertext = AESencrypt(message)
		self.s.sendto(ciphertext, self.server_address)
		window.command_entry.delete(0, END)

class Shop():
	def __init__(self, userID):
		self.name = userID
		self.score = 0
		ShopScore[userID] = self.score
		self.critics = 0
		self.goodsNum = []  # 商品ID由0,1,2……统一编号
		self.customers = []
		self.ID_map_name = []
		self.ID_map_price = []
		self.closed = False

	def add_customer(self, user_ID):
		if self.closed == True:
			return False
		if user_ID not in self.customers:
			self.customers.append(user_ID)
			window.feedback_message.insert(1.0, str(user_ID) + ' welcome to ' + self.name + ' Mall\n')
			return True
		return False

	# 赶走商店里的所有顾客
	def remove_customer(self):
		for i in self.customers:
			self.leave(i)
			window.feedback_message.insert(1.0, i + ' leave from ' + self.name + '\n')
		return True

	# 让指定顾客离开
	def leave(self, userid):
		self.customers.remove(userid)
		window.feedback_message.insert(1.0, userid + ' leave from ' + self.name + '\n')

	def critic(self, grade):
		self.score = ((self.score * self.critics) + grade) / (self.critics + 1)
		self.critics += 1
		ShopScore[self.name] = self.score

	def buy(self, id, number):
		if id >= len(self.goodsNum):
			return False
		else:
			if self.goodsNum[id] < number:
				return False
			else:
				self.goodsNum[id] = self.goodsNum[id] - number
				return True

	def addgood(self, name, number, price):
		if name in self.ID_map_name:
			return False
		else:
			self.goodsNum.append(int(number))
			self.ID_map_name.append(name)
			self.ID_map_price.append(int(price))
			return True

	def close(self):
		self.closed = True

	def reopen(self):
		self.closed = False

class ListenerThread(threading.Thread):
	def run(self):
		while True:
			client.receive_message()

client = Client(ServerIP, ServerPort)

if __name__ == '__main__':
	listener_thread = ListenerThread()
	listener_thread.setDaemon(True)
	listener_thread.start()
	window.root.mainloop()



