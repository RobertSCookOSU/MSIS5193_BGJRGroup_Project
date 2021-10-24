from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
import numpy as np
import time
import pandas as pd


driver = webdriver.Firefox(executable_path='c:\\Users\\Rober\\Documents\\geckodriver.exe')

sheriff_url = 'https://docs.oklahomacounty.org/sheriff/SheriffSales/'

sales_date_list = []
address_list = []
appraisal_list = []

i = 1
while i < 4:
    driver.get(sheriff_url)

    time.sleep(3)

    sales_date_ddl = Select(driver.find_element_by_id('SaleDates'))
    sales_date_ddl.select_by_index(i-1)

    submit_button = driver.find_elements_by_css_selector('input[type="submit"]')
    for elements in submit_button:
        elements.click()

    time.sleep(2)

    data = driver.find_elements_by_css_selector('td:nth-child(3) > font.featureFont')

    element_cnt = 0
    while element_cnt < len(data):
        if element_cnt % 9 == 0:
            sales_date_list.append(data[element_cnt].text)
        if element_cnt % 9 == 4:
            address_list.append(data[element_cnt].text)
        if element_cnt % 9 == 7:
            appraisal_list.append(data[element_cnt].text)
        element_cnt += 1

    i += 1

data_dictionary = {"SalesDate": sales_date_list,"Address":address_list,"AppraisalValue":appraisal_list}
df = pd.DataFrame(data_dictionary)

total_records = len(df.index)

# We need to add some columns for the additional data
df["beds"] = np.nan
df["baths"] = np.nan
df["sqft"] = np.nan
df["yearbuilt"] = np.nan
df["renoyear"] = np.nan

driver.quit()

cnt = 0

while cnt < total_records:
    if df.iloc[cnt,3] > 0:
        cnt += 1
        continue

    driver = webdriver.Firefox(executable_path='c:\\Users\\Rober\\Documents\\geckodriver.exe')
    address = df.iloc[cnt,1]
    address = address.replace('(RECALLED)','') + ',OK'
    realtor_url = 'https://www.realtor.com/'
    driver.get(realtor_url)
    time.sleep(5)

    # Check for bot challenge
    bot_text = driver.find_elements_by_css_selector('div > p')
    if len(bot_text) > 2:
        if "Challenge" in bot_text[2].text:
            print("We got caught by the bot challenge")
            break

    search_box = driver.find_element_by_id('searchbox-input')
    search_box.send_keys(address)
    time.sleep(9)

    search_button = driver.find_element_by_css_selector('form > div > button')
    search_button.click()

    time.sleep(4)

    # Check for bot challenge again
    bot_text = driver.find_elements_by_css_selector('div > p')
    if len(bot_text) > 2:
        if "Challenge" in bot_text[2].text:
            print("We got caught by the bot challenge")
            break    

    num_beds_list = driver.find_elements_by_css_selector('li[data-label="property-meta-beds"]>span')
    
    # Check to see if we even found the address
    if len(num_beds_list) < 1:
        df.iloc[cnt,3] = 100
        cnt += 1
        driver.quit()
        continue

    num_beds = driver.find_element_by_css_selector('li[data-label="property-meta-beds"]>span').text
    num_baths = driver.find_element_by_css_selector('li[data-label="property-meta-bath"]>span').text
    sqft = driver.find_element_by_css_selector('li[data-label="property-meta-sqft"]>span').text

    df.iloc[cnt,3] = num_beds
    df.iloc[cnt,4] = num_baths
    df.iloc[cnt,5] = sqft

    property_details = driver.find_elements_by_css_selector('#ldp-detail-public-records > ul > li')

    for detail in property_details:
        data_text = detail.text

        if "built" in data_text:
            data_text = data_text.replace("Year built: ","")
            df.iloc[cnt,6] = data_text
        elif "renovated" in data_text:
            data_text = data_text.replace("Year renovated: ", "")
            df.iloc[cnt,7] = data_text

    time.sleep(24)

    cnt += 1

    driver.quit()

driver.quit()

df.to_csv('c:\\temp\\sheriffsales.csv', index=False)
