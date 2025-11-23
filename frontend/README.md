# frontend

An Electron application with React and TypeScript

## Recommended IDE Setup


## Project Setup

### Install

```bash
$ npm install
```

### Development

```bash
$ npm run dev
```

### Build

```bash
# For windows
$ npm run build:win

# For macOS
$ npm run build:mac

# For Linux
$ npm run build:linux
```

## Content Security Policy and map tiles

This app uses Leaflet with OpenStreetMap tiles. By default, a strict CSP blocks external images. To allow map tiles to load while keeping other resources restricted, the renderer's `index.html` includes:

```
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://*.tile.openstreetmap.org" />
```

If you switch providers or need additional hosts, add them to the `img-src` list only (avoid broadening other directives). For example, to allow Mapbox tiles you would add `https://*.tiles.mapbox.com`.
