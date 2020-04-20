import os
import re
import time
import traceback
from IPython import embed

from notion.client import NotionClient
from notion.block import BulletedListBlock, NumberedListBlock, TextBlock, HeaderBlock, ImageBlock, CalloutBlock

import chromedriver_binary
from selenium import webdriver

NOTION_TOKEN = os.environ['NOTION_TOKEN']
EVERNOTE_USERNAME = os.environ['EVERNOTE_USERNAME']
EVERNOTE_PASSWORD = os.environ['EVERNOTE_PASSWORD']

class EvernoteScraper:
    EVERNOTE_URL = 'https://www.evernote.com/Home.action?login=true'

    def __init__(self):
        self.login()

    def login(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10)
        self.driver.set_window_size(5000, 5000)

        self.driver.get(self.EVERNOTE_URL)

        self.driver.find_element_by_css_selector('#email-wrapper input').send_keys(EVERNOTE_USERNAME)
        self.driver.find_element_by_css_selector('#loginButton').click()
        self.driver.find_element_by_css_selector('#password-wrapper input').send_keys(EVERNOTE_PASSWORD)
        self.driver.find_element_by_css_selector('#loginButton').click()

    def get_ingredient_tags(self, title):
        title = re.sub(' 【クックパッド】 簡単おいしいみんなのレシピが32.万品', '', title)

        self.driver.find_element_by_css_selector('#gwt-debug-Sidebar-searchButton-container').click()
        self.driver.find_element_by_css_selector('#gwt-debug-searchViewSearchBox').clear()
        self.driver.find_element_by_css_selector('#gwt-debug-searchViewSearchBox').send_keys("検索結果が0件になる文字列\n")
        self.driver.find_element_by_css_selector('#gwt-debug-searchViewSearchBox').clear()
        self.driver.find_element_by_css_selector('#gwt-debug-Sidebar-searchButton-container').click()
        self.driver.find_element_by_css_selector('#gwt-debug-searchViewSearchBox').send_keys(re.sub(r'・|☆|！|【|】|♡|★|♪|❤|〜|✿|１|２|３|４|５|６|７|８|９|０|❀|（|）|\(|\)|❤|\*|、|。|1|2|3|4|5|6|7|8|9|0|&|＆|「|」|✩|＊|♬|～|♡|＊|？|by.*', ' ', title) + "\n")
        time.sleep(3)

        count = 0
        while True:
            notes = self.driver.find_elements_by_css_selector('.focus-NotesView-Note')
            note_found = False

            for note in notes:
                note_title = note.find_element_by_css_selector('.qa-title').text

                if note_title == title:
                    note_found = True
                    note.click()
                    break

            if note_found:
                break

            time.sleep(1)
            count += 1

            if count > 5:
                raise

            print('note_title: ' + note_title)
            print('recipe.title: ' + title)

        time.sleep(3)

        tag_spans = self.driver.find_elements_by_css_selector('.qa-TagLozenge-name')
        tags = list(map(lambda tag_span: tag_span.text, tag_spans))
        tags = list(map(lambda tag: re.sub(r'ためねぎ', 'たまねぎ', tag), tags))
        return tags

class NotionRecipeTool:
    NOTION_RECIPE_PAGE_URL = 'https://www.notion.so/11c19a60d8f7497ea65cccc088019472'

    def __init__(self, token_id):
        client = NotionClient(token_id)
        recipe_page = client.get_block(self.NOTION_RECIPE_PAGE_URL)
        self.recipes = recipe_page.collection.get_rows()

    def get_recipes(self):
        return self.recipes

notion_recipe_tool = NotionRecipeTool(NOTION_TOKEN)
evernote_scraper = EvernoteScraper()

for recipe in notion_recipe_tool.get_recipes():
    try:
        # url に // が誤って含まれているのを修正しておく
        fixed_url = re.sub(r'cookpad.com//pro', 'cookpad.com/pro', recipe.url)
        recipe.url = fixed_url

        print('start: ' + recipe.title)

        if not (recipe.ingredients == [] or recipe.ingredients == ['']):
            print('skip!')
            continue

        ingredients = evernote_scraper.get_ingredient_tags(recipe.title)
        recipe.ingredients = ingredients

        print('done!')
    except:
        print('error!')
        traceback.print_exc()
