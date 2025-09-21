# 3_update_latest.py
import requests
from bs4 import BeautifulSoup
import json
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth

BASE_URL = "https://aniwatchtv.to"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Referer': 'https://aniwatchtv.to/'
}

def setup_selenium_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    stealth(driver, languages=["en-US", "en"], vendor="Google Inc.", platform="Win32", webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True)
    return driver

def get_soup(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

def get_stream_url(driver, watch_page_url):
    if not watch_page_url: return None
    print(f"  -> Mengambil stream dari: {watch_page_url}")
    try:
        driver.get(watch_page_url)
        wait = WebDriverWait(driver, 30)
        iframe = wait.until(EC.presence_of_element_located((By.ID, "iframe-embed")))
        time.sleep(5)
        stream_src = iframe.get_attribute('src')
        if stream_src and ('megacloud' in stream_src or 'vidstream' in stream_src):
            print(f"    -> Ditemukan: {stream_src[:70]}...")
            return stream_src
        return None
    except Exception:
        print(f"    -> Gagal mendapatkan iframe.")
        return None

def scrape_homepage_sections(soup):
    data = {'spotlight': [], 'latest_episodes': []}
    if not soup: return data
    # Spotlight
    slider = soup.find('div', id='slider')
    if slider:
        for item in slider.find_all('div', class_='deslide-item'):
            title_el = item.find('div', class_='desi-head-title')
            watch_now_el = item.find('a', class_='btn-primary')
            if not title_el or not watch_now_el: continue
            data['spotlight'].append({
                'title': title_el.text.strip(),
                'watch_url': f"{BASE_URL}{watch_now_el['href']}",
                'image_url': item.find('img', class_='film-poster-img').get('data-src'),
            })
    # Latest Episodes
    section = soup.find('section', class_='block_area_home')
    if section:
        for item in section.find_all('div', class_='flw-item'):
            title_el = item.find('h3', class_='film-name').find('a')
            if not title_el or not title_el.has_attr('href'): continue
            detail_slug = title_el['href']
            data['latest_episodes'].append({
                'title': title_el.get('title', '').strip(),
                'watch_url': f"{BASE_URL}/watch{detail_slug}",
                'image_url': item.find('img', class_='film-poster-img').get('data-src'),
            })
    return data

def main():
    print("Memulai scraper update terbaru...")
    home_soup = get_soup(f"{BASE_URL}/home")
    homepage_data = scrape_homepage_sections(home_soup)

    if not homepage_data['spotlight'] and not homepage_data['latest_episodes']:
        print("Gagal mengambil data dari halaman utama. Proses dihentikan.")
        return

    print("Menyiapkan driver Selenium dengan mode STEALTH...")
    driver = setup_selenium_driver()
    for section in ['spotlight', 'latest_episodes']:
        for anime in homepage_data[section]:
            time.sleep(random.uniform(2, 4))
            anime['stream_url'] = get_stream_url(driver, anime['watch_url'])
    driver.quit()

    with open('anime_homepage.json', 'w', encoding='utf-8') as f:
        json.dump(homepage_data, f, ensure_ascii=False, indent=2)
    print("\nData halaman utama berhasil diperbarui di 'anime_homepage.json'")

if __name__ == "__main__":
    main()