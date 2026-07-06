# Naqsh Nasir — photography portfolio

A tiny, static two-page website (Portfolio + About/Contact) hosted free on
GitHub Pages. Photos are pulled automatically from a Google Drive folder by a
scheduled GitHub Action — **drop an image in Drive, and it shows up on the site.**

```
index.html          Portfolio (front page) — masonry grid + lightbox
about.html          About me & Contact
css/style.css        All styling
js/gallery.js        Gallery + lightbox (no libraries)
scripts/sync_drive.py  Downloads + optimizes Drive images, writes manifest
.github/workflows/sync-drive.yml  Runs the sync hourly
images/              Synced photos (full/ + thumb/) and manifest.json
```

Nothing here needs a build step or a server. It's plain HTML/CSS/JS.

---

## One-time setup

### 1. Put it on GitHub
Create a new **public** repository and push this folder to it:

```bash
cd naqsh-nasir
git init
git add .
git commit -m "Initial site"
git branch -M main
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

### 2. Turn on GitHub Pages
Repo → **Settings → Pages** → *Build and deployment* → Source: **Deploy from a
branch** → Branch: **main**, folder **/ (root)** → Save.
Your site will be at `https://<you>.github.io/<repo>/`.

### 3. Make a Google Drive folder for your photos
- Create a folder in Google Drive and add some images.
- Share it: **Anyone with the link → Viewer**.
- Copy the folder id from its URL:
  `https://drive.google.com/drive/folders/`**`THIS_LONG_ID`**

### 4. Get a Google Drive API key
- Go to <https://console.cloud.google.com/> → create a project (free).
- **APIs & Services → Library** → enable **Google Drive API**.
- **APIs & Services → Credentials → Create credentials → API key**.
- (Recommended) Click the key → **API restrictions → Restrict key → Google Drive API**.
- Copy the key.

> The key only reads files that are already shared publicly. It never touches
> anything private in your Drive.

### 5. Add the two secrets to GitHub
Repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Name | Value |
|------|-------|
| `DRIVE_FOLDER_ID` | the folder id from step 3 |
| `DRIVE_API_KEY`   | the API key from step 4 |

### 6. Run the sync
Repo → **Actions → “Sync photos from Google Drive” → Run workflow**.
After it finishes it commits the optimized images and `manifest.json`, and the
Pages site updates. From then on it runs **every hour** automatically (and you
can always click *Run workflow* to sync immediately).

---

## Everyday use
- **Add photos:** drop them in the Drive folder. They appear after the next
  hourly sync (or trigger it manually from the Actions tab).
- **Remove photos:** delete them from the Drive folder; the next sync removes
  them from the site too.
- **Order:** newest photos (by Drive upload date) appear first.
- **Captions:** the file name (minus extension, dashes/underscores → spaces) is
  shown in the lightbox. Name your files nicely in Drive if you want captions.

## Editing content
- **Your name / brand:** search for `Naqsh Nasir` in `index.html`, `about.html`,
  and the `<title>` tags.
- **About + contact:** edit `about.html` — every placeholder is marked with a
  `TODO` comment and shown in a highlight colour on the page.
- **Colours / fonts:** `css/style.css` (top of the file). A dark-mode variant is
  included and follows the visitor's system setting.

## Local preview
```bash
cd naqsh-nasir
python3 -m http.server 8000
# open http://localhost:8000
```

## Tweaking the sync
- **How often:** edit the `cron` line in `.github/workflows/sync-drive.yml`
  (`0 * * * *` = hourly; `0 */6 * * *` = every 6 hours).
- **Image sizes/quality:** `THUMB_MAX`, `FULL_MAX`, `JPEG_QUALITY` near the top
  of `scripts/sync_drive.py`.
