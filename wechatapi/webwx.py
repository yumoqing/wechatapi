import xml
import ramdom
import time

from httpapi import HttpClient, RESPONSE_TEXT, RESPONSE_BIN, 
from httpapi import RESPONSE_JSON, RESPONSE_FILE

class WebWX(HttpClient):
	def __init__(self,appid='wx782c26e4c19acffb',lang='zh_CN'):
		HttpClient.__init__(self,coding='utf-8')
		self.appid = appid
		self.lang = lang
		self.uuid = None
		self.base_uri = None
		self.check_login_period = 0
		self.deviceId = 'e' + repr(random.random())[2:17]
		
	async def getUUID(self):
		data = {
			"appid":self.appid,
			"fun":"new",
			"lang":self.lang,
			"_": int(time.time())
		}
		txt = await self.post("https://wx.qq.com/jslogin",data=data)
		regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"'
		pm = re.search(regx, data)
		if pm:
			code = pm.group(1)
			uuid = pm.group(2)
			if code == '200':
				self.uuid = uuid
				return True
		return False
	
	async def getQRCode(self):
		url = 'https://wx.qq.com/qrcode/' + self.uuid
		qrimg = await self.get(url,method=RESPONSE_BIN)
		return qrimg

	async def checkLoginStatus(self):
		params = {
			"tip":self.check_login_period,
			"uuid":self.uuid,
			"_":int(time.time()),
			"loginicon":"true"
		}
		url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/login'
		data = await self.get(url,params=params.RESPONSE_JSON)
		code = data['window.code']
                if code == '201':
                        self.login_status = True
			self.userAvatar = data['window.userAvatar']
                        return True
                elif code == '200':
                        url = data['window.redirect_uri']
                        r_uri = url + '&fun=new'
                        self.redirect_uri = r_uri
                        self.base_uri = r_uri[:r_uri.rfind('/')]
                        self.login_status = True
                        return
                elif code == '408':
                        self.uuid = ''
                else:
                        self.uuid = ''
                return

	async def login(self,url):
		data = await self.get(self.redirect_uri)
		if data == '':
			return False
		doc = xml.dom.minidom.parseString(data)
		root = doc.documentElement
		for node in root.childNodes:
			if node.nodeName == 'skey':
				self.skey = node.childNodes[0].data
			elif node.nodeName == 'wxsid':
				self.sid = node.childNodes[0].data
			elif node.nodeName == 'wxuin':
				self.uin = node.childNodes[0].data
			elif node.nodeName == 'pass_ticket':
				self.pass_ticket = node.childNodes[0].data

		if '' in (self.skey, self.sid, self.uin, self.pass_ticket):
			return False
		self.BaseRequest = {
			'Uin': int(self.uin),
			'Sid': self.sid,
			'Skey': self.skey,
			'DeviceID': self.deviceId,
		}
		return True

	async def webwxinit(self):
		url = 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxinit'
		url = url + '?pass_ticket=%s&skey=%s&r=%s' % (self.pass_ticket,\
				self.skey, int(time.time()))
		data = {
			"BaseRequest":self.BaseRequest
		}
		d = self.post(url,data=data,method=RESPONSE_JSON)
		self.SyncKey = d['SyncKey']
		self.User = d['User']
		# synckey for synccheck
		self.synckey = '|'.join(
			[str(keyVal['Key']) + '_' + str(keyVal['Val']) for keyVal in self.SyncKey['List']])

		return d['BaseResponse']['Ret'] == 0


	async def webwxstatusnotify(self):
		url = self.base_uri + \
			'/webwxstatusnotify?lang=zh_CN&pass_ticket=%s' % (self.pass_ticket)
		params = {
			'BaseRequest': self.BaseRequest,
			"Code": 3,
			"FromUserName": self.User['UserName'],
			"ToUserName": self.User['UserName'],
			"ClientMsgId": int(time.time())
		}
		dic = await self.post(url, params)
		if dic == '':
			return False

		return dic['BaseResponse']['Ret'] == 0

			
