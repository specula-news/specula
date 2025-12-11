
def get_video_info(source):
    videos = []
    try:
        # Steg 1: Hämta video-listan (ALLTID EXTRACT_FLAT)
        list_opts = {
            'quiet': True,
            'ignoreerrors': True,
            'extract_flat': True,
            'playlistend': 10,
            'http_headers': HEADERS
        }

        with yt_dlp.YoutubeDL(list_opts) as ydl:
            info = ydl.extract_info(source['url'], download=False)
            if not info:
                return videos

        entries = info.get("entries", [])
        if not entries:
            return videos

        # Steg 2: För varje video – hämta detaljer separat
        detail_opts = {
            'quiet': True,
            'ignoreerrors': True,
            'extract_flat': False,
            'http_headers': HEADERS
        }

        for e in entries:
            if not e or not e.get("url"):
                continue

            video_url = e.get("url")

            # Hämta riktig metadata
            with yt_dlp.YoutubeDL(detail_opts) as ydl:
                full = ydl.extract_info(video_url, download=False)

            if not full:
                continue

            # Hämta thumbnail
            thumb = DEFAULT_IMAGE
            if full.get("thumbnails"):
                thumb = full["thumbnails"][-1]["url"]
            elif full.get("id"):
                thumb = f"https://img.youtube.com/vi/{full['id']}/hqdefault.jpg"

            # Timestamp fixat
            ts = 0
            if full.get("release_timestamp"):
                ts = full["release_timestamp"]
            elif full.get("timestamp"):
                ts = full["timestamp"]
            elif full.get("_timestamp"):
                ts = full["_timestamp"]
            elif full.get("upload_date"):
                ts = datetime.strptime(full["upload_date"], "%Y%m%d").timestamp()
            else:
                ts = time.time()

            if is_too_old(ts):
                continue

            title = full.get("title", "Video")
            desc = clean_text(full.get("description", ""))

            lang_note = ""
            if source.get("lang") == "sv":
                title = translate_text(title, "sv")
                desc = translate_text(desc, "sv")
                lang_note = " (Translated from Swedish)"

            videos.append({
                "title": title,
                "link": full.get("webpage_url", video_url),
                "images": [thumb],
                "summary": desc,
                "category": source.get("cat", "video"),
                "filter_tag": source.get("filter_tag", ""),
                "source": source.get("source_name", "YouTube"),
                "lang_note": lang_note,
                "timestamp": ts,
                "time_str": "",
                "is_video": True
            })

    except Exception as e:
        print(f"FEL VID VIDEOHÄMTNING: {e}")

    return videos
