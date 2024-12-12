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
    # 設定log檔
    def set_log():
        # log檔儲存路徑
        log_file_path = './data/verdict_data/verdict_data_log.log'

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

    # 設定driver
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
    # 檢查存放資料的路徑是否存在，如果不存在就建立路徑
    def creatpath(path):
        if not os.path.exists(path):
            os.makedirs(path)
            logger.info(f'已建立資料夾路徑 {path}')
        else:
            logger.info(f'確認資料夾路徑已存在: {path}')

""" 透過之前蒐集的URL開啟網頁 """
class open_website:
    # 檢查檔案路徑並找到檔案
    def get_file_path_and_check(file_parts):
        try:
            # 動態取得檔案路徑
            base_path = os.path.dirname(__file__)  # 獲取目前執行檔案的目錄
            file_path = os.path.join(base_path, *file_parts)  # 拼接路徑

            # 檢查檔案是否存在
            if not os.path.isfile(file_path):
                logger.error(f"檔案不存在: {file_path}")
                return None
            else:
                logger.info(f"找到檔案: {file_path}")
                return file_path
        except Exception as e:
            logger.error(f"檔案檢查發生錯誤: {e}")
            return None

    # 加工URL (前面加上 https://judgment.judicial.gov.tw/FJUD/)
    def change_url(file_path, keyword):
        try:
            # 讀取 CSV 檔案
            logger.info(f"嘗試讀取 CSV 檔案: {file_path}")
            url_data = pd.read_csv(file_path)
            logger.info(f"成功讀取 CSV 檔案: {file_path}")

            # 確認 CSV 檔案欄位名稱是否正確
            if '關鍵字' not in url_data.columns or 'URL' not in url_data.columns:
                logger.error(f"CSV 檔案中缺少必要欄位：{url_data.columns}")
                raise ValueError("CSV 檔案中缺少必要的欄位：'關鍵字' 或 'URL'")
            
            # 查找對應關鍵字的 URL
            logger.info(f"嘗試查找關鍵字 '{keyword}' 的對應 URL")
            specified_url = url_data.loc[url_data['關鍵字'] == keyword, 'URL']

            if specified_url.empty:
                logger.error(f"找不到關鍵字 '{keyword}' 的 URL")
                raise ValueError(f"找不到關鍵字 '{keyword}' 的 URL")

            # 與主頁連結結合
            try:
                front_page = "https://judgment.judicial.gov.tw/FJUD/"
                new_url = front_page + specified_url.values[0]
                logger.info(f"成功生成目標網站 URL: {new_url}")
                return new_url
            except Exception as e:
                logger.error("無法合併")

        except ValueError as ve:
            logger.error(f"資料處理錯誤: {ve}")
        except Exception as e:
            logger.error(f"URL合併異常: {e}")
        return None

    # 輸入新的URL並開啟網頁
    def input_and_open(driver, new_url):
        try:
            # 使用瀏覽器開啟新連結
            driver.get(new_url)
            logger.info(f"已成功開啟網頁: {new_url}")
        except Exception as e:
            logger.error(f"無法開啟網頁: {e}")

""" 爬取網頁資料 """
class catch_and_save:
    # 取得網頁的 HTML
    def get_soup(driver):
        try:
            html = driver.page_source
            soup = bs(html, 'html.parser')
            return soup
        except Exception as e:
            logger.error(f"取得HTML或解析時發生錯誤: {e}")
            return None
        
    # 爬取表格的標題
    def catch_table_headers(driver):
        try:
            soup = catch_and_save.get_soup(driver)

            # 從HTML內找到 <th>標籤，作為標題
            headers_element = soup.select_one("#jud tbody tr").find_all("th")
            headers = [header.text.strip() for header in headers_element]

            if headers:
                logger.info(f"成功獲得表格標題: {headers}")
                return headers
            else:
                logger.warning("未能獲得標題")
                return None
        except Exception as e:
            logger.error(f"提取標題時發生錯誤: {e}")
            return None
    
    # 爬取對應標題的內容
    def catch_table_content(driver):
        try:
            soup = catch_and_save.get_soup(driver)

            # 選取表格的所有資料列，排除 class="summary" 的 <tr>
            rows = soup.select("#jud tbody tr:not(.summary)")

            # 建立資料列表
            table_data = []

            # 遍歷每一列資料
            for row in rows[1:]:  # 跳過第一列，因為第一列是標題
                cols = row.find_all('td')
                # 提取每個欄位的文字，去除多餘空白
                row_data = [col.text.strip() for col in cols]
                table_data.append(row_data)

            if table_data:
                logger.info("成功提取表格內容")
                return table_data
            else:
                logger.warning("未提取到任何表格內容")
                return None
        except Exception as e:
            logger.error(f"提取表格內容時發生錯誤: {e}")
            return None
        
    # 換頁後再繼續爬 (直到頁數沒有為止)
    def change_page(driver):
        try:
            # 嘗試定位下一頁按鈕
            next_button = driver.find_element(By.ID, "hlNext")
            
            # 如果按鈕存在且可點擊，則點擊
            if next_button and next_button.is_displayed():
                next_button.click()
                sleep(3)  # 等待新頁面加載
                logger.info("已跳轉到下一頁")
                return True
            else:
                logger.info("無法找到下一頁按鈕，或已到最後一頁")
                return False
        except Exception as e:
            logger.error(f"跳轉下一頁時發生錯誤: {e}")
            return False
        
        except Exception as e:
            logger.error(f"爬取第{x}頁的時候發生錯誤: {e}")


    # 存成 CSV檔
    def save_to_csv(headers, data, output_path, is_first_page):
        try:
            # 使用動態的標題（headers）
            df = pd.DataFrame(data, columns=headers)

            # 判斷是否為第一頁
            mode = 'w' if is_first_page else 'a'
            header = is_first_page  # 第一頁需要寫表頭，其餘頁不需要

            df.to_csv(output_path, mode=mode, header=header, index=False, encoding='utf-8-sig')
            logger.info(f"表格已成功儲存為 CSV: {output_path}")
        except Exception as e:
            logger.error(f"儲存為 CSV 時發生錯誤: {e}")

    


if __name__ == '__main__':
    # 檢查路徑、資料夾，若不存在就建立
    data_folder = './data/verdict_data'
    operate.creatpath(data_folder)

    # 設定log
    logger = setting.set_log()

    # 取得檔案路徑
    file_parts = ["data", "keyword", "keyword_url.csv"]
    file_path = open_website.get_file_path_and_check(file_parts)

    # 設定檔案路徑和關鍵字
    file_path = "./data/keyword/keyword_url.csv"
    keyword = "詐欺罪"

    # 生成 URL
    newurl = open_website.change_url(file_path, keyword)

    if newurl:
        # 開啟瀏覽器
        driver = setting.set_driver()
        sleep(2)

        # 進入目標網址
        open_website.input_and_open(driver, newurl)
        sleep(2)

        # 計數器
        current_page = 1  # 爬到第X頁
        total_count = 0   # 累計爬了Y筆資料

        # 提取表格標題
        headers = catch_and_save.catch_table_headers(driver)
        if headers:
            logger.info(f"表格標題: {headers}")
        sleep(2)

        while True:
            logger.info(f"開始爬取第 {current_page} 頁")
            
            # 提取表格內容
            content = catch_and_save.catch_table_content(driver)
            if content:
                # 記錄當前頁的資料數量
                page_count = len(content)
                total_count += page_count
                logger.info(f"第 {current_page} 頁共爬取 {page_count} 筆資料，累計爬取 {total_count} 筆資料")

                # 儲存為 CSV
                output_csv = './data/verdict_data/verdict_data.csv'
                is_first_page = current_page == 1
                catch_and_save.save_to_csv(headers, content, output_csv, is_first_page)
            else:
                logger.warning(f"第 {current_page} 頁未提取到任何資料")

            # 嘗試切換到下一頁
            if not catch_and_save.change_page(driver):
                logger.info("已到最後一頁，結束爬取")
                break 

            # 更新頁數
            current_page += 1
            sleep(2)  # 等待新頁面加載

            ### 測試需求 ###
            if current_page == 3:
                logger.info(f"已達設定的測試頁數限制，結束爬取")
                break
        logger.info(f"爬取完成，共爬取 {total_count} 筆資料")

    else:
        logger.error("生成 URL 失敗，無法繼續執行")

    # 關閉瀏覽器
    driver.quit()