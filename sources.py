# Sources for aggregation site - FINAL COMPLETE LIST

SOURCES = [
    # ==========================================
    #           1. GLOBAL NEWS (MEDIA)
    # ==========================================
    # Web
    {"url": "https://www.aljazeera.com/xml/rss/all.xml", "cat": "geopolitics", "type": "web", "source_name": "Al Jazeera", "lang": "en", "filter_tag": "global"},
    {"url": "http://feeds.bbci.co.uk/news/world/rss.xml", "cat": "geopolitics", "type": "web", "source_name": "BBC World", "lang": "en", "filter_tag": "global"},
    {"url": "https://www.cnbc.com/id/100727362/device/rss/rss.html", "cat": "geopolitics", "type": "web", "source_name": "CNBC", "lang": "en", "filter_tag": "usa"},
    {"url": "https://www.scmp.com/rss/91/feed", "cat": "geopolitics", "type": "web", "source_name": "SCMP", "lang": "en", "filter_tag": "china"},
    
    # Video (TV Channels)
    {"url": "https://www.youtube.com/@dwnews/videos", "cat": "geopolitics", "type": "video", "source_name": "DW News", "lang": "en", "filter_tag": "global"},
    {"url": "https://www.youtube.com/@aljazeeraenglish/videos", "cat": "geopolitics", "type": "video", "source_name": "Al Jazeera English", "lang": "en", "filter_tag": "global"},
    {"url": "https://www.youtube.com/@BBCNews/videos", "cat": "geopolitics", "type": "video", "source_name": "BBC News", "lang": "en", "filter_tag": "global"},
    {"url": "https://www.youtube.com/@France24_en/videos", "cat": "geopolitics", "type": "video", "source_name": "France 24", "lang": "en", "filter_tag": "global"},
    {"url": "https://www.youtube.com/@channelnewsasia/videos", "cat": "geopolitics", "type": "video", "source_name": "CNA", "lang": "en", "filter_tag": "china"},
    {"url": "https://www.youtube.com/@cgtn/videos", "cat": "geopolitics", "type": "video", "source_name": "CGTN", "lang": "en", "filter_tag": "china"},
    {"url": "https://www.youtube.com/@Firstpost/videos", "cat": "geopolitics", "type": "video", "source_name": "Firstpost", "lang": "en", "filter_tag": "india"},

    # ==========================================
    #        2. YOUTUBERS (INDEPENDENT)
    # ==========================================
    # Geopolitics / Analysis
    {"url": "https://www.youtube.com/@brdecode123/videos", "cat": "youtubers", "type": "video", "source_name": "BR Decode", "lang": "en", "filter_tag": "geo"},
    {"url": "https://www.youtube.com/@johnnyharris/videos", "cat": "youtubers", "type": "video", "source_name": "Johnny Harris", "lang": "en", "filter_tag": "geo"},
    {"url": "https://www.youtube.com/@VisualPolitikEN/videos", "cat": "youtubers", "type": "video", "source_name": "VisualPolitik", "lang": "en", "filter_tag": "geo"},
    {"url": "https://www.youtube.com/@TheMilitaryShow/videos", "cat": "youtubers", "type": "video", "source_name": "The Military Show", "lang": "en", "filter_tag": "geo"},
    {"url": "https://www.youtube.com/@Asianometry/videos", "cat": "youtubers", "type": "video", "source_name": "Asianometry", "lang": "en", "filter_tag": "geo"},
    {"url": "https://www.youtube.com/@GeopoliticalEconomyReport/videos", "cat": "youtubers", "type": "video", "source_name": "Geopolitical Economy", "lang": "en", "filter_tag": "geo"},
    {"url": "https://www.youtube.com/@lenapetrova/videos", "cat": "youtubers", "type": "video", "source_name": "Lena Petrova", "lang": "en", "filter_tag": "geo"},
    {"url": "https://www.youtube.com/@EUdebatesLIVE/videos", "cat": "youtubers", "type": "video", "source_name": "EU Debates", "lang": "en", "filter_tag": "geo"},

    # Tech YouTubers
    {"url": "https://www.youtube.com/@LinusTechTips/videos", "cat": "youtubers", "type": "video", "source_name": "Linus Tech Tips", "lang": "en", "filter_tag": "tech"},
    {"url": "https://www.youtube.com/@MKBHD/videos", "cat": "youtubers", "type": "video", "source_name": "MKBHD", "lang": "en", "filter_tag": "tech"},
    {"url": "https://www.youtube.com/@Hardwareunboxed/videos", "cat": "youtubers", "type": "video", "source_name": "Hardware Unboxed", "lang": "en", "filter_tag": "tech"},
    {"url": "https://www.youtube.com/@der8auer-en/videos", "cat": "youtubers", "type": "video", "source_name": "der8auer", "lang": "en", "filter_tag": "tech"},
    
    # EV YouTubers
    {"url": "https://www.youtube.com/@FullyChargedShow/videos", "cat": "youtubers", "type": "video", "source_name": "Fully Charged", "lang": "en", "filter_tag": "ev"},
    {"url": "https://www.youtube.com/@electricviking/videos", "cat": "youtubers", "type": "video", "source_name": "Electric Viking", "lang": "en", "filter_tag": "ev"},
    
    # Gaming YouTubers
    {"url": "https://www.youtube.com/@gameranxTV/videos", "cat": "youtubers", "type": "video", "source_name": "Gameranx", "lang": "en", "filter_tag": "gaming"},
    {"url": "https://www.youtube.com/@IGN/videos", "cat": "youtubers", "type": "video", "source_name": "IGN", "lang": "en", "filter_tag": "gaming"},
    {"url": "https://www.youtube.com/@gamespot/videos", "cat": "youtubers", "type": "video", "source_name": "GameSpot", "lang": "en", "filter_tag": "gaming"},

    # ==========================================
    #           ECONOMY & BUSINESS
    # ==========================================
    # Web
    {"url": "https://efn.se/feeds/feed.xml", "cat": "economy", "type": "web", "source_name": "EFN.se", "lang": "sv"},
    {"url": "https://www.borskollen.se/rss/nyheter", "cat": "economy", "type": "web", "source_name": "Börskollen", "lang": "sv"},
    {"url": "https://www.theverge.com/rss/index.xml", "cat": "tech", "type": "web", "source_name": "The Verge", "lang": "en"},
    
    # Video (Forums/Institutes)
    {"url": "https://www.youtube.com/@qatareconomicforum430/videos", "cat": "economy", "type": "video", "source_name": "Qatar Economic Forum", "lang": "en"},
    {"url": "https://www.youtube.com/@FII_INSTITUTE/videos", "cat": "economy", "type": "video", "source_name": "FII Institute", "lang": "en"},
    {"url": "https://www.youtube.com/@wef/videos", "cat": "economy", "type": "video", "source_name": "World Economic Forum", "lang": "en"},
    {"url": "https://www.youtube.com/@TheDiaryOfACEO/videos", "cat": "economy", "type": "video", "source_name": "Diary of a CEO", "lang": "en"},

    # ==========================================
    #               GAMING (ESPORTS)
    # ==========================================
    # Web
    {"url": "https://www.eurogamer.net/feed", "cat": "gaming", "type": "web", "source_name": "Eurogamer", "lang": "en"},
    {"url": "https://www.pcgamer.com/rss", "cat": "gaming", "type": "web", "source_name": "PC Gamer", "lang": "en"},
    {"url": "https://www.fz.se/feeds/nyheter", "cat": "gaming", "type": "web", "source_name": "FZ.se", "lang": "sv"},
    
    # Video (Tournaments)
    {"url": "https://www.youtube.com/@ewc/videos", "cat": "gaming", "type": "video", "source_name": "Esports World Cup", "lang": "en"},
    {"url": "https://www.youtube.com/@esl/videos", "cat": "gaming", "type": "video", "source_name": "ESL", "lang": "en"},

    # ==========================================
    #             EV / ENERGY (WEB)
    # ==========================================
    {"url": "https://insideevs.com/rss/articles/all/", "cat": "ev", "type": "web", "source_name": "InsideEVs", "lang": "en"},
    {"url": "https://electrek.co/feed/", "cat": "ev", "type": "web", "source_name": "Electrek", "lang": "en"},
    {"url": "https://cleantechnica.com/feed/", "cat": "ev", "type": "web", "source_name": "CleanTechnica", "lang": "en"},
    {"url": "https://oilprice.com/rss/main", "cat": "ev", "type": "web", "source_name": "OilPrice", "lang": "en"},
    {"url": "https://teslaclubsweden.se/feed/", "cat": "ev", "type": "web", "source_name": "Tesla Club Sweden", "lang": "sv"},
    # SVENSKA
    {"url": "https://alltomelbil.se/feed/", "cat": "ev", "type": "web", "source_name": "Allt om Elbil", "lang": "sv"},
    {"url": "https://elbilen.se/feed/", "cat": "ev", "type": "web", "source_name": "Elbilen.se", "lang": "sv"},

    # ==========================================
    #               SCIENCE
    # ==========================================
    {"url": "https://www.space.com/feeds/all", "cat": "science", "type": "web", "source_name": "Space.com", "lang": "en"},
    {"url": "https://www.nasa.gov/rss/dyn/breaking_news.rss", "cat": "science", "type": "web", "source_name": "NASA", "lang": "en"},
    {"url": "https://www.youtube.com/@pbsspacetime/videos", "cat": "science", "type": "video", "source_name": "PBS Space Time", "lang": "en"},
    {"url": "https://www.youtube.com/@Kurzgesagt/videos", "cat": "science", "type": "video", "source_name": "Kurzgesagt", "lang": "en"},

    # ==========================================
    #             CONSTRUCTION
    # ==========================================
    {"url": "https://www.archdaily.com/rss", "cat": "construction", "type": "web", "source_name": "ArchDaily", "lang": "en"},
    {"url": "https://www.constructiondive.com/feeds/news/", "cat": "construction", "type": "web", "source_name": "Construction Dive", "lang": "en"},
    {"url": "https://www.constructionenquirer.com/feed/", "cat": "construction", "type": "web", "source_name": "Construction Enquirer", "lang": "en"},
    # SVENSKA
    {"url": "https://www.byggvarlden.se/feed/", "cat": "construction", "type": "web", "source_name": "Byggvärlden", "lang": "sv"},
    {"url": "https://www.byggindustrin.se/rss/nyheter", "cat": "construction", "type": "web", "source_name": "Byggindustrin", "lang": "sv"},
    
    # YouTube Construction
    {"url": "https://www.youtube.com/@TheB1M/videos", "cat": "construction", "type": "video", "source_name": "The B1M", "lang": "en"},
]