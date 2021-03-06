# coding: utf-8
from pulsar import provider
import re
import common
from itertools import chain

# this read the settings
settings = common.Settings()
# define the browser
browser = common.Browser()
# create the filters
filters = common.Filtering()
# special settings
values2 = {"ALL": '', "Hide remakes": 'remake', "Trusted/A+ only": 'trusted',
           "A+ only": 'aplus'}  # read category
category = values2[provider.ADDON.getSetting('category')]


# using function from Steeve to add Provider's name and search torrent
def extract_torrents(data):
    try:
        filters.information()  # print filters settings
        data = common.clean_html(data)
        name = re.findall(r'<div class="link"><a href=".*?">(.*?)</a>',data) # find all names
        size = re.findall(r'<div class="size" title=".*?">(.*?)</div>',data) # find all sizes
        cont = 0
        for cm, torrent in enumerate(re.findall(r'<a href="(.*?)" class="dllink">Torrent</a>', data)):
            #find name in the torrent
            nm = name[cm].replace('<wbr/>', '')
            if filters.verify(nm, size[cm]):
                yield { "name": nm + ' - ' + size[cm] + ' - ' + settings.name_provider, "uri": torrent}
                cont += 1
            else:
                provider.log.warning(filters.reason)
            if cont == settings.max_magnets:  # limit magnets
                break
        provider.log.info('>>>>>>' + str(cont) + ' torrents sent to Pulsar<<<<<<<')
    except:
        provider.log.error('>>>>>>>ERROR parsing data<<<<<<<')
        provider.notify(message='ERROR parsing data', header=None, time=5000, image=settings.icon)


def get_titles(title, tvdb_id):
    url_tvdb = "http://www.thetvdb.com/api/GetSeries.php?seriesname=%s" % provider.quote_plus(title)
    provider.log.info(url_tvdb)
    if browser.open(url_tvdb):
        pat = re.compile('<seriesid>%d</seriesid>.*?<AliasNames>(.*?)</AliasNames>' % tvdb_id, re.I | re.S)
        show = pat.search(browser.content) # find all aliases
        if show:
            aliases = show.group(1).strip()
            provider.log.info("Aliases: " + aliases)
            return [ title ] + aliases.split('|')
    return [ title ]


def search(query):
    global filters
    filters.title = query  # to do filtering by name
    query += ' ' + settings.extra
    if settings.time_noti > 0: provider.notify(message="Searching: " + query.title() + '...', header=None, time=settings.time_noti, image=settings.icon)
    query = provider.quote_plus(query.rstrip())
    param = r'?filter%5B0%5D%5Bt%5D=nyaa_class&filter%5B0%5D%5Bv%5D=' + category if category else ''
    url_search = "%s/search/%s%s" % (settings.url, query, param)  # change in each provider
    provider.log.info(url_search)
    if browser.open(url_search):
        results = extract_torrents(browser.content)
    else:
        provider.log.error('>>>>>>>%s<<<<<<<' % browser.status)
        provider.notify(message=browser.status, header=None, time=5000, image=settings.icon)
        results = []
    return results


def search_movie(info):
    return []


def search_episode(info):
    iters = []
    filters.use_TV()
    titles = get_titles(info['title'], info['tvdb_id'])
    for title in titles:
        query = common.clean(title) + ' %02d' % info['absolute_number']
        iters.append(search(query))
    return chain.from_iterable(iters)

# This registers your module for use
provider.register(search, search_movie, search_episode)
