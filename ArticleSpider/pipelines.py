# -*- coding: utf-8 -*-
import codecs
import json
import pymysql
import pymysql.cursors
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exporters import JsonItemExporter
from twisted.enterprise import adbapi

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html


class ArticlespiderPipeline(object):
    def process_item(self, item, spider):
        return item


class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        if 'front_image_url' in item:
            for ok, value in results:
                images_file_path = value['path']
            item['front_image_path'] = images_file_path
        return item


class JsonWithEncodingPipeline(object):
    # 自定义json文件的导出
    def __init__(self):
        self.file = codecs.open('article.json', 'w', encoding='utf-8')

    def process_item(self,item,spider):
        lines = json.dumps(dict(item),ensure_ascii=False) + '\n'
        self.file.write(lines)
        return item

    def spider_closed(self,spider):
        self.file.close()


class JsonExporterPipeline(object):
    # 使用scrapy提供的json export导出json文件
    def __init__(self):
        self.file = open('articleexport.json', 'wb')
        self.exporter = JsonItemExporter(self.file, encoding='utf-8')
        self.exporter.start_exporting()

    def spider_closed(self,spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item


class MysqlPipeline(object):
    # 采用同步的方式将数据写入kafka
    def __init__(self):
        self.conn = pymysql.connect('host', 'user', 'password', 'dbname', charset='utf8', use_unicode=True)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        insert_sql = """
            insert into jobbole_article(title,url,create_date)
            VALUES (%s,%s,%s)
        """
        try:
            self.cursor.execute(insert_sql, (item['title'], item['url'], item['create_date']))
            self.conn.commit()
        except:
            self.conn.rollback()

    def spider_closed(self):
        self.conn.close()


class MysqlTwistedPipline(object):
    def __init__(self,dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_setting(cls,setting):
        dbparms = dict(
            host=setting['MYSQL_HOST'],
            db=setting['MYSQL_DBNAME'],
            user=setting['MYSQL_USER'],
            passwd=setting['MYSQL_PASSWORD'],
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor,
            use_unicode=True
        )
        dbpool = adbapi.Connection('MySQLdb', **dbparms)
        return cls(dbpool)

    def process_item(self, item, spider):
        # 使用twisted将mysql插入变成异步执行
        query = self.dbpool.runInteraction(self.do_insert,item)
        query.addErrback(self.handle_error, item, spider)  # 处理异常

    def handle_error(self, failure, item, spider):
        print(failure)

    def do_insert(self, cursor, item):
        # 执行具体的插入
        # 根据不同的item构建不同的SQL语句并插入到mysql中
        insert_sql, params = item.get_insert_sql()
        cursor.execute(insert_sql, (item['title'], item['url'], item['create_date']))

        # insert_sql = """
        #         insert into jobbole_article(title,url,create_date)
        #         VALUES (%s,%s,%s)
        # """
        # cursor.execute(insert_sql, (item['title'], item['url'], item['create_date']))
