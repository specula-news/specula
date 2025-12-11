# SPECULA // AI-Powered Global News Aggregator

![Project Status](https://img.shields.io/badge/status-active-00f0ff)
![Python](https://img.shields.io/badge/backend-python-blue)
![Frontend](https://img.shields.io/badge/frontend-HTML%2FJS-orange)
![License](https://img.shields.io/badge/license-MIT-green)

**SPECULA** is a fully automated, self-hosted news aggregation engine. It fetches, filters, and categorizes news from RSS feeds and YouTube channels in real-time. Designed with a futuristic "Matrix/Cyberpunk" aesthetic, it provides a distraction-free environment to stay updated on Geopolitics, Technology, Gaming, Energy, and Science.

## 🚀 Features

### 🧠 Backend (Python)
*   **Multi-Source Aggregation:** Scrapes RSS feeds and YouTube channels simultaneously.
*   **Smart Media Handling:** Uses `yt-dlp` for video metadata and custom scraping strategies (BeautifulSoup) to fetch high-res images from complex sites like Sweclockers or Aftonbladet.
*   **Content Filtering:** Automatically categories articles based on tags and sources.
*   **"Anti-Clumping" Algorithm:** Custom sorting logic ensures a diverse feed by preventing multiple articles from the same source appearing consecutively.
*   **Auto-Translation:** optional Google Translate integration to standardize headlines to English.

### 💻 Frontend (The News Feed)
*   **Responsive Design:** Fully optimized for Desktop and Mobile (5-column grid on mobile).
*   **PWA Support:** Can be installed as a native app on iOS and Android.
*   **Theme System:** Toggle between Dark Mode (Cyberpunk/Matrix) and Light Mode.
*   **Read Later:** LocalStorage-based bookmarking system.
*   **Embedded Video:** Detects video content and adds play overlays.

### 🎛️ Admin Dashboard (The Control Center)
*   **Visual Source Management:** No coding required to add sources.
*   **Drag & Drop:** Move sources between categories easily.
*   **Smart URL Fixer:** Paste a generic URL (e.g., `www.sweclockers.com`), and the admin panel automatically finds the correct RSS feed.
*   **Live Testing:** Test URLs directly from the dashboard.
*   **GitHub Sync:** Saves changes directly to `sources.py` in the repository via the GitHub API.

---

## 🛠️ Installation & Setup

### Prerequisites
*   Python 3.8+
*   A GitHub Account (for hosting and actions)

### 1. Local Setup
Clone the repository and install dependencies:

```bash
git clone https://github.com/specula-news/specula.git
cd specula
pip install -r requirements.txt
