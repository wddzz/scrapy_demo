# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose, TakeFirst, Join

# 使用scrapy Django item来处理item


def date_convert(value):
    return value + 'jobbole'


def return_value(value):
    # 结果取值列表
    return value


class ArticleItemLoader(ItemLoader):
    # 自定义itemloader
    default_output_processor = TakeFirst()  # 结果取列表第一个值


class ArticlespiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title = scrapy.Field(
        output_processor=Join(',')
    )
    url = scrapy.Field()
    create_date = scrapy.Field(
        input_processor=MapCompose(date_convert)
    )
    url_object_id = scrapy.Field()
    front_image_url = scrapy.Field(
        output_processor=MapCompose(return_value)
    )
    front_image_path = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
                    insert into jobbole_article(title,url,create_date)
                    VALUES (%s,%s,%s)
                """
        params = (self['title'], self['url'], self['create_date'])
        return insert_sql, params


class ZhihuQuestionItem(scrapy.Item):
    # 知乎的问题item
    zhihu_id = scrapy.Field()
    topics = scrapy.Field()

    def get_insert_sql(self):
        # 插入知乎question表的SQL语句
        insert_sql = """insert into zhihu_answer(zhihu_id, url, question_id, content,update_time)
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE content=VALUES(content), update_time=VALUES(update_time)
        """
        params = "......"
        return insert_sql, params


class ZhihuAnswerItem(scrapy.Item):
    # 知乎的问题回答item
    zhihu_id = scrapy.Field()
    url = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """......"""
        params = """......"""
        return insert_sql, params