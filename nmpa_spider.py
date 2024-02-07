import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from datetime import datetime, timedelta
import pandas as pd
import os
import re


# 关闭页面导航条
def skip_introjs(driver):
    # 等待关闭按钮出现并点击
    try:
        is_intro = WebDriverWait(driver, 20, 0.5).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "introjs-skipbutton")))
        is_intro.click()
        print("导航条已关闭！")
    except:
        print("没有发现导航条！")
    return


# 处理一页列表（即有10条结果的页面）
def onepage_of_list(driver, df, first_number_of_windows, codes_list):
    wait = WebDriverWait(driver, 60, 0.5)
    list_elements = wait.until(EC.presence_of_element_located((By.TAG_NAME, "tbody"))) # 寻找页面中的表格
    number_of_list = list_elements.find_elements(By.CLASS_NAME, "el-table_1_column_1") # 寻找表格中的序号
    button_of_list = list_elements.find_elements(By.TAG_NAME, "button") # 寻找表格中的按钮
    code_of_list = list_elements.find_elements(By.CLASS_NAME, "el-table_1_column_2")

    # 遍历每个链接（按钮），并点击
    if button_of_list:
        index = 0
        while index < button_of_list.__len__():
        # for index, element in enumerate(button_of_list):
            code = code_of_list[index].text # 当前行的注册证编号

            if code not in codes_list:
                print("\n发现一条新的产品信息")
                second_number_of_windows = len(driver.window_handles)
                number = number_of_list[index].text # 当前行的序号

                # button_of_list[index].click() #经常被遮挡而不可用
                driver.execute_script("arguments[0].click();", button_of_list[index]) # 点击详情按钮
                
                # 等待新窗口打开
                wait.until(EC.number_of_windows_to_be(second_number_of_windows + 1))
                # Swith to new window
                driver.switch_to.window(driver.window_handles[second_number_of_windows])
                # 获取详情信息
                try:
                    # wait.until(EC.title_is("国家药品监督管理局数据查询"))
                    detail_elements = wait.until(EC.presence_of_element_located((By.TAG_NAME, "tbody")))
                    # 缺少一个判断表格是否加载完成的语句，下句太慢
                    # wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#su'),u'详情'))
                    # 判断整个表格是否加载完成，即出现“详情”（有点瑕疵，也可能其他字段出现）
                    wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "tbody"),'详情'))
                    # sleep(3)
                    # detail_elements = wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "tbody"),'详情'))

                    rows_elements = detail_elements.find_elements(By.TAG_NAME, "tr")

                    if len(rows_elements) == 0:
                        print("\n第" + number + "条数据爬取不完整，正在重新爬取...", end="")
                        # 关闭详情窗口
                        driver.close()
                        # 返回到列表窗口
                        driver.switch_to.window(driver.window_handles[first_number_of_windows])
                        continue

                    columns1 = ["序号"]
                    columns2 = [number]
                    print("\n正在爬取第" + number + "条数据，该条有" + str(len(rows_elements)) + "个数据项...", end="")
                    for rows_element in rows_elements:
                        temp = rows_element.text.splitlines()
                        columns1.append(temp[0])
                        del temp[0]
                        columns2_value = ""
                        for item in temp:
                            columns2_value = columns2_value + item
                        columns2.append(columns2_value)
                    if df.empty:
                        df = pd.DataFrame(columns=range(len(rows_elements) + 1))
                        df.loc[len(df)] = columns1
                    if len(df.columns) == columns2.__len__():
                        df.loc[len(df)] = columns2
                        print("\n第" + number + "条数据已爬取！", end="")
                        # 关闭详情窗口
                        driver.close()
                        # 返回到列表窗口
                        driver.switch_to.window(driver.window_handles[first_number_of_windows])
                        index += 1
                    else:
                        print("\n第" + number + "条数据爬取不完整，正在重新爬取...", end="")
                        # 关闭详情窗口
                        driver.close()
                        # 返回到列表窗口
                        driver.switch_to.window(driver.window_handles[first_number_of_windows])
                        continue
                except:
                    print("第" + number + "条数据提取失败，正在重新爬取...", end="")
                    # 关闭详情窗口
                    driver.close()
                    # 返回到列表窗口
                    driver.switch_to.window(driver.window_handles[first_number_of_windows])
                    continue
            else:
                index += 1
    else:
        print("查询结果没有加载成功！")

    return df


def keyword_query(driver, my_database, my_keyword, df_path, filename):
    wait = WebDriverWait(driver, 30, 0.5)
    # 查找选择数据库，输入关键词和提交按钮相关的元素
    database_elements = wait.until(EC.presence_of_all_elements_located((By.LINK_TEXT, my_database)))
    input_elements = driver.find_elements(By.CLASS_NAME, "el-input__inner") # 输入查询的关键词
    button_elements = driver.find_elements(By.CLASS_NAME, "el-button--default")
    first_number_of_windows = len(driver.window_handles)

    # 如果用户提供了上一次爬取的数据，就可以与之比对
    codes_list = (pd.read_excel(df_path, header=0)["注册证编号"].to_list() if df_path else [])
        
    df = pd.DataFrame(columns=range(14)) 

    # 点击数据库，输入搜索关键字，点击搜索按钮
    driver.execute_script("arguments[0].click();", database_elements[0])
    input_elements[1].send_keys(my_keyword)
    driver.execute_script("arguments[0].click();", button_elements[0])

    # 等待新窗口打开
    if wait.until(EC.number_of_windows_to_be(first_number_of_windows + 1)):
        # Swith to new window
        sleep(2)
        driver.switch_to.window(driver.window_handles[first_number_of_windows])
    else:
        print("查询页面没有加载成功！")
        return False

    # 关闭查询结果列表页导航
    skip_introjs(driver)

    # 查找第一页详情链接
    df = onepage_of_list(driver, df, first_number_of_windows, codes_list)

    # 取下一页
    nextpage_button_elements = driver.find_elements(By.CLASS_NAME, "btn-next")
    number_pages = 0
    while nextpage_button_elements[0].is_enabled():
        number_pages += 1
        nextpage_button_elements[0].click()
        df = onepage_of_list(driver, df, first_number_of_windows, codes_list)
        print(f"已保存{number_pages}上的{len(df)}条数据")
        # break

    time = datetime.now().strftime('%Y%m%d%H%M')
    
    if not filename:
        filename = f'data/{my_keyword}_{my_database}_{time}.xlsx'
    
    # df.to_excel((r'D:\nmpa_ylqx.xlsx'), sheet_name=my_database, index=False)
    if os.path.exists(filename):
        print("向文件" + filename + "中追加数据!")
        with pd.ExcelWriter(filename, mode="a", engine="openpyxl", if_sheet_exists="replace") as writer:
            df.to_excel(writer, sheet_name=my_database, index=False)
            # df.to_excel(writer, sheet_name='Sheet1', index=False)
    else:
        print(r"新建文件" + filename + "!")
        with pd.ExcelWriter(filename) as writer:
            df.to_excel(writer, sheet_name=my_database, index=False)
    print(f"数据保存到{os.path.abspath()(filename)}")

    return True


def search_ylqx(database, keyword, df_path=False, output_path=False):
    """通过关键词在数据库里查找医疗器械，储存在一个用户指定的文件里。
    
    参数:
        database: 数据库名称，如`境内医疗器械（注册）`、`进口医疗器械（注册）`.
        keyword: 要查询的关键词.
        df_path: 上一次爬取的excel文件的地址.如果没有提供，则爬取所有内容.
        output_path: 指定结果的存储路径。如果该文件已存在，函数将续写其内容；如果文件不存在，
            函数将创建该文件并写入结果。默认路径为`data`文件夹下`{keyword}_{database}_{time}.xlsx`

    """
    print("开始时间：" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

    # 四个大类：药品、医疗器械、化装品、其他
    # url = "https://www.nmpa.gov.cn/datasearch/home-index.html#category=yp"
    url = "https://www.nmpa.gov.cn/datasearch/home-index.html#category=ylqx"
    # url = "https://www.nmpa.gov.cn/datasearch/home-index.html#category=hzp"
    # url = "https://www.nmpa.gov.cn/datasearch/home-index.html#category=qt"

    # 提高效率，无界面浏览等
    options = webdriver.FirefoxOptions()
    options.add_argument("-headless")
    driver = webdriver.Firefox(options=options)

    '''
    # 有界面浏览
    driver = webdriver.Firefox()
    driver.maximize_window()
    '''
    # 打开网页
    driver.get(url)

    # 数据库和关键词
    # database = "境内医疗器械（注册）"
    # database = "境内医疗器械（备案）"
    # database = "进口医疗器械（备案历史数据）"
    # database = "进口医疗器械（注册）"
    # keyword = "过敏"
    # keyword = "."

    # 
    # df_path = 'D:/Roche/data/过敏自勉/过敏_境内.xlsx'

    # 关闭首页导航条，以免影响操作
    skip_introjs(driver)
    print("开始爬取 数据库："+database+";关键词："+keyword+" ")

    # 执行“数据库+关键词”查询
    if keyword_query(driver, database, keyword, df_path, output_path):
        print("已完成对 数据库："+database+";关键词："+keyword+" 的成功爬取！")
    else:
        print("本次数据爬取失败！")

    # 关闭浏览器
    driver.quit()

    print("结束时间：" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
