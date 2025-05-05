import os
from datetime import datetime
import time

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By

weekday_dict = {
    0: 'Monday',
    1: 'Tuesday',
    2: 'Wednesday',
    3: 'Thursday',
    4: 'Friday',
    5: 'Saturday',
    6: 'Sunday'

}
month_dict = {
    1: 'January',
    2: 'February',
    3: 'March',
    4: 'April',
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September',
    10: 'October',
    11: 'November',
    12: 'December'
}

image_sample = '<img    src="{image_directory}/{image}"  height="200px"   />'
html_sample = """
              <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
    <title>Lot Detail - {name}</title>
</head>
<body>






<h1>{name}</h1>

    {images}
    



        <table>
                                    <tr>
                                        <td>Minimum Bid:</td>
                                        <td>{minimum_bid}</td>
                                    </tr>

                                    <tr style="white-space: nowrap;">
		                                <td>Final prices include buyers premium:</td>
		                                <td>{final_price}</td>
	                                </tr>
                                    <tr>
                                        <td>Number Bids:</td>
                                        <td>{bids_number}</td>
                                    </tr>




                                    <tr>
                                        <td colspan="2">Auction Time</td>
                                        <td>{bid_close_time}</td>
                                    </tr>
                                    <tr>
                                        <td id="CurrentBiddingTable" colspan="2">Description</td>
                                        <td>{description}</td>
                                    </tr>
                                </table>


    

</body>
</html>
"""

option = webdriver.ChromeOptions()
option.headless = False
browser = webdriver.Chrome(options=option)

current_link = 'https://richmondfirearms.com/Engraved_Browning_Synergy_Classic_Grade_VI_Over_Un-LOT336.aspx'


def get_lot_path(soup):
    information = soup.find_all('h1', class_='BreadcrumbH1')[1].find_all('a', class_='CategoryBreadcrumbLink')
    if len(information) < 2:
        information = soup.find_all('h1', class_='BreadcrumbH1')[0].find_all('a', class_='CategoryBreadcrumbLink')

    path = 'All/'

    for directory in information[1:]:
        directory = directory.text
        directory = directory.replace('&amp;', '&')

        path += f'{directory}/'

    return path


def get_lot_info(soup):
    upper_panel = soup.find('div', id='LotInfo')
    lot_name = upper_panel.find('h1').text
    minimum_bid = soup.find('td', id='MinimumBidding').text
    final_prices = soup.find('td', id='FinalBid').text
    bids_number = soup.find('td', id='NumberOfBids').text
    description = soup.find('div', id='Description').text

    lot_close_time = soup.find('div', id='ClosedItem'
                               ).text.removeprefix('\r\n                '
                                                   ).removesuffix('\r\n            '
                                                                  ).replace(
        'This lot is closed for bidding.  Bidding ended on', ''
    ).strip()

    month, day, year = map(lambda x: int(x.strip()), lot_close_time.split('/'))

    lot_close_time = datetime(year, month, day)
    lot_close_time = f'Auction closed on {weekday_dict[lot_close_time.weekday()]}, {month_dict[lot_close_time.month]} {lot_close_time.day}, {lot_close_time.year}'

    return lot_name.replace('"', '|').replace('/',
                                              '|'), lot_close_time, minimum_bid, final_prices, bids_number, description


def get_lot_images(soup):
    images_links = soup.find('div', style='margin-top:15px;').find_all('a')
    images_bytes = {}

    for image_link in images_links:
        image_name = image_link.get("href")
        image_link = f'https://richmondfirearms.com{image_name}'
        image_byte = requests.get(image_link).content

        image_name = image_name.split('/')[-1]
        images_bytes[image_name] = image_byte

    return images_bytes


def write_data(path, info, images):
    lot_name, lot_close_time, minimum_bid, final_prices, bids_number, description = info

    lot_directory = f'{path}{lot_name}/'
    lot_images_directory = f'{lot_directory}/{lot_name}_img/'

    os.makedirs(lot_directory)
    os.makedirs(lot_images_directory)
    images_html = ''
    for image_name, image_byte in images.items():
        images_html += image_sample.format(image_directory=f'{lot_name}_img', image=image_name)

        with open(f'{lot_images_directory}/{image_name}', 'wb') as file:
            file.write(image_byte)

    with open(f'{lot_directory}/{lot_name}.html', 'w') as file:
        file.write(
            html_sample.format(name=lot_name, images=images_html, minimum_bid=minimum_bid, final_price=final_prices,
                               bids_number=bids_number, bid_close_time=lot_close_time, description=description))


for _ in range(1):  # 375
    response = requests.get(current_link).text
    my_soup = BeautifulSoup(response, 'lxml')

    lot_path = get_lot_path(my_soup)
    lot_info = get_lot_info(my_soup)
    print(f'Parsing this item: {lot_info[0]} ...')
    lot_images = get_lot_images(my_soup)

    write_data(path=lot_path, info=lot_info, images=lot_images)

    browser.get(current_link)
    button_xpath = '//*[@id="NextButton"]'
    browser.find_element(By.XPATH, value=button_xpath).click()

    current_link = browser.current_url
    print(f'{lot_info[0]} parsed!')
    time.sleep(3)
