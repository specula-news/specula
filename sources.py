# Sources for aggregation site

SOURCES = [
    # --- NEWS: GLOBAL ---
    {"url":"https://www.reuters.com/rss/news/world","cat":"geopolitics","type":"web","source_name":"Reuters","lang":"en","filter_tag":"global"},
    {"url":"https://www.theguardian.com/europe/rss","cat":"geopolitics","type":"web","source_name":"The Guardian","lang":"en","filter_tag":"global","custom_image":"data:image/png;base64,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","image_strategy":null},
    {"url":"https://www.aljazeera.com/xml/rss/all.xml","cat":"geopolitics","type":"web","source_name":"Al Jazeera","lang":"en","filter_tag":"global"},
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
    {"url":"https://www.youtube.com/@lenapetrova/videos","cat":"youtubers","type":"video","source_name":"Lena Petrova","lang":"en","filter_tag":"geo"},
    # --- YT: Tech ---
    {"url":"https://www.youtube.com/@AnastasiInTech/videos","cat":"youtubers","type":"video","source_name":"Anastasi In Tech","lang":"en","filter_tag":"tech"},
    {"url":"https://www.youtube.com/@veritasium/videos","cat":"youtubers","type":"video","source_name":"Veritasium","lang":"en","filter_tag":"tech"},
    {"url":"https://www.youtube.com/@smartereveryday/videos","cat":"youtubers","type":"video","source_name":"Smartereveryday","lang":"en","filter_tag":"tech"},
    {"url":"https://www.youtube.com/@Jayztwocents/videos","cat":"youtubers","type":"video","source_name":"Jayztwocents","lang":"en","filter_tag":"tech"},
    {"url":"https://www.youtube.com/@LinusTechTips/videos","cat":"youtubers","type":"video","source_name":"Linus Tech Tips","lang":"en","filter_tag":"tech"},
    {"url":"https://www.youtube.com/@MKBHD/videos","cat":"youtubers","type":"video","source_name":"MKBHD","lang":"en","filter_tag":"tech"},
    {"url":"https://www.youtube.com/@Hardwareunboxed/videos","cat":"youtubers","type":"video","source_name":"Hardware Unboxed","lang":"en","filter_tag":"tech"},
    {"url":"https://www.youtube.com/@der8auer-en/videos","cat":"youtubers","type":"video","source_name":"der8auer","lang":"en","filter_tag":"tech"},
    # --- YT: Energy ---
    {"url":"https://www.youtube.com/@UndecidedMF/videos","cat":"youtubers","type":"video","source_name":"UndecidedMF","lang":"en","filter_tag":"energy"},
    # --- YT: EV ---
    {"url":"https://www.youtube.com/@FullyChargedShow/videos","cat":"youtubers","type":"video","source_name":"Fully Charged","lang":"en","filter_tag":"ev"},
    {"url":"https://www.youtube.com/@electricviking/videos","cat":"youtubers","type":"video","source_name":"Electric Viking","lang":"en","filter_tag":"ev"},
    # --- YT: Gaming ---
    {"url":"https://www.youtube.com/@Raxxanterax/videos","cat":"youtubers","type":"video","source_name":"Raxxanterax","lang":"en","filter_tag":"gaming"},
    {"url":"https://www.youtube.com/@jackfrags/videos","cat":"youtubers","type":"video","source_name":"Jackfrags","lang":"en","filter_tag":"gaming"},
    {"url":"https://www.youtube.com/@ZiggyDGaming/videos","cat":"youtubers","type":"video","source_name":"ZiggyD","lang":"en","filter_tag":"gaming"},
    {"url":"https://www.youtube.com/@AsmonTV/videos","cat":"youtubers","type":"video","source_name":"AsmonTV","lang":"en","filter_tag":"gaming"},
    {"url":"https://www.youtube.com/@gameranxTV/videos","cat":"youtubers","type":"video","source_name":"Gameranx","lang":"en","filter_tag":"gaming"},
    # --- GAME: News ---
    {"url":"https://www.eurogamer.net/feed","cat":"gaming","type":"web","source_name":"Eurogamer","lang":"en"},
    {"url":"https://www.pcgamer.com/rss","cat":"gaming","type":"web","source_name":"PC Gamer","lang":"en"},
    # --- GAME: Video ---
    {"url":"https://www.youtube.com/@gamespot/videos","cat":"gaming","type":"video","source_name":"GameSpot","lang":"en","filter_tag":"gaming"},
    {"url":"https://www.youtube.com/@IGN/videos","cat":"gaming","type":"video","source_name":"IGN","lang":"en","filter_tag":"gaming"},
    {"url":"https://www.youtube.com/@ewc/videos","cat":"gaming","type":"video","source_name":"Esports World Cup","lang":"en"},
    {"url":"https://www.youtube.com/@esl/videos","cat":"gaming","type":"video","source_name":"ESL","lang":"en"},
    # --- TOPIC: Tech ---
    {"url":"https://www.nyteknik.se/nyheter/ny-teknik-i-rrs-format/972205","cat":"tech","type":"web","source_name":"Nyteknik","lang":"sv"},
    {"url":"https://www.theverge.com/rss/index.xml","cat":"tech","type":"web","source_name":"The Verge","lang":"en"},
    {"url":"https://techcrunch.com/feed/","cat":"tech","type":"web","source_name":"TechCrunch","lang":"en"},
    {"url":"https://feeds.arstechnica.com/arstechnica/index","cat":"tech","type":"web","source_name":"Ars Technica","lang":"en"},
    {"url":"https://anastasiintech.substack.com/feed","cat":"tech","type":"web","source_name":"Anastasi In Tech","lang":"en"},
    {"url":"https://feber.se/rss/","cat":"tech","type":"web","source_name":"Feber","lang":"sv"},
    {"url":"https://www.wired.com/feed/rss","cat":"tech","type":"web","source_name":"WIRED","lang":"en"},
    {"url":"https://www.engadget.com/rss.xml","cat":"tech","type":"web","source_name":"Engadget","lang":"en"},
    {"url":"https://mashable.com/feeds/rss/tech","cat":"tech","type":"web","source_name":"Mashable","lang":"en"},
    # --- TOPIC: Energy ---
    {"url":"https://energy.economictimes.indiatimes.com/rss/recentstories","cat":"energy","type":"web","source_name":"ET EnergyWorld","lang":"en","image_strategy":"lazy"},
    {"url":"https://energydigital.com/feed","cat":"energy","type":"web","source_name":"Energy Digital","lang":"en"},
    {"url":"https://www.breakthroughenergy.org/news","cat":"energy","type":"web","source_name":"Breakthrough Energy","lang":"en"},
    {"url":"https://oilprice.com/rss/main","cat":"energy","type":"web","source_name":"OilPrice","lang":"en"},
    {"url":"https://www.renewableenergyworld.com/feed/","cat":"energy","type":"web","source_name":"Renewable Energy World","lang":"en"},
    # --- TOPIC: EV ---
    {"url":"https://insideevs.com/rss/articles/all/","cat":"ev","type":"web","source_name":"InsideEVs","lang":"en"},
    {"url":"https://electrek.co/feed/","cat":"ev","type":"web","source_name":"Electrek","lang":"en"},
    {"url":"https://cleantechnica.com/feed/","cat":"ev","type":"web","source_name":"CleanTechnica","lang":"en"},
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
    {"url":"https://rss.aftonbladet.se/rss2/small/pages/sections/senastenytt/","cat":"geopolitics","type":"web","source_name":"Aftonbladet","lang":"sv","filter_tag":"sweden"},
    {"url":"https://www.dagensps.se/feed/","cat":"geopolitics","type":"web","source_name":"Dagens PS","lang":"sv","filter_tag":"sweden"},
    # --- GEO: EU ---
    {"url":"https://www.youtube.com/@EUdebatesLIVE/videos","cat":"geopolitics","type":"video","source_name":"EU Debates","lang":"en","filter_tag":"eu"},
]

URLS_GLOBAL = []