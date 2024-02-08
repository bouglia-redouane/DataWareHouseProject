from ..items import Categorie, SubCategorie, Course, Instructor, Organization, CourseOrganization, CourseInstructor, InstructorOrganization
import scrapy
import re
import httpx
import json
from scrapy_playwright.page import PageMethod
from ..utils import string_to_id

class UdemySpiderSpider(scrapy.Spider):
    name = "udemy_spider"
    allowed_domains = ["www.udemy.com"]
    start_urls = {"general": "https://www.udemy.com/fr/",
                  "main": "https://www.udemy.com",
                  "contact": "https://about.udemy.com/fr/societe/"}

    custom_settings = {
        'ITEM_PIPELINES': {
            'scraping.pipelines.UdemyPipeline': 300,
        }
    }


    def __init__(self, max_item=1, platform_name="Udemy", platform_type="online", *args, **kwargs):
        super(UdemySpiderSpider, self).__init__(*args, **kwargs)
        self.max_item=max_item
        self.platform_name=platform_name
        self.platform_type=platform_type
        self.platform_id=string_to_id(platform_name)

    def start_requests(self):
        """yield scrapy.Request(
            self.start_urls['contact'],
            callback=self.parse_organization,
            meta=dict(playwright=True))"""

        yield scrapy.Request(
            self.start_urls['general'],
            callback=self.parse,
            meta=dict(playwright=True))

    def parse(self, response):

        """for categorie in self.parse_categories(response):
            yield categorie
            break"""

        for sub_categorie in self.parse_sub_categories(response):
            for item in self.parse_courses(sub_categorie, max_item=self.max_item):
                yield item
                break
            break
            """yield sub_categorie
            break"""

    def parse_categories(self, response):
        for categorie in response.xpath('//nav/a[@class = "js-side-nav-cat"]'):
            yield Categorie(name=categorie.xpath("./text()").get(), link=self.start_urls['main']+categorie.xpath("./@href").get())

    def parse_sub_categories(self, response):
        pattern = r'/courses/([^/]+)'
        tmp = SubCategorie()
        for sub_categorie in response.xpath('//a[contains(@class, "js-subcat")]'):
            tmp['name'] = sub_categorie.xpath("./text()").get()
            tmp['link'] = self.start_urls['main']+sub_categorie.xpath("./@href").get()
            tmp['id'] = sub_categorie.xpath("./@data-id").get()
            tmp['categorie_id'] = re.search(pattern, tmp['link']).group(1)
            yield tmp

    def parse_courses(self, sub_categorie, max_item):
        counter = 1
        url = sub_categorie['link']+"?p="+str(counter)
        while (self.check_url(sub_categorie['id'], counter) == True) and (counter <= max_item):
            yield scrapy.Request(
                url,
                callback=self.parse_course,
                meta=dict(
                    playwright=True,
                    playwright_page_methods=[PageMethod('wait_for_selector', '.pagination-module--container--1Dmb0')],
                    sub_cat_id=sub_categorie['id']
                ))
            counter = counter + 1
            url = sub_categorie['link']+"?p="+str(counter)

    def parse_course(self, response):
        title, urls, img_urls, ids, desc, rating, num_reviews, duration, level, price, type, sub_categorie_id = self.get_courses_details(response)
        if len(urls) > 0:
            tmp = Course()
            for i in range(len(urls)):
                tmp['id'] = ids[i]
                tmp['url'] = self.start_urls['main']+urls[i]
                tmp['img_url'] = img_urls[i]
                tmp['title'] = title[i]
                tmp['desc'] = desc[i]
                tmp['rating'] = rating[i]
                tmp['num_reviews'] = num_reviews[i]
                tmp['duration'] = duration[i]
                tmp['price'] = price[i]
                tmp['level'] = level[i]
                tmp['type'] = type
                tmp['sub_categorie_id'] = sub_categorie_id
                url = f'https://www.udemy.com/api-2.0/courses/{ids[i]}/?fields[course]=visible_instructors'
                yield tmp
                yield CourseOrganization(course_id=ids[i], organization_id=self.platform_id)
                yield scrapy.Request(
                        url,
                        callback=self.parse_instructors,
                        meta=dict(
                            playwright=True,
                            course_id=ids[i]
                        )
                    )

    def get_courses_details(self, response):
        title = response.xpath('//div[@class="course-list--container--FuG0T"]//h3[@data-purpose="course-title-url"]/a/text()').extract()
        urls = response.xpath('//div[@class="course-list--container--FuG0T"]//h3[@data-purpose="course-title-url"]/a/@href').extract()
        img_urls = response.xpath('//div[@class="course-list--container--FuG0T"]//img[contains(@class, "course-card-image-module--image--3V2QD")]/@src').extract()
        ids = [re.search(r"/(\d+)_", img_url).group(1) for img_url in img_urls]
        desc = response.xpath('//div[@class="course-list--container--FuG0T"]//h3[@data-purpose="course-title-url"]//span[@data-testid="seo-headline"]/text()').extract()
        rating = response.xpath('//div[@class="course-list--container--FuG0T"]//h3[@data-purpose="course-title-url"]//span[@data-testid="seo-rating"]/text()').extract()
        num_reviews = response.xpath('//div[@class="course-list--container--FuG0T"]//h3[@data-purpose="course-title-url"]//span[@data-testid="seo-num-reviews"]/text()').extract()
        duration = response.xpath('//div[@class="course-list--container--FuG0T"]//h3[@data-purpose="course-title-url"]//span[@data-testid="seo-content-info"]/text()').extract()
        level = response.xpath('//div[@class="course-list--container--FuG0T"]//h3[@data-purpose="course-title-url"]//span[@data-testid="seo-instructional-level"]/text()').extract()
        price = self.get_prices(ids)
        type = self.platform_type
        sub_categorie_id = response.meta['sub_cat_id']
        return title, urls, img_urls, ids, desc, rating, num_reviews, duration, level, price, type, sub_categorie_id

    def parse_instructors(self, response):
        response_dict = json.loads(response.xpath("//pre/text()").get())['visible_instructors']
        for val in response_dict:
            id = re.search(r'50x50/(\d+)_', val['image_50x50']).group(1)
            yield Instructor(id=id,
                             name=val['display_name'],
                             desc=val['job_title'],
                             url=self.start_urls['main']+val['url'])
            yield CourseInstructor(course_id=response.meta['course_id'], instructor_id=id)
            yield InstructorOrganization(instructor_id=id, organization_id=self.platform_id)

    def parse_organization(self, response):
        organization = Organization()
        organization['name'] = response.xpath('//img[contains(@class, "udemy-logo")]/@alt').get()
        organization['img_url'] = response.xpath('//img[contains(@class, "udemy-logo")]/@src').get()
        organization['desc'] = response.xpath('//div[@class = "origins__article"]//text()').extract()
        organization['contact_url'] = response.xpath('//div[@class="leadership__desc"]//a/@href').get()
        self.platform_id = organization['name']
        yield organization

    def check_url(self, id, page):
        url = f'https://www.udemy.com/api-2.0/discovery-units/all_courses/?p={page}&page_size=16&subcategory=&instructional_level=&lang=&price=&duration=&closed_captions=&subs_filter_type=&subcategory_id={id}&source_page=subcategory_page&locale=fr_FR&currency=usd&navigation_locale=en_US&skip_price=true&sos=ps&fl=scat'
        response = self.make_http_request(url)
        if response.status_code != 200:
            return False
        return True

    def get_prices(self, ids):
        tmp = ["pas disponible"] * (len(ids))
        url = f"https://www.udemy.com/api-2.0/pricing/?course_ids={','.join(ids)}&fields[pricing_result]=price"
        response = self.make_http_request(url)
        if response.status_code == 200:
            response_dict = json.loads(response.text)
            courses = response_dict['courses']
            for i, value in enumerate(courses.values()):
                tmp[i] = f"{value['price']['amount']} {value['price']['currency_symbol']}"
        return tmp

    def make_http_request(self, url):
        with (httpx.Client() as client):
            response = client.get(url, headers={"User-Agent": self.settings.get('USER_AGENT')})
        return response
