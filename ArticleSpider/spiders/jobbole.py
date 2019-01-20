# -*- coding: utf-8 -*-
import scrapy
from scrapy.loader import ItemLoader

from ArticleSpider.items import ArticlespiderItem, ArticleItemLoader


class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/']

    def parse(self, response):
        front_image_url =
        # item_loader = ItemLoader(item=ArticlespiderItem(),response=response)
        item_loader = ArticleItemLoader(item=ArticlespiderItem(),response=response)
        item_loader.add_xpath('title', '//div')
        item_loader.add_value('url', response.url)
        item_loader.add_value('front_image_url', [front_image_url])

        article_item = item_loader.load_item()
        yield article_item
