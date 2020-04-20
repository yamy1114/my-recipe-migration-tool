import os
import re
import time
import traceback
from IPython import embed

from notion.client import NotionClient
from notion.block import BulletedListBlock, NumberedListBlock, TextBlock, HeaderBlock, ImageBlock, CalloutBlock

NOTION_TOKEN = os.environ['NOTION_TOKEN']

class NotionRecipeTool:
    NOTION_RECIPE_PAGE_URL = 'https://www.notion.so/11c19a60d8f7497ea65cccc088019472'

    def __init__(self, token_id):
        client = NotionClient(token_id)
        recipe_page = client.get_block(self.NOTION_RECIPE_PAGE_URL)
        self.recipes = recipe_page.collection.get_rows()
        embed()

    def get_recipes(self):
        return self.recipes

notion_recipe_tool = NotionRecipeTool(NOTION_TOKEN)
