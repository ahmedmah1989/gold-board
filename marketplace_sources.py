"""Strict, seller-specific iSagha marketplace observations, not platform-wide prices."""
import json
import math
import re
from html import unescape


def text(value):
    return re.sub(r'\s+', ' ', unescape(re.sub(r'<[^>]+>', ' ', value))).strip()


def parse_isagha_product(html, expected):
    products = []
    for raw in re.findall(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.S):
        try:
            p = json.loads(raw)
            if isinstance(p, dict) and p.get('@type') == 'Product':
                products.append(p)
        except ValueError:
            continue
    if len(products) != 1:
        raise ValueError('ambiguous_product')
    p = products[0]
    offer = p.get('offers', {})
    if str(p.get('sku')) != expected['sku'] or p.get('url') != expected['url'] or offer.get('url') != expected['url']:
        raise ValueError('identity_mismatch')
    if p.get('brand', {}).get('name') != 'بي تي سي BTC' or offer.get('priceCurrency') != 'EGP':
        raise ValueError('identity_mismatch')
    rows = {}
    for row in re.findall(r'<tr\b[^>]*>(.*?)</tr>', html, re.S):
        label = re.search(r'<th\b[^>]*>(.*?)</th>', row, re.S)
        value = re.search(r'<td\b[^>]*>(.*?)</td>', row, re.S)
        if label and value:
            k = text(label[1])
            if k in rows:
                raise ValueError('ambiguous_product_table')
            rows[k] = text(value[1])
    if rows.get('صاحب المنتج') != expected['seller'] or rows.get('كود المنتج') != expected['sku']:
        raise ValueError('seller_or_sku_mismatch')
    if rows.get('العيار') != 'عيار '+str(expected['karat']) or float(rows.get('وزن المنتج', 'nan')) != expected['weight']:
        raise ValueError('identity_mismatch')
    if rows.get('الماركة') != 'بي تي سي BTC':
        raise ValueError('identity_mismatch')
    price = offer.get('price')
    if type(price) not in (float, int) or not math.isfinite(price) or price <= 0:
        raise ValueError('invalid_product_price')
    visible = re.findall(r'<p\b[^>]*data-testid=["\']product-price["\'][^>]*>(.*?)</p>', html, re.S)
    if len(visible) != 1:
        raise ValueError('missing_visible_price')
    value = re.search(r'data-testid=["\']price-figure["\'][^>]*>([\d.,]+)</span>', visible[0])
    table_price = re.fullmatch(r'([\d.,]+) جنيه', rows.get('سعر المنتج', ''))
    if not value or not table_price or any(abs(float(v.replace(',', ''))-price) > .01 for v in (value[1],table_price[1])):
        raise ValueError('price_mismatch')
    desc = text(p.get('description', ''))
    if not re.search(r'وزن\s*'+re.escape(str(expected['weight']))+r'\s*جرام', desc) or 'عيار '+str(expected['karat']) not in desc:
        raise ValueError('identity_mismatch')
    return {'listedPrice':price, 'sourceTime':None, 'inStock':True if offer.get('availability')=='https://schema.org/InStock' else False if offer.get('availability')=='https://schema.org/OutOfStock' else None,
            'identityVerified':True, 'marketplace':'iSagha', 'seller':expected['seller'],
            'manufacturingIncluded':None, 'taxIncluded':None, 'stampIncluded':None, 'shippingIncluded':None,
            'reason':'سعر المنتج لدى البائع المحدد عبر آي صاغة؛ وقت تسعير المنتج وشمول الرسوم غير مثبتين، والإجمالي يراجع قبل الشراء.'}
