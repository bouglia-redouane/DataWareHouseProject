# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

from .items import Categorie, SubCategorie, Course, Instructor, Organization
from .utils import *
import re

class UdemyPipeline:
    def process_item(self, item, spider):
        if isinstance(item, Organization):
            return self.process_organization(item)
        elif isinstance(item, Categorie):
            return self.process_categorie(item)
        elif isinstance(item, SubCategorie):
            return self.process_sub_categorie(item)
        elif isinstance(item, Course):
            return self.process_course(item)
        return item
    def process_organization(self, item):
        item['desc'] = list_to_string(item['desc'])
        item['id'] = string_to_id(item['name'])
        return item

    def process_sub_categorie(self, item):
        item['categorie_id'] = string_to_id(item['categorie_id'])
        return item

    def process_categorie(self, item):
        id = re.search(r'/([^/]+)/$', item['link']).group(1)
        item['id'] = string_to_id(id)
        return item

    def process_course(self, item):
        item['duration'] = item['duration'].replace('\xa0', ' ')
        item['rating'] = item['rating'].replace('\xa0', ' ')
        return item

class PostgreSQLConnection:
    pass