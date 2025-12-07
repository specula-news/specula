# Sources for aggregation site - VERIFIERAD & FUNGERANDE VERSION

SOURCES = [
    # ==========================================
    #               GAMING
    # ==========================================
    {"url": "https://www.eurogamer.net/feed", "cat": "gaming", "type": "web", "source_name": "Eurogamer"},
    {"url": "https://www.nintendolife.com/feeds/latest", "cat": "gaming", "type": "web", "source_name": "Nintendo Life"},
    {"url": "https://www.pushsquare.com/feeds/latest", "cat": "gaming", "type": "web", "source_name": "Push Square"},
    {"url": "https://www.purexbox.com/feeds/latest", "cat": "gaming", "type": "web", "source_name": "Pure Xbox"},
    {"url": "https://kotaku.com/rss", "cat": "gaming", "type": "web", "source_name": "Kotaku"},
    {"url": "https://www.gamespot.com/feeds/news/", "cat": "gaming", "type": "web", "source_name": "GameSpot"},
    {"url": "https://www.pcgamer.com/rss", "cat": "gaming", "type": "web", "source_name": "PC Gamer"},
    {"url": "https://www.videogameschronicle.com/feed/", "cat": "gaming", "type": "web", "source_name": "VGC"},
    {"url": "https://www.gematsu.com/feed", "cat": "gaming", "type": "web", "source_name": "Gematsu"},
    {"url": "https://gamingbolt.com/feed", "cat": "gaming", "type": "web", "source_name": "GamingBolt"},
    {"url": "https://www.vg247.com/feed", "cat": "gaming", "type": "web", "source_name": "VG247"},
    {"url": "https://www.fz.se/feeds/nyheter", "cat": "gaming", "type": "web", "source_name": "FZ.se"},
    {"url": "https://www.ign.com/feeds/all", "cat": "gaming", "type": "web", "source_name": "IGN"},
    {"url": "https://www.youtube.com/@IGN/videos", "cat": "gaming", "type": "video", "source_name": "IGN YouTube"},
    {"url": "https://www.youtube.com/@gamespot/videos", "cat": "gaming", "type": "video", "source_name": "GameSpot YouTube"},

    # ==========================================
    #                TECH
    # ==========================================
    {"url": "https://www.theverge.com/rss/index.xml", "cat": "tech", "type": "web", "source_name": "The Verge"},
    {"url": "https://techcrunch.com/feed/", "cat": "tech", "type": "web", "source_name": "TechCrunch"},
    {"url": "https://feeds.arstechnica.com/arstechnica/index", "cat": "tech", "type": "web", "source_name": "Ars Technica"},
    {"url": "https://anastasiintech.substack.com/feed", "cat": "tech", "type": "web", "source_name": "Anastasi In Tech"},
    {"url": "https://feber.se/rss/", "cat": "tech", "type": "web", "source_name": "Feber"},
    {"url": "https://www.nyteknik.se/rss", "cat": "tech", "type": "web", "source_name": "NyTeknik"},
    {"url": "https://tjock.se/feed/", "cat": "tech", "type": "web", "source_name": "Tjock.se"},
    {"url": "https://www.youtube.com/@LinusTechTips/videos", "cat": "tech", "type": "video", "source_name": "Linus Tech Tips"},
    {"url": "https://www.youtube.com/@Jayztwocents/videos", "cat": "tech", "type": "video", "source_name": "JayzTwoCents"},
    {"url": "https://www.youtube.com/@Hardwareunboxed/videos", "cat": "tech", "type": "video", "source_name": "Hardware Unboxed"},
    {"url": "https://www.youtube.com/@der8auer-en/videos", "cat": "tech", "type": "video", "source_name": "der8auer"},
    {"url": "https://www.youtube.com/@elithecomputerguy/videos", "cat": "tech", "type": "video", "source_name": "Eli the Computer Guy"},

    # ==========================================
    #               EV (ELBILAR / ENERGI)
    # ==========================================
    {"url": "https://insideevs.com/rss/articles/all/", "cat": "ev", "type": "web", "source_name": "InsideEVs"},
    {"url": "https://electrek.co/feed/", "cat": "ev", "type": "web", "source_name": "Electrek"},
    {"url": "https://cleantechnica.com/feed/", "cat": "ev", "type": "web", "source_name": "CleanTechnica"},
    {"url": "https://oilprice.com/rss/main", "cat": "ev", "type": "web", "source_name": "OilPrice"},
    {"url": "https://www.renewableenergyworld.com/feed/", "cat": "ev", "type": "web", "source_name": "Renewable Energy World"},
    {"url": "https://teslaclubsweden.se/feed/", "cat": "ev", "type": "web", "source_name": "Tesla Club"},
    {"url": "https://www.youtube.com/@ELEKTROmanija/videos", "cat": "ev", "type": "video", "source_name": "ELEKTROmanija"},
    {"url": "https://www.youtube.com/@UndecidedMF/videos", "cat": "ev", "type": "video", "source_name": "Undecided"},
    {"url": "https://www.youtube.com/@electricviking/videos", "cat": "ev", "type": "video", "source_name": "Electric Viking"},
    {"url": "https://www.youtube.com/@Tesla/videos", "cat": "ev", "type": "video", "source_name": "Tesla"},

    # ==========================================
    #               GEOPOLITICS
    # ==========================================
    {"url": "https://www.scmp.com/rss/91/feed", "cat": "geopolitics", "type": "web", "source_name": "SCMP"},
    {"url": "https://www.aljazeera.com/xml/rss/all.xml", "cat": "geopolitics", "type": "web", "source_name": "Al Jazeera"},
    {"url": "https://www.dagensps.se/feed/", "cat": "geopolitics", "type": "web", "source_name": "Dagens PS"},
    {"url": "https://www.cnbc.com/id/100727362/device/rss/rss.html", "cat": "geopolitics", "type": "web", "source_name": "CNBC World"},
    {"url": "https://rss.aftonbladet.se/rss2/small/pages/sections/nyheter/", "cat": "geopolitics", "type": "web", "source_name": "Aftonbladet"},
    {"url": "https://www.youtube.com/@wocomoDOCS/videos", "cat": "geopolitics", "type": "video", "source_name": "wocomoDOCS"},
    {"url": "https://www.youtube.com/@channelnewsasia/videos", "cat": "geopolitics", "type": "video", "source_name": "Channel NewsAsia"},
    {"url": "https://www.youtube.com/@cgtn/videos", "cat": "geopolitics", "type": "video", "source_name": "CGTN"},
    {"url": "https://www.youtube.com/@CGTNEurope/videos", "cat": "geopolitics", "type": "video", "source_name": "CGTN Europe"},
    {"url": "https://www.youtube.com/@CCTVVideoNewsAgency/videos", "cat": "geopolitics", "type": "video", "source_name": "CCTV News"},
    {"url": "https://www.youtube.com/@cgtnamerica/videos", "cat": "geopolitics", "type": "video", "source_name": "CGTN America"},
    {"url": "https://www.youtube.com/@TheDiaryOfACEO/videos", "cat": "geopolitics", "type": "video", "source_name": "Diary of a CEO"},
    {"url": "https://www.youtube.com/@johnnyharris/videos", "cat": "geopolitics", "type": "video", "source_name": "Johnny Harris"},
    {"url": "https://www.youtube.com/@DWDocumentary/videos", "cat": "geopolitics", "type": "video", "source_name": "DW Documentary"},
    {"url": "https://www.youtube.com/@Asianometry/videos", "cat": "geopolitics", "type": "video", "source_name": "Asianometry"},
    {"url": "https://www.youtube.com/@BBCNews/videos", "cat": "geopolitics", "type": "video", "source_name": "BBC News"},

    # ==========================================
    #               SCIENCE
    # ==========================================
    {"url": "https://www.space.com/feeds/all", "cat": "science", "type": "web", "source_name": "Space.com"},
    {"url": "https://www.scientificamerican.com/feed/home/", "cat": "science", "type": "web", "source_name": "Scientific American"},
    {"url": "https://www.newscientist.com/feed/home/", "cat": "science", "type": "web", "source_name": "New Scientist"},
    {"url": "https://www.nasa.gov/rss/dyn/breaking_news.rss", "cat": "science", "type": "web", "source_name": "NASA"},
    {"url": "https://www.youtube.com/@pbsspacetime/videos", "cat": "science", "type": "video", "source_name": "PBS Space Time"},
    {"url": "https://www.youtube.com/@SpaceEyeTech/videos", "cat": "science", "type": "video", "source_name": "Space Eye Tech"},
    {"url": "https://www.youtube.com/@PracticalEngineeringChannel/videos", "cat": "science", "type": "video", "source_name": "Practical Engineering"},
    {"url": "https://www.youtube.com/@smartereveryday/videos", "cat": "science", "type": "video", "source_name": "SmarterEveryDay"},
    {"url": "https://www.youtube.com/@veritasium/videos", "cat": "science", "type": "video", "source_name": "Veritasium"},
    {"url": "https://www.youtube.com/@ScienceChannel/videos", "cat": "science", "type": "video", "source_name": "Science Channel"},

    # ==========================================
    #             CONSTRUCTION
    # ==========================================
    {"url": "https://www.archdaily.com/feed/", "cat": "construction", "type": "web", "source_name": "ArchDaily"},
    {"url": "https://www.constructiondive.com/feeds/news/", "cat": "construction", "type": "web", "source_name": "Construction Dive"},
    {"url": "https://www.constructionenquirer.com/feed/", "cat": "construction", "type": "web", "source_name": "Construction Enquirer"},
    {"url": "https://www.youtube.com/@TomorrowsBuild/videos", "cat": "construction", "type": "video", "source_name": "Tomorrow's Build"},
    {"url": "https://www.youtube.com/@TheB1M/videos", "cat": "construction", "type": "video", "source_name": "The B1M"},
]