def get_video_info(source):
    videos = []
    try:
        # STEP 1: Get video list (flat mode - stable)
        list_opts = {
            'quiet': True,
            'ignoreerrors': True,
            'extract_flat': True,
            'playlistend': 10,
            'http_headers': HEADERS
        }

        with yt_dlp.YoutubeDL(list_opts) as ydl:
            info = ydl.extract_info(source["url"], download=False)

        if not info:
            return videos

        entries = info.get("entries", [])
        if not entries:
            return videos

        # STEP 2: Fetch full metadata for each video
        detail_opts = {
            'quiet': True,
            'ignoreerrors': True,
            'extract_flat': False,
            'http_headers': HEADERS
        }

        for e in entries:
            if not e or not e.get("url"):
                continue

            video_url = e["url"]

            # fetch full data
            with yt_dlp.YoutubeDL(detail_opts) as ydl:
                full = ydl.extract_info(video_url, download=False)

            if not full:
                continue

            # thumbnail
            thumb = DEFAULT_IMAGE
            if full.get("thumbnails"):
                thumb = full["thumbnails"][-1]["url"]
            elif full.get("id"):
                thumb = f"https://img.youtube.com/vi/{full['id']}/hqdefault.jpg"

            # timestamp
            ts = 0
            if full.get("release_timestamp"):
                ts = full["release_timestamp"]
            elif full.get("timestamp"):
                ts = full["timestamp"]
            elif full.get("upload_date"):
                ts = datetime.strptime(full["upload_date"], "%Y%m%d").timestamp()
            else:
                ts = time.time()

            if is_too_old(ts):
                continue

            title = full.get("title", "Video")
            desc = clean_text(full.get("description", ""))

            if source.get("lang") == "sv":
                title = translate_text(title, "sv")
                desc = translate_text(desc, "sv")

            # THE CRITICAL PART (required by your frontend):
            videos.append({
                "is_video": True,                          # REQUIRED
                "category": source["cat"],                 # REQUIRED
                "filter_tag": source.get("filter_tag", ""),# REQUIRED
                "source": source["source_name"],
                "title": title,
                "summary": desc,
                "link": full.get("webpage_url", video_url),
                "images": [thumb],
                "timestamp": ts,
                "is_article": False,
                "time_str": "",
            })

    except Exception as e:
        print("VIDEO ERROR:", e)

    return videos
