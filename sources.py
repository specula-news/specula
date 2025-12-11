# Sources for aggregation site - FINAL ADJUSTMENTS (v20.5.28)

SOURCES = [
    # --- NEWS: GLOBAL ---
    {"url":"https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml","cat":"geopolitics","type":"web","source_name":"The New York Times","lang":"en","filter_tag":"global"},
    {"url":"https://www.reutersagency.com/feed/","cat":"geopolitics","type":"web","source_name":"Reuters","lang":"en","filter_tag":"global"},
    {"url":"https://www.theguardian.com/europe","cat":"geopolitics","type":"web","source_name":"The Guardian","lang":"en","filter_tag":"global"},
    {"url":"https://www.bloomberg.com/europe","cat":"geopolitics","type":"web","source_name":"Bloomberg","lang":"en","filter_tag":"global"},
    {"url":"http://rss.cnn.com/rss/edition.rss","cat":"geopolitics","type":"web","source_name":"Cnn","lang":"en","filter_tag":"global"},
    {"url":"https://www.aljazeera.com/xml/rss/all.xml","cat":"geopolitics","type":"web","source_name":"Al Jazeera","lang":"en","filter_tag":"global"},
    {"url":"http://feeds.bbci.co.uk/news/world/rss.xml","cat":"geopolitics","type":"web","source_name":"BBC World","lang":"en","filter_tag":"global"},
    # --- MEDIA: Global ---
    {"url":"https://www.youtube.com/@dwnews/videos","cat":"geopolitics","type":"video","source_name":"DW News","lang":"en","filter_tag":"global"},
    {"url":"https://www.youtube.com/@aljazeeraenglish/videos","cat":"geopolitics","type":"video","source_name":"Al Jazeera English","lang":"en","filter_tag":"global"},
    {"url":"https://www.youtube.com/@BBCNews/videos","cat":"geopolitics","type":"video","source_name":"BBC News","lang":"en","filter_tag":"global"},
    {"url":"https://www.youtube.com/@France24_en/videos","cat":"geopolitics","type":"video","source_name":"France 24","lang":"en","filter_tag":"global"},
    {"url":"https://www.youtube.com/@Asianometry/videos","cat":"geopolitics","type":"video","source_name":"Asianometry","lang":"en","filter_tag":"global"},
    {"url":"https://www.youtube.com/@GeopoliticalEconomyReport/videos","cat":"geopolitics","type":"video","source_name":"Geopolitical Economy","lang":"en","filter_tag":"global"},
    {"url":"https://www.youtube.com/@wocomoDOCS/videos","cat":"geopolitics","type":"video","source_name":"wocomoDOCS","lang":"en","filter_tag":"global"},
    {"url":"https://www.youtube.com/@DWDocumentary/videos","cat":"geopolitics","type":"video","source_name":"DW Documentary","lang":"en","filter_tag":"global"},
    {"url":"https://www.youtube.com/@TheMilitaryShow/videos","cat":"geopolitics","type":"video","source_name":"The Military Show","lang":"en","filter_tag":"global"},
    {"url":"https://www.youtube.com/@asiasociety/videos","cat":"geopolitics","type":"video","source_name":"Asia Society","lang":"en","filter_tag":"global"},
    {"url":"https://www.youtube.com/@VisualPolitikEN/videos","cat":"geopolitics","type":"video","source_name":"VisualPolitik EN","lang":"en","filter_tag":"global"},
    # --- MEDIA: China ---
    {"url":"https://www.youtube.com/@channelnewsasia/videos","cat":"geopolitics","type":"video","source_name":"CNA","lang":"en","filter_tag":"china"},
    {"url":"https://www.youtube.com/@cgtn/videos","cat":"geopolitics","type":"video","source_name":"CGTN","lang":"en","filter_tag":"china"},
    # --- MEDIA: India ---
    {"url":"https://www.youtube.com/@Firstpost/videos","cat":"geopolitics","type":"video","source_name":"Firstpost","lang":"en","filter_tag":"india"},
    # --- YT: Geo ---
    {"url":"https://www.youtube.com/@brdecode123/videos","cat":"youtubers","type":"video","source_name":"BR Decode","lang":"en","filter_tag":"geo"},
    {"url":"https://www.youtube.com/@johnnyharris/videos","cat":"youtubers","type":"video","source_name":"Johnny Harris","lang":"en","filter_tag":"geo"},
    {"url":"https://www.youtube.com/@VisualPolitikEN/videos","cat":"youtubers","type":"video","source_name":"VisualPolitik","lang":"en","filter_tag":"geo"},
    {"url":"https://www.youtube.com/@lenapetrova/videos","cat":"youtubers","type":"video","source_name":"Lena Petrova","lang":"en","filter_tag":"geo"},
    # --- YT: Tech ---
    {"url":"https://www.youtube.com/@Jayztwocents/videos","cat":"youtubers","type":"video","source_name":"Jayztwocents","lang":"en","filter_tag":"tech"},
    {"url":"https://www.youtube.com/@LinusTechTips/videos","cat":"youtubers","type":"video","source_name":"Linus Tech Tips","lang":"en","filter_tag":"tech"},
    {"url":"https://www.youtube.com/@MKBHD/videos","cat":"youtubers","type":"video","source_name":"MKBHD","lang":"en","filter_tag":"tech"},
    {"url":"https://www.youtube.com/@Hardwareunboxed/videos","cat":"youtubers","type":"video","source_name":"Hardware Unboxed","lang":"en","filter_tag":"tech"},
    {"url":"https://www.youtube.com/@der8auer-en/videos","cat":"youtubers","type":"video","source_name":"der8auer","lang":"en","filter_tag":"tech"},
    # --- YT: Energy ---
    {"url":"https://www.youtube.com/@veritasium/videos","cat":"youtubers","type":"video","source_name":"Veritasium","lang":"en","filter_tag":"energy"},
    {"url":"https://www.youtube.com/@smartereveryday/videos","cat":"youtubers","type":"video","source_name":"SmarterEveryDay","lang":"en","filter_tag":"energy"},
    # --- YT: EV ---
    {"url":"https://www.youtube.com/@FullyChargedShow/videos","cat":"youtubers","type":"video","source_name":"Fully Charged","lang":"en","filter_tag":"ev"},
    {"url":"https://www.youtube.com/@electricviking/videos","cat":"youtubers","type":"video","source_name":"Electric Viking","lang":"en","filter_tag":"ev"},
    # --- YT: Gaming ---
    {"url":"https://www.youtube.com/@AsmonTV/videos","cat":"youtubers","type":"video","source_name":"AsmonTV","lang":"en","filter_tag":"gaming"},
    {"url":"https://www.youtube.com/@gameranxTV/videos","cat":"youtubers","type":"video","source_name":"Gameranx","lang":"en","filter_tag":"gaming"},
    # --- GAME: News ---
    {"url":"https://www.eurogamer.net/feed","cat":"gaming","type":"web","source_name":"Eurogamer","lang":"en"},
    {"url":"https://www.pcgamer.com/rss","cat":"gaming","type":"web","source_name":"PC Gamer","lang":"en"},
    {"url":"https://www.fz.se/feeds/nyheter","cat":"gaming","type":"web","source_name":"FZ.se","lang":"sv"},
    # --- GAME: Video ---
    {"url":"https://www.youtube.com/@gamespot/videos","cat":"gaming","type":"video","source_name":"GameSpot","lang":"en","filter_tag":"gaming"},
    {"url":"https://www.youtube.com/@IGN/videos","cat":"gaming","type":"video","source_name":"IGN","lang":"en","filter_tag":"gaming"},
    {"url":"https://www.youtube.com/@ewc/videos","cat":"gaming","type":"video","source_name":"Esports World Cup","lang":"en"},
    {"url":"https://www.youtube.com/@esl/videos","cat":"gaming","type":"video","source_name":"ESL","lang":"en"},
    # --- TOPIC: Tech ---
    {"url":"https://www.sweclockers.com/feeds/nyheter","cat":"tech","type":"web","source_name":"Sweclockers","lang":"en"},
    {"url":"https://www.nyteknik.se/nyheter/ny-teknik-i-rrs-format/972205","cat":"tech","type":"web","source_name":"Nyteknik","lang":"en"},
    {"url":"https://www.theverge.com/rss/index.xml","cat":"tech","type":"web","source_name":"The Verge","lang":"en"},
    {"url":"https://www.theverge.com/rss/index.xml","cat":"tech","type":"web","source_name":"The Verge","lang":"en"},
    {"url":"https://techcrunch.com/feed/","cat":"tech","type":"web","source_name":"TechCrunch","lang":"en"},
    {"url":"https://feeds.arstechnica.com/arstechnica/index","cat":"tech","type":"web","source_name":"Ars Technica","lang":"en"},
    {"url":"https://anastasiintech.substack.com/feed","cat":"tech","type":"web","source_name":"Anastasi In Tech","lang":"en"},
    {"url":"https://feber.se/rss/","cat":"tech","type":"web","source_name":"Feber","lang":"sv"},
    {"url":"https://www.wired.com/feed/rss","cat":"tech","type":"web","source_name":"WIRED","lang":"en"},
    {"url":"https://www.engadget.com/rss.xml","cat":"tech","type":"web","source_name":"Engadget","lang":"en"},
    {"url":"https://mashable.com/feeds/rss/tech","cat":"tech","type":"web","source_name":"Mashable","lang":"en"},
    # --- TOPIC: Energy ---
    {"url":"https://energy.economictimes.indiatimes.com/rss/recentstories","cat":"energy","type":"web","source_name":"ET EnergyWorld","lang":"en"},
    {"url":"https://energydigital.com/feed","cat":"energy","type":"web","source_name":"Energy Digital","lang":"en"},
    {"url":"https://www.breakthroughenergy.org/news","cat":"energy","type":"web","source_name":"Breakthrough Energy","lang":"en"},
    {"url":"https://oilprice.com/rss/main","cat":"energy","type":"web","source_name":"OilPrice","lang":"en"},
    {"url":"https://www.renewableenergyworld.com/feed/","cat":"energy","type":"web","source_name":"Renewable Energy World","lang":"en"},
    # --- TOPIC: EV ---
    {"url":"https://insideevs.com/rss/articles/all/","cat":"ev","type":"web","source_name":"InsideEVs","lang":"en"},
    {"url":"https://electrek.co/feed/","cat":"ev","type":"web","source_name":"Electrek","lang":"en"},
    {"url":"https://cleantechnica.com/feed/","cat":"ev","type":"web","source_name":"CleanTechnica","lang":"en"},
    {"url":"https://oilprice.com/rss/main","cat":"ev","type":"web","source_name":"OilPrice","lang":"en"},
    {"url":"https://teslaclubsweden.se/feed/","cat":"ev","type":"web","source_name":"Tesla Club Sweden","lang":"sv"},
    {"url":"https://alltomelbil.se/feed/","cat":"ev","type":"web","source_name":"Allt om Elbil","lang":"sv"},
    {"url":"https://elbilen.se/feed/","cat":"ev","type":"web","source_name":"Elbilen.se","lang":"sv"},
    # --- TOPIC: Science ---
    {"url":"https://www.space.com/feeds/all","cat":"science","type":"web","source_name":"Space.com","lang":"en"},
    {"url":"https://www.nasa.gov/rss/dyn/breaking_news.rss","cat":"science","type":"web","source_name":"NASA","lang":"en"},
    {"url":"https://www.youtube.com/@pbsspacetime/videos","cat":"science","type":"video","source_name":"PBS Space Time","lang":"en"},
    {"url":"https://www.youtube.com/@Kurzgesagt/videos","cat":"science","type":"video","source_name":"Kurzgesagt","lang":"en"},
    # --- TOPIC: Constr ---
    {"url":"https://www.archdaily.com/rss","cat":"construction","type":"web","source_name":"ArchDaily","lang":"en"},
    {"url":"https://www.constructiondive.com/feeds/news/","cat":"construction","type":"web","source_name":"Construction Dive","lang":"en"},
    {"url":"https://www.constructionenquirer.com/feed/","cat":"construction","type":"web","source_name":"Construction Enquirer","lang":"en"},
    {"url":"https://www.byggvarlden.se/feed/","cat":"construction","type":"web","source_name":"Byggvärlden","lang":"sv"},
    {"url":"https://www.byggindustrin.se/rss/nyheter","cat":"construction","type":"web","source_name":"Byggindustrin","lang":"sv"},
    {"url":"https://www.youtube.com/@TheB1M/videos","cat":"construction","type":"video","source_name":"The B1M","lang":"en"},
    {"url":"https://www.youtube.com/@TomorrowsBuild/videos","cat":"construction","type":"video","source_name":"Tomorrow's Build","lang":"en"},
    {"url":"https://www.youtube.com/@FD_Engineering/videos","cat":"construction","type":"video","source_name":"Free Documentary Engineering","lang":"en"},
    # --- ECONOMY ---
    {"url":"https://efn.se/feeds/feed.xml","cat":"economy","type":"web","source_name":"EFN.se","lang":"sv"},
    {"url":"https://www.borskollen.se/rss/nyheter","cat":"economy","type":"web","source_name":"Börskollen","lang":"sv"},
    {"url":"https://www.youtube.com/@qatareconomicforum430/videos","cat":"economy","type":"video","source_name":"Qatar Economic Forum","lang":"en"},
    {"url":"https://www.youtube.com/@FII_INSTITUTE/videos","cat":"economy","type":"video","source_name":"FII Institute","lang":"en"},
    {"url":"https://www.youtube.com/@wef/videos","cat":"economy","type":"video","source_name":"World Economic Forum","lang":"en"},
    {"url":"https://www.youtube.com/@TheDiaryOfACEO/videos","cat":"economy","type":"video","source_name":"Diary of a CEO","lang":"en"},
    # --- GEO: Sweden ---
    {"url":"https://rss.aftonbladet.se/rss2/small/pages/sections/nyheter/","cat":"geopolitics","type":"web","source_name":"Aftonbladet","lang":"sv","filter_tag":"sweden"},
    {"url":"https://www.dagensps.se/feed/","cat":"geopolitics","type":"web","source_name":"Dagens PS","lang":"sv","filter_tag":"sweden"},
    # --- GEO: EU ---
    {"url":"https://www.youtube.com/@EUdebatesLIVE/videos","cat":"geopolitics","type":"video","source_name":"EU Debates","lang":"en","filter_tag":"eu"},
]

URLS_GLOBAL = [
]

URLS_TECH = [
]

URLS_ENERGY = [
]

URLS_EV = [
]

URLS_SCIENCE = [
]

URLS_CONSTRUCTION = [
]

URLS_VIDEO_GLOBAL = [
]

URLS_VIDEO_CHINA = [
]

URLS_VIDEO_USA = [
]

URLS_VIDEO_INDIA = [
]

URLS_YOUTUBE_GEO = [
]

URLS_YOUTUBE_TECH = [
]

URLS_YOUTUBE_ENERGY = [
]

URLS_YOUTUBE_EV = [
]

URLS_YOUTUBE_GAMING = [
]

URLS_GAMING = [
]

URLS_GAMING_ACTION = [
]

URLS_GAMING_SHOOTER = [
]

URLS_GAMING_RPG = [
]

URLS_GAMING_MMORPG = [
]

URLS_GAMING_STRATEGY = [
]

URLS_GAMING_SPORTS = [
]

URLS_GAMING_UPCOMING = [
]

URLS_GEO_GLOBAL = [
]

URLS_GEO_USA = [
]

URLS_GEO_CHINA = [
]

URLS_GEO_EU = [
]

URLS_GEO_INDIA = [
]

URLS_GEO_SWEDEN = [
]