import os
import re
from IPython import embed

from notion.client import NotionClient
from notion.block import BulletedListBlock, NumberedListBlock, TextBlock, HeaderBlock, ImageBlock, CalloutBlock

import chromedriver_binary
from selenium import webdriver

NOTION_TOKEN = os.environ['NOTION_TOKEN']
COOKPAD_USERNAME = os.environ['COOKPAD_USERNAME']
COOKPAD_PASSWORD = os.environ['COOKPAD_PASSWORD']

class CookpadScraper:
    COOKPAD_LOGIN_URL = 'https://cookpad.com/login'

    def __init__(self):
        self.login()

    def login(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=options)

        self.driver.get(self.COOKPAD_LOGIN_URL)
        login_form = self.driver.find_element_by_class_name('cp_form')
        login_form_email = login_form.find_element_by_id('login_form_email')
        login_form_email.send_keys(COOKPAD_USERNAME)
        login_form_password = login_form.find_element_by_id('login_form_password')
        login_form_password.send_keys(COOKPAD_PASSWORD)
        login_form_button = login_form.find_element_by_class_name('button')
        login_form_button.click()

    def get_recipe_data(self, url):
        self.driver.get(url)

        ingredients = []
        directions = []

        pro_recipe_title = self.driver.find_element_by_class_name('pro_recipe_title')
        description = pro_recipe_title.find_element_by_class_name('description').text

        recipe_ingredients = self.driver.find_element_by_class_name('recipe_ingredients')
        volume_unit = recipe_ingredients.find_element_by_class_name('unit').text
        items = recipe_ingredients.find_elements_by_class_name('item')

        for item in items:
            item_name = item.find_element_by_class_name('item_name').text
            item_unit = item.find_element_by_class_name('item_unit').text
            ingredients.append({
                    'item_name': item_name,
                    'item_unit': item_unit
                })

        recipe_steps = self.driver.find_element_by_class_name('recipe_steps')
        step_texts = recipe_steps.find_elements_by_class_name('text')

        for step_text in step_texts:
            directions.append(step_text.text)

        return [description, volume_unit, ingredients, directions]

class NotionRecipeTool:
    NOTION_RECIPE_PAGE_URL = 'https://www.notion.so/11c19a60d8f7497ea65cccc088019472'

    def __init__(self, token_id):
        client = NotionClient(token_id)
        recipe_page = client.get_block(self.NOTION_RECIPE_PAGE_URL)
        self.recipes = recipe_page.collection.get_rows()

    def get_recipes(self):
        return self.recipes

    def add_recipe_detail(self, recipe, description, volume_unit, ingredients, directions):
        children = recipe.children
        self._clear_blocks_without_first_image(children)

        children.add_new(TextBlock, title='')
        children.add_new(CalloutBlock, title=description, color='brown_background', icon='👨‍🍳')

        children.add_new(HeaderBlock, title='Ingredients')
        children.add_new(CalloutBlock, title=volume_unit, color='brown_background', icon='☝️')

        for ingredient in ingredients:
            children.add_new(BulletedListBlock, title='{item} {unit}'.format(item=ingredient["item_name"], unit=ingredient['item_unit']))
        children.add_new(HeaderBlock, title='Directions')

        for direction in directions:
            children.add_new(NumberedListBlock, title=direction)

    def _clear_blocks_without_first_image(self, blocks):
        image_found = False

        for block in blocks:
            if block.type != 'image':
                block.remove()

            if block.type == 'image':
                if image_found:
                    block.remove()
                else:
                    image_found = True

notion_recipe_tool = NotionRecipeTool(NOTION_TOKEN)
cookpad_scraper = CookpadScraper()

for recipe in notion_recipe_tool.get_recipes():
    # url に // が誤って含まれているのを修正しておく
    fixed_url = re.sub(r'cookpad.com//pro', 'cookpad.com/pro', recipe.url)
    recipe.url = fixed_url

    print('start: ' + recipe.title)

    if recipe.integration_status == 'DONE' or not re.match(r'https://cookpad.com/pro/.*', recipe.url):
        print('skip!')
        continue

    description, volume_unit, ingredients, directions = cookpad_scraper.get_recipe_data(recipe.url)
    notion_recipe_tool.add_recipe_detail(recipe, description, volume_unit, ingredients, directions)
    recipe.integration_status = 'DONE'

    print('done!')
