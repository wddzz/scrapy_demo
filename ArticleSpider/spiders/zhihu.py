import scrapy
import re
import json
import time
from urllib import parse
from scrapy.loader import ItemLoader
from ArticleSpider.items import ZhihuAnswerItem, ZhihuQuestionItem


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com']
    # question的第一页answer的请求url
    start_answer_url = "https://www.zhihu.com/api/v4/questions/{0}/answer&limit={1}&offset={2}"

    header = {
        'HOST': 'www.zhihu.com',
        'Referer': 'https://www.zhihu.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }

    def parse(self, response):
        """
        提取出html页面中的所有url，并跟踪这些url进行下一步爬取
        如果提取的url中格式为/question/xxx/就下载之后直接进入解析函数
        """
        all_urls = response.css('a::attr(href)').extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        all_urls = filter(lambda x: True if x.startswith('https') else False, all_urls)
        for url in all_urls:
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", url)
            if match_obj:
                request_url = match_obj.group(1)
                question_id = match_obj.group(2)
                yield scrapy.Request(request_url, headers=self.header, callback=self.parse_question)
            else:
                yield scrapy.Request(url, headers=self.header)

    def parse_question(self, response):
        # 处理question页面，从页面中提取出具体的question item
        if 'QuestionHeader-title' in response.text:
            # 处理新版本
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", response.url)
            if match_obj:
                question_id = int(match_obj.group(2))

            item_loader = ItemLoader(item=ZhihuQuestionItem(),response=response.text)
            item_loader.add_css('title', 'h1.QuestionHeader-title::text')
            item_loader.add_css('content', '.QuestionHeader-detail')
            item_loader.add_css('answer_num', '.List-headerText')
            item_loader.add_css('comments_num', '.QuestionHeader-action')

            question_item = item_loader.load_item()
        else:
            # 处理老版本页面的item提取
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", response.url)
            if match_obj:
                question_id = int(match_obj.group(2))

            item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response.text)
            item_loader.add_css('title', 'h1.QuestionHeader-title::text')
            item_loader.add_css('content', '.QuestionHeader-detail')
            item_loader.add_css('answer_num', '.List-headerText span::text')
            item_loader.add_css('comments_num', '#zh-question-meta-wrap a[name="addcomment"]::text')

            question_item = item_loader.load_item()
        yield scrapy.Request(self.start_answer_url.format(question_id,20,0), headers=self.header,callback=self.parse_answer)
        yield question_item

    def parse_answer(self,response):
        # 处理question的answer
        ans_json = json.loads(response.text)
        is_end = ans_json['paging']['is_end']
        totals_answer = ans_json['paging']['totals']
        next_url = ans_json['paging']['next']

        # 提取answer的具体字段
        for answer in ans_json['data']:
            answer_item = ZhihuAnswerItem()
            answer_item['zhihu_id'] = answer['id']
            answer_item['question_id'] = answer['question']['id']

            yield answer_item

        if not is_end:
            yield scrapy.Request(next_url, headers=self.header, callback=self.parse_answer)
    def start_requests(self):
        return [scrapy.Request('https://www.zhihu.com/#signin', headers=self.header, callback=self.login)]

    def login(self, response):
        response_text = response.text
        match_obj = re.match('.*name="_xsrf" value="(.*?)"', response_text, re.DOTALL)
        crsf = ''
        if match_obj:
            crsf = match_obj.group(1)
        if crsf:
            post_data = {
                '_crsf': crsf,
                'phone': '13366666666',
                'password': 'admin123',
                'captcha':''
            }
            t = str(int(time.time() * 1000))
            captcha_url = "https://www.zhihu.com/captcha.gif?r={0}&type=login".format(t)
            yield scrapy.Request(url=captcha_url,headers=self.header,meta={'post_data':post_data},callback=self.after_capter_login)

    def after_capter_login(self,response):
        post_data = response.meta['post_data']
        with open('captcha.jpg', 'wb') as f:
            f.write(response.content)
            f.close()
        from PIL import Image
        try:
            im = Image.open('captcha.jpg')
            im.show()
            im.close()
        except:
            pass

        captcha = input('请输入验证码：')
        post_data['captcha'] = captcha
        post_url = 'https://www.zhihu.com/login/phone_num'
        return [scrapy.FormRequest(url=post_url, formdata=post_data, headers=self.header, callback=self.check_login)]

    def check_login(self, response):
        # 验证是否登录成功
        text_json = json.loads(response.text)
        if 'msg' in text_json and text_json['msg'] == '登录成功':
            for url in self.start_urls:
                yield scrapy.Request(url, dont_filter=True, headers=self.header)
        pass