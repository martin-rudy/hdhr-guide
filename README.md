# HDHR Guide

A lightweight Docker container that queries a [HDHomeRun](https://www.silicondust.com/) tuner for its DeviceAuth, downloads the XMLTV guide from the [Silicondust API](https://github.com/Silicondust/documentation/wiki/XMLTV-Guide-Data), and serves it over HTTP for use with media servers like [Jellyfin](https://jellyfin.org/).

## Features

- **Zero config beyond the HDHomeRun URL** — just point it at your tuner
- **Auto-refreshes** the guide every 12 hours (configurable) with random jitter as required by the API
- **Always up-to-date DeviceAuth** — queries your HDHomeRun before each guide pull
- **2 days of guide data** for free, 14 days with an HDHomeRun DVR subscription
- **Tiny footprint** — ~50 MB Alpine-based image

## Quick Start

### 1. Create your `.env` file

```bash
cp .env.example .env
```

Edit `.env` and set your HDHomeRun URL:

```ini
HDHR_URL=http://192.168.4.34/discover.json
```

> **Find your HDHomeRun URL:** Open `http://hdhomerun.local/discover.json` in a browser, or use the IP directly. The response will contain your `DeviceID` and `DeviceAuth`.

### 2. Start the container

```bash
docker compose -f docker-compose-example.yml up -d
```

The guide will be available at `http://localhost:9000/xmlguide.xmltv`.

### 3. Configure Jellyfin

1. Go to **Dashboard → Live TV**
2. Under **Guide Data Providers**, add a new provider of type **XmlTV**
3. Set the **XMLTV URL** to:
   ```
   http://hdhr-guide:9000/xmlguide.xmltv
   ```
   (If running outside Docker Compose, use the host IP instead of `hdhr-guide`)

4. Click **Refresh Guide Data**

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `HDHR_URL` | **Yes** | — | Full URL to your HDHomeRun's `discover.json` (e.g., `http://192.168.4.34/discover.json`) |
| `HDHR_GUIDE_PORT` | No | `9000` | Internal HTTP port the guide is served on |
| `HDHR_GUIDE_REFRESH_HOURS` | No | `12` | How often to refresh the guide data (in hours). DeviceAuth is valid 16–24 hours, so values between 6–20 are recommended. |

## How It Works

```mermaid
sequenceDiagram
    participant J as Jellyfin
    participant G as hdhr-guide
    participant H as HDHomeRun
    participant S as Silicondust API

    G->>H: GET /discover.json
    H-->>G: DeviceAuth + DeviceID
    G->>S: GET /api/xmltv?DeviceAuth=xxx
    S-->>G: XMLTV guide (gzipped)
    J->>G: GET /xmlguide.xmltv
    G-->>J: XMLTV guide
```

## License

MIT
