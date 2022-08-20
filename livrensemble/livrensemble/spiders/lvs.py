import scrapy
from scrapy import Request


class LvsSpider(scrapy.Spider):
    name = 'lvs'
    allowed_domains = ['www.livrensemble.be']
    start_urls = ['https://www.livrensemble.be']
    custom_settings = {'ROBOTSTXT_OBEY': False, 'LOG_LEVEL': 'INFO',
                       'CONCURRENT_REQUESTS_PER_DOMAIN': 10,
                       'RETRY_TIMES': 5,
                       'FEED_URI': r'output.xlsx',
                       'FEED_FORMAT': 'xlsx',
                       'FEED_EXPORTERS': {'xlsx': 'scrapy_xlsx.XlsxItemExporter'},
                       }

    def parse(self, response):
        sidebar_categories = response.xpath(
            "//div[@data-elementor-id='99094']/section/div/div[@data-id='e337e04']/div//div[a[contains("
            "span/span/text(),'Livre') or contains(span/span/text(),'Bande dessinée') or contains(span/span/text(),"
            "'Manga') or contains(span/span/text(),'Soldes')]]")
        for sidebar_categorie in sidebar_categories:
            sidebar_link = sidebar_categorie.xpath("./a/@href").get()
            categories = sidebar_categorie.xpath("./div/div/section/div/div/div/section/div/div/div[div/div/h3/a]")
            if categories:
                for category in categories:
                    cat_link = category.xpath("./div/div/h3/a/@href").get()
                    sub_categories = category.xpath(
                        "./div[contains(@class,'elementor-list-item-link')]/div/ul/li/a")
                    if sub_categories:
                        for sub_category in sub_categories:
                            sub_cat_link = sub_category.xpath("./@href").get()
                            yield Request(sub_cat_link, callback=self.parse_listing)
                    else:
                        yield Request(cat_link, callback=self.parse_listing)
            else:
                yield Request(sidebar_link, callback=self.parse_listing)

    def parse_listing(self, response):
        for url in response.xpath("//a[@class='ast-loop-product__link']/@href").extract():
            yield Request(url, callback=self.parse_details)

        next_page_url = response.xpath("//a[@class='next page-numbers']/@href").get()
        if next_page_url:
            if not next_page_url.startswith(self.start_urls[0]):
                next_page_url = self.start_urls[0] + next_page_url
            yield Request(next_page_url, callback=self.parse_listing)

    def parse_details(self, response):
        item = dict()
        item['tile'] = response.xpath("//h1[contains(@class,'product_title')]/text()").get()
        try:
            item['price'] = response.xpath("//p[@class='price']/span/bdi/text()").get() + response.xpath(
                "//p[@class='price']/span/bdi/span/text()").get()
        except:
            item['price'] = response.xpath("//p[@class='price']/ins/span/bdi/text()").get() + response.xpath(
                "//p[@class='price']/ins/span/bdi/span/text()").get()

        item['isnb 13'] = response.xpath("//p[contains(b/text(),'ISNB 13')]/text()").get()
        item['isnb 10'] = response.xpath("//p[contains(b/text(),'ISNB 10')]/text()").get()
        item['condition'] = response.xpath("//p[contains(b/text(),'État du livre :')]/text()").get()
        item['url'] = response.url

        yield item
