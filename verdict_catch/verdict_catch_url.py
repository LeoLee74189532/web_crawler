""" 套件 """
import requests as res
from bs4 import BeautifulSoup as bs
from time import sleep
from pprint import pprint
import pandas as pd
import json
import csv
import logging as log
from logging import getLogger
logger = getLogger('verdict.log')

# 處理正則表達式
import re 

# 執行 系統命令(commend)
import os

# 讓執行中可能會跑出的warnings閉嘴
# import warnings
# warnings.filterwarnings("ignore")

""" selenium套件 """
# 瀏覽器自動化
from selenium import webdriver as wd
from selenium.webdriver.chrome.service import Service

# (三人行) 在動態網頁中，等待指定元素出現的工具(要等多久?)
from selenium.webdriver.support.ui import WebDriverWait
# (三人行) 當指定元素出現，便符合等待條件 → 停止等待階段，並往下一段程式碼執行
from selenium.webdriver.support import expected_conditions as EC
# (三人行) 以...搜尋指定物件 (如: ID、Name、連結內容等...)
from selenium.webdriver.common.by import By 

# 處理逾時例外的工具 (網頁反應遲緩 or 網路不穩定)
from selenium.common.exceptions import TimeoutException

# 加入行為鍊 ActionChain (在 WebDriver 中模擬滑鼠移動、點擊、拖曳、按右鍵出現選單，以及鍵盤輸入文字、按下鍵盤上的按鈕等)
from selenium.webdriver.common.action_chains import ActionChains

# 加入鍵盤功能 (例如 Ctrl、Alt 等)
from selenium.webdriver.common.keys import Keys

""" 設定 """
class setting:
    """ 設定log檔 """
    def set_log():
        # log檔儲存路徑
        log_file_path = './data/keyword/keyword_url_log.log'

        # 基本設定
        logger = log.getLogger('verdict.log')

        # 設定等級
        logger.setLevel(log.INFO)

        # 設定輸出格式
        formatter = log.Formatter('%(asctime)s - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S")

        # 儲存在 log 當中的事件處理器 (a: append, w: write)
        fileHandler = log.FileHandler(log_file_path, mode='a', encoding='utf-8')
        fileHandler.setFormatter(formatter)

        # 輸出在終端機介面上的事件處理器
        console_handler = log.StreamHandler()
        console_handler.setFormatter(formatter)

        # 加入事件
        logger.addHandler(console_handler)
        logger.addHandler(fileHandler)

        return logger

    """ 設定driver """
    def set_driver():
        # 啟動瀏覽器的工具選項
        verdict_options = wd.ChromeOptions()
        # verdict_options.add_argument("--headless")             # 不開啟實體瀏覽器視窗
        verdict_options.add_argument("--start-maximized")        # 最大化視窗
        # verdict_options.add_argument("--incognito")            # 開啟無痕分頁(如果要開實體瀏覽器，就不用無痕分頁)
        verdict_options.add_argument("--disable-popup-blocking") # 禁止彈出連結，避免彈窗干擾自動化操作
        verdict_options.add_argument("--disable-notifications")  # 取消 chrome 推波通知
        verdict_options.add_argument("--lang=zh-TW")             # 設定為繁體中文
        verdict_options.add_experimental_option('detach', True)  # 設定不自動關閉瀏覽器
        verdict_options.add_argument("--no-sandbox")             # 添加此行可以在某些環境中提高穩定性
        # verdict_options.add_argument("--disable-dev-shm-usage")  # 提高性能
        verdict_options.add_argument('--disable-gpu')            # 禁用GPU加速

        # 使用 Chrome 的 Webdriver (若沒有特別設定，只要電腦有安裝Chrome，就可以直接使用)
        driver = wd.Chrome(options = verdict_options)
        
        return driver

""" 額外操作 """
class operate:
    """ 檢查存放資料的路徑是否存在，如果不存在就建立路徑 """
    def creatpath(path):
        if not os.path.exists(path):
            os.makedirs(path)
            logger.info(f'已建立資料夾路徑 {path}')
        else:
            logger.info(f'資料夾路徑已存在: {path}')
    
    """ 滾動頁面 """
    def scroll():
        # JS元素
        innerHeight = 0 # 瀏覽器內部的高度
        offset = 0      # 當前捲動的量(高度)
        count = 0       # 累計無效滾動次數
        limit = 3       # 最大無效滾動次數
        
        # 持續捲動，直到沒有元素動態產生
        while count <= limit:
            # 每次移動高度
            offset = driver.execute_script(
                'return document.documentElement.scrollHeight;'
            )

            '''
            或是每次只滾動一點距離，
            以免有些網站會在移動長距離後，
            將先前移動當中的元素隱藏

            EX: 將上方的 script 改成: offset += 600
            '''

            # 捲軸往下滑動
            driver.execute_script(f'''window.scrollTo({{top: {offset}, behavior: 'smooth' }});''')
            
            '''
            [補充]
            如果要滾動的是 div 裡面的捲軸，可以使用以下的方法
            document.querySelector('div').scrollTo({...})
            '''
            
            # (重要)強制等待，此時若有新元素生成，瀏覽器內部高度會自動增加
            sleep(3)
            
            # 透過執行 js語法 來取得捲動後的當前總高度
            innerHeight = driver.execute_script(
                'return document.documentElement.scrollHeight;'
            )
            
            # 經過計算，如果滾動距離(offset)大於、等於視窗內部總高度(innerHeight)，代表已經到底了
            if offset == innerHeight:
                count += 1
                
            # 為了實驗功能，捲動超過一定的距離，就結束程式
            # if offset >= 600:
            #     break

            # print (innerHeight)

""" 開啟網頁、輸入資料並查詢 """
class open_website:
    # 輸入網址
    def enter_url(driver, url):
        try:
            # 將瀏覽器導向指定網址
            driver.get(url)
            logger.info(f"成功開啟網址: {url}")
        except Exception as e:
            logger.error(f"無法開啟網址: {url}, 錯誤原因: {e}")

    # 輸入關鍵字並查詢
    def search_keyword(driver, keyword):
        try:
            keyword_input = driver.find_element(By.ID, "txtKW") # 定位輸入欄
            keyword_input.clear()  # 清空輸入欄位
            keyword_input.send_keys(keyword)  # 輸入要查詢的關鍵字
            logger.info(f"已輸入關鍵字: {keyword}")
        except Exception as e:
            logger.error("無法正常搜尋該關鍵字的判決書資料")

    # 按下送出按鈕
    def click_search(driver):
        try:
            # 定位送出按鈕，點擊
            search_button = driver.find_element(By.ID, "btnSimpleQry")
            search_button.click()
            logger.info("已點擊「送出按鈕」")
        except Exception as e:
            logger.error(f"點擊「送出按鈕」時發生錯誤: {e}")

    # 切換至初始頁面 (如要蒐集其他關鍵字結果的 隱藏URL)

""" 抓取資料並存成csv檔 """
class catch_and_save:
    # 抓取隱藏網址(要抓取資料的HTML在此連結內)
    def catch_hidden_url(driver):
        try:
            # 取得網頁的 HTML
            html = driver.page_source
            # 解析 HTML
            soup = bs(html, 'html.parser')
            # 根據指定的 HTML 路徑，找到 <a> 標籤並提取 href
            hidden_url_element = soup.select_one("#result-count li.active a")
            hidden_url = hidden_url_element['href'] if hidden_url_element else None
            
            if hidden_url:
                logger.info(f"成功抓取隱藏網址: {hidden_url}")
                return hidden_url
            else:
                logger.warning("未找到隱藏網址")
                return None
        except Exception as e:
            logger.error(f"使用 BeautifulSoup 抓取隱藏網址時發生錯誤: {e}")
            return None
    
    # 將爬取的資料存成 CSV檔
    def save_to_csv(keyword, url, file_path):
        try:
            # 建立表格資料
            table = pd.DataFrame({
                "關鍵字": [keyword],  # 關鍵字列
                "URL": [url]         # URL 列
            })
            # 存成 CSV
            table.to_csv(file_path, index=False, encoding='utf-8-sig')  # 不寫入索引，支援中文
            logger.info(f"成功將資料存成 CSV 檔案: {file_path}")
        except Exception as e:
            logger.error(f"存檔時發生錯誤: {e}")


if __name__ == '__main__':
    # 檢查路徑、資料夾，若不存在就建立
    data_folder = './data/keyword'
    operate.creatpath(data_folder)

    # 設定log
    logger = setting.set_log()

    # 開啟瀏覽器
    driver = setting.set_driver()
    sleep(2)

    # 進入目標網址
    target_url = "https://judgment.judicial.gov.tw/FJUD/default.aspx"
    open_website.enter_url(driver, target_url)
    sleep(2)

    # 輸入關鍵字並查詢
    keyword = "詐欺罪"  # 輸入您要查詢的關鍵字
    sleep(2)
    open_website.search_keyword(driver, keyword)
    open_website.click_search(driver)
    sleep(3)

    # bs抓取隱藏網址
    hidden_url = catch_and_save.catch_hidden_url(driver)

    # 檢查是否抓取到網址
    if hidden_url:
        # 存成 CSV
        csv_file_path = f"{data_folder}/keyword_url.csv"
        catch_and_save.save_to_csv(keyword, hidden_url, csv_file_path)

    # 關閉
    driver.quit()

