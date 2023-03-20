# coding: utf-8
from json import loads
from os.path import exists
from pickle import dump, load
from time import sleep, time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Concert(object):
    def __init__(self, session, price, date, real_name, nick_name, ticket_num, damai_url, target_url):
        self.session = session  # 场次序号优先级
        self.price = price  # 票价序号优先级
        self.date = date # 日期选择
        self.real_name = real_name  # 实名者序号
        self.status = 0  # 状态标记
        self.time_start = 0  # 开始时间
        self.time_end = 0  # 结束时间
        self.num = 0  # 尝试次数
        self.type = 0  # 目标购票网址类别
        self.ticket_num = ticket_num  # 购买票数
        self.nick_name = nick_name  # 用户昵称
        self.damai_url = damai_url  # 大麦网官网网址
        self.target_url = target_url  # 目标购票网址
        self.browser = 0 # 0代表Chrome，1代表Firefox，默认为Chrome
        self.total_wait_time = 3 # 页面元素加载总等待时间
        self.refresh_wait_time = 0.3 # 页面元素等待刷新时间
        self.intersect_wait_time = 0.5 # 间隔等待时间，防止速度过快导致问题

        if self.target_url.find("detail.damai.cn") != -1:
            self.type = 1
        elif self.target_url.find("piao.damai.cn") != -1:
            self.type = 2
        else:
            self.type = 0
            self.driver.quit()
            raise Exception("***Error:Unsupported Target Url Format:{}***".format(self.target_url))

            
    def isClassPresent(self, item, name, ret=False):
        try:
            result = item.find_element_by_class_name(name)
            if ret:
                return result
            else:
                return True
        except:
            return False

        
    def get_cookie(self):
        self.driver.get(self.damai_url)
        print("###请点击登录###")
        while self.driver.title.find('大麦网-全球演出赛事官方购票平台') != -1:  # 等待网页加载完成
            sleep(1)
        print("###请扫码登录###")
        while self.driver.title == '大麦登录':  # 等待扫码完成
            sleep(1)
        dump(self.driver.get_cookies(), open("cookies.pkl", "wb"))
        print("###Cookie保存成功###")

        
    def set_cookie(self):
        try:
            cookies = load(open("cookies.pkl", "rb"))  # 载入cookie
            for cookie in cookies:
                cookie_dict = {
                    'domain':'.damai.cn',  # 必须有，不然就是假登录
                    'name': cookie.get('name'),
                    'value': cookie.get('value'),
                    "expires": "",
                    'path': '/',
                    'httpOnly': False,
                    'HostOnly': False,
                    'Secure': False}
                self.driver.add_cookie(cookie_dict)
            print(u'###载入Cookie###')
        except Exception as e:
            print(e)

            
    def login(self):
        print(u'###打开浏览器，进入大麦网###')
        if not exists('cookies.pkl'):   # 如果不存在cookie.pkl,就获取一下
            self.driver = webdriver.Chrome()
            self.get_cookie()
            print(u'###成功获取Cookie，重启浏览器###')
            self.driver.quit()
        # 选择了Chrome浏览器，并成功加载cookie，设置不载入图片，提高刷新效率
        options = webdriver.ChromeOptions()
        options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images":2})
        self.driver = webdriver.Chrome(options=options)
        self.driver.get(self.target_url)
        self.set_cookie()
        self.driver.refresh()
    
    def check_login(self):
        try:
            # detail.damai.cn
            if self.type == 1:  # detail.damai.cn
                locator = (By.XPATH, "/html/body/div[1]/div/div[3]/div[1]/a[2]/div")
            elif self.type == 2:  # piao.damai.cn
                locator = (By.XPATH, "/html/body/div[1]/div/ul/li[2]/div/label/a[2]")
            WebDriverWait(self.driver, self.total_wait_time, self.refresh_wait_time).until(
                EC.text_to_be_present_in_element(locator, self.nick_name))
            self.status = 1
        except Exception as e:
            print(e)
            self.status = 0
            self.driver.quit()
    
        
    def enter_concert(self):
        self.login()
        self.check_login()
        if self.status == 1:
            print("###登录成功###")
        else:
            raise Exception("***错误：登录失败,请检查配置文件昵称或删除cookie.pkl后重试***")

    
    def choose_ticket(self):
        self.time_start = time()
        print("###开始进行日期及票价选择###")
        # while self.driver.title.find('确认订单') == -1:  # 如果跳转到了确认界面就算这步成功了，否则继续执行此步
        self.num += 1 # 记录抢票轮数
        self.choose_date()
        session_em, price_em = self.order_select()
        self.choose_session(session_em=session_em)
        self.choose_price(price_em=price_em)
            
    
    def choose_date(self):
        if self.date != 0: # 如果需要选择日期
            calendar = WebDriverWait(self.driver, self.total_wait_time, self.refresh_wait_time).until(
                EC.presence_of_element_located((By.CLASS_NAME, "functional-calendar")))
            datelist = calendar.find_elements(by=By.CSS_SELECTOR, value="[class='wh_content_item']")
            # datelist = calendar.find_elements(by=By.CSS_SELECTOR, value="[class='wh_top_change']")
            # datelist = calendar.find_elements_by_css_selector("[class='wh_content_item']") # 找到能选择的日期
            datelist = datelist[7:] # 跳过前面7个表示周一~周日的元素
            datelist[self.date - 1].click() # 选择对应日期

    def order_select(self):
        selects = self.driver.find_elements(by=By.CLASS_NAME, value='perform__order__select')
        # print('可选区域数量为：{}'.format(len(selects)))
        for item in selects:
            if item.find_element(by=By.CLASS_NAME, value='select_left').text == '场次':
                session = item
                # print('\t场次定位成功')
            elif item.find_element(by=By.CLASS_NAME, value='select_left').text == '票档':
                price = item
                # print('\t票档定位成功')
        return session, price

    def choose_session(self, session_em):
        session_list = session_em.find_elements(by=By.CLASS_NAME, value='select_right_list_item')
        print('可选场次数量为：{}'.format(len(session_list)))
        if len(self.session) == 1:
            j = session_list[self.session[0] - 1].click()
        else:
            for i in self.session:  # 根据优先级选择一个可行场次
                j = session_list[i - 1]
                k = self.isClassPresent(j, 'presell', True)
                if k:  # 如果找到了带presell的类
                    if k.text == '无票':
                        continue
                    elif k.text == '预售':
                        j.click()
                        print("choose_session presell")
                        break
                else:
                    j.click()
                    print("choose_session done")
                    break

    def choose_price(self, price_em):
        price_list = price_em.find_elements(by=By.CLASS_NAME, value='select_right_list_item')
        print('可选票档数量为：{}'.format(len(price_list)))
        if len(self.price) == 1:
            j = price_list[self.price[0] - 1].click()
        else:
            for i in self.price:
                j = price_list[i - 1]
                k = self.isClassPresent(j, 'notticket')
                if k:  # 存在notticket代表存在缺货登记，跳过
                    continue
                else:
                    j.click()
                    print("choose_price done")
                    break

    def buy(self):
        buybutton = self.driver.find_element(by=By.CLASS_NAME, value='buybtn')
        buybutton_text = buybutton.text
        print(buybutton_text)
        
        def add_ticket(): # 设置增加票数
            try:
                for i in range(self.ticket_num - 1):  
                    addbtn = WebDriverWait(self.driver, self.total_wait_time, self.refresh_wait_time).until(
                        EC.presence_of_element_located((By.XPATH, "//div[@class='cafe-c-input-number']/a[2]")))
                    addbtn.click()
            except:
                raise Exception("***错误：票数增加失败***")

        if buybutton_text == "即将开抢" or buybutton_text == "即将开售":
            self.status = 2
            self.driver.refresh()
            print('---尚未开售，刷新等待---')

        elif buybutton_text == "立即预订":
            add_ticket()
            buybutton.click()
            self.status = 3

        elif buybutton_text == "立即购买":
            add_ticket()
            buybutton.click()
            self.status = 4

        elif buybutton_text == "选座购买":  # 选座购买暂时无法完成自动化
            # buybutton.click()
            self.status = 5
            print("###请自行选择位置和票价###")

        elif buybutton_text == "提交缺货登记":
            print('###抢票失败，请手动提交缺货登记###')

    def check_order(self):
        if self.status in [3, 4]:
            print('###开始确认订单###')
            button_xpath = " //*[@id=\"confirmOrder_1\"]/div[%d]/button" # 同意以上协议并提交订单Xpath
            button_replace = 8 # 当实名者信息不空时为9，空时为8
            if self.real_name: # 实名者信息不为空
                button_replace = 9
                print('###选择购票人信息###')
                try:
                    list_xpath = "//*[@id=\"confirmOrder_1\"]/div[2]/div[2]/div[1]/div[%d]/label/span[1]/input"
                    for i in range(len(self.real_name)): # 选择第i个实名者
                        WebDriverWait(self.driver, self.total_wait_time, self.refresh_wait_time).until(
                            EC.presence_of_element_located((By.XPATH, list_xpath%(i+1)))).click()
                except Exception as e:
                    print(e)
                    raise Exception("***错误：实名信息框未显示，请检查网络或配置文件***")
            submitbtn = WebDriverWait(self.driver, self.total_wait_time, self.refresh_wait_time).until(
                    EC.presence_of_element_located(
                        (By.XPATH, button_xpath%button_replace))) # 同意以上协议并提交订单
            submitbtn.click()  
            '''# 以下的方法更通用，但是更慢
            try:
                buttons = self.driver.find_elements_by_tag_name('button') # 找出所有该页面的button
                for button in buttons:
                    if button.text == '同意以上协议并提交订单':
                        button.click()
                        break
            except Exception as e:
                raise Exception('***错误：没有找到提交订单按钮***')
           '''
            try:
                WebDriverWait(self.driver, self.total_wait_time, self.refresh_wait_time).until(
                    EC.title_contains('支付宝'))
                self.status = 6
                print('###成功提交订单,请手动支付###')
                self.time_end = time()
            except Exception as e:
                print('---提交订单失败,请查看问题---')
                print(e)            

    def finish(self):
        if self.status == 6:  # 说明抢票成功
            print("###经过%d轮奋斗，共耗时%f秒，抢票成功！请确认订单信息###" % (self.num, round(self.time_end - self.time_start, 3)))
        else:
            self.driver.quit()


if __name__ == '__main__':
    try:
        config = {
            "session": [1],  # 场次
            "price": [1, 3],  # 票档
            "date": 1,  # 日期 0:不需要选择日期, 1:需要选择日期
            "real_name": [],  # 实名信息序号
            "nick_name": "麦子4jGdd",  # 用户昵称
            "ticket_num": 2,  #票数
            "damai_url": "https://www.damai.cn/",  # 官网网址
            "target_url": "https://detail.damai.cn/item.htm?spm=a2oeg.search_category.0.0.47a64d1569dzBI&id=640417691473",  # 目标网址
        }
        con = Concert(
            config['session'], 
            config['price'], 
            config['date'], 
            config['real_name'], 
            config['nick_name'], 
            config['ticket_num'],
            config['damai_url'], 
            config['target_url']
        )
    except Exception as e:
        raise Exception(f"***错误：初始化失败，请检查配置*** {e}")
    con.enter_concert()
    con.choose_ticket()
    # if con.type == 1:  # detail.damai.cn
    #     con.choose_ticket_1()
    #     con.check_order_1()
    # elif con.type == 2:  # piao.damai.cn
    #     con.choose_ticket_2()
    #     con.check_order_2()
    # while True: # 可用于无限抢票，防止弹窗类异常使抢票终止
    # if True:
    #     try:
    #         if con.type == 1:  # detail.damai.cn
    #             con.choose_ticket_1()
    #             con.check_order_1()
    #         elif con.type == 2:  # piao.damai.cn
    #             con.choose_ticket_2()
    #             con.check_order_2()
    #         # break
    #     except Exception as e:
    #         print(e)
    #         con.driver.get(con.target_url)
    con.finish()
