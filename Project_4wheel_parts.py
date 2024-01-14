import requests
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Selenium Logic is required first to extract the cloudfare cookie "__cf_bm"
Browser needs to be run headful, headless didn't work for me

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

#Selenium Logic
driver_path = r"C:\Users\JORGITO\Downloads\chromedriver.exe"
options = webdriver.ChromeOptions()

driver = webdriver.Chrome(executable_path=driver_path, options=options)
driver.get('https://www.4wheelparts.com/')

user_agent = driver.execute_script("return navigator.userAgent;")
cookies = driver.get_cookies()

for elem in cookies:
    if "__cf_bm" in elem['name']:
        cf_bm_cookie = elem['value']

driver.quit()


# Initialize lists
data_columns = ['Taxonomy', 'End Level', 'Brand', 'Product Title', 'Part Number', 'Sale Price', 'Strike Price', 'Description', 'Features', 'Product URL']
spec_columns = ['Product URL', 'Part Number', 'End Level', 'Attribute Name', 'Attribute Value']
media_columns = ['Product URL', 'Model Number', 'End Level', 'Media Name', 'Media Url', 'Media Count']

data, specs, media = [], [], []

url_categories = ['https://www.4wheelparts.com/b/suspension/suspension-air-helper-spring/_/N-cm5hy#SKU', 
                  'https://www.4wheelparts.com/b/suspension/monotube-shocks/_/N-11ltdwp']

cookies = {'__cf_bm': cf_bm_cookie}
headers = {'User-Agent': user_agent}


# Funtion to fetch all products inside each category
def fetch_category(category_url):

    page_left = True
    product_count = 0
    
    while(page_left):

        

        response = requests.get(category_url, cookies=cookies, headers=headers)

        print(f'Entered Category with Status Code: {response.status_code}')

        print(category_url)

        

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            product_titles = soup.find_all('h2', class_="plp-h2")
            product_links = [title.a['href'] for title in product_titles]

            print(len(product_links))

            total_product = int(soup.find('input', id='totalProduct-sku')['value'])

            product_count += 24

            #Stopping Condition
            if product_count > total_product:
                product_count = total_product
                page_left = False


            pagination_url = f'https://www.4wheelparts.com/b/suspension/suspension-air-helper-spring/_/N-cm5hy?SNo={product_count}&SNrpp=24&skuSelectedTab=true'

            
            category_url = pagination_url   #Changing category_url by the pagination one to navegate to all product pages in the category


            def fetch_product(product_url):
                print(f"Entering URL: {product_url} ...")
                try:
                    product_html = requests.get(product_url, cookies=cookies, headers=headers)
                    product_html.raise_for_status()
                    product_soup = BeautifulSoup(product_html.text, 'html.parser')
                except requests.RequestException as e:
                    print(f"Error fetching {product_url}: {e}")
                    return

                # Extract data
                taxonomy = '|'.join([elem.text.strip() for elem in product_soup.find('ol', class_='breadcrumb').find_all('li')])
                end_level = product_soup.find('ol', class_='breadcrumb').find_all('li')[-1].text.strip()
                brand = product_soup.find('li', class_='sku-part-number-container').a.text.strip()
                title = product_soup.find('h1', class_='sku-display-name').text.strip()
                part_number = product_soup.find('li', class_='sku-part-number-container').span.text.strip().split(':')[1][4:]
                description = product_soup.find('div', id='Features').p.text.strip()
                sale_price = product_soup.find('div', class_='sku-price-details').h3.span.text.strip()
                strike_price = product_soup.find('span', class_='listPrice-strike').text.strip() if product_soup.find('span', class_='listPrice-strike') else None
                features = product_soup.find('div', class_='sku-details-page').find('li', class_='bullets-').text.strip()

                # Append to lists
                data.append([taxonomy, end_level, brand, title, part_number, sale_price, strike_price, description, features, product_url])

                # Extract specifications
                list_li = product_soup.find('div', id='specsSection').find_all('li')
                for li in list_li:
                    specs.append([product_url, 
                                end_level, 
                                part_number, 
                                li.text.split(':')[0].strip(), 
                                li.text.split(':')[1].strip()])

                # Extract media
                media_counter = 0
                list_img = product_soup.find('div', class_='product-main').find_all('img')
                for img in list_img:
                    media_counter += 1
                    media.append([product_url, end_level, part_number, 'image', img['data-zoom-image'], str(media_counter)])

            

            
            for product_url in product_links:
                fetch_product(product_url)
                print('-' * 80)

            product_titles.clear()
            product_links.clear()


for category_url in url_categories:
    fetch_category(category_url)


# Create DataFrames
df_data = pd.DataFrame(data, columns=data_columns)
df_spec = pd.DataFrame(specs, columns=spec_columns)
df_media = pd.DataFrame(media, columns=media_columns)

# Write to Excel
with pd.ExcelWriter('Editable Output Template - 4wheel_parts copy.xlsx') as writer:
    df_data.to_excel(writer, sheet_name='Data', index=False)
    df_spec.to_excel(writer, sheet_name='Specification', index=False)
    df_media.to_excel(writer, sheet_name='Media', index=False)
