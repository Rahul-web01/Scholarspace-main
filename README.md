<div align="center">

  # 🎓 ScholarSpace

  <h3><b>Free notes, previous year papers and practice sets, organised by year and subject</b></h3>

  <p>
    <img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" />
    <img src="https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white" />
    <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" />
    <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
    <img src="https://img.shields.io/badge/Google%20Drive-4285F4?style=for-the-badge&logo=googledrive&logoColor=white" />
    <img src="https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white" />
  </p>

  <p>
    <a href="https://github.com/Rahul-web01/Scholarspace-main/issues">Report a bug</a> ·
    <a href="https://github.com/Rahul-web01/Scholarspace-main/issues">Request a feature</a>
  </p>
</div>

---

## 📖 Overview

**ScholarSpace** is a free study-material hub for university students. Study material usually lives in scattered
WhatsApp groups and private drives; ScholarSpace puts it in one searchable place.

* **750+ files** across **90 subjects**: notes, previous year question papers (PYQs), practice sets, assignments and books.
* **B.Tech CSE, separate for each college, year by year**:
  * **BBD University**, matched to the 2026-27 syllabus (core subjects, Group A/B, electives).
  * **ITM College (AKTU)**, with AKTU-syllabus notes (core subjects, electives, open electives).

  The two colleges have different syllabi, notes and exam difficulty, so their material is never mixed.
* **BBA (BBD University), year by year**, matched to the 2023-24 NEP syllabus (core subjects, electives, skill courses).
* **Other courses too**: Mechanical, Electrical and Civil subjects, B.Pharm and Agriculture, plus official syllabus PDFs.

## ✨ Features

| Feature | Description |
| :--- | :--- |
| 🔎 **Instant search** | Search every subject and file from the home page (press <kbd>/</kbd>). |
| 📚 **College & year browsing** | Pick your college (BBD University or ITM College) and year to see only the subjects you study. |
| 🗂️ **Files grouped by type** | Each subject page splits Notes, PYQs, Practice and Books, with a filter box. |
| 👁️ **View or download** | Files open in Google Drive's viewer, or download in one click. No sign-in needed. |
| 🧮 **SGPA calculator** | Add subjects, credits and marks; SGPA, grades and average update live (10-point scale). |
| 🌗 **Light & dark mode** | Follows the system theme, with a toggle. |
| 📱 **Responsive** | Designed for phones first; works on tablets and desktops. |
| ✉️ **Contribute** | Students can share notes or request subjects through the contribute page. |

## 🛠️ How it works

```
Google Drive (public folder)  ──►  tools/crawl_drive.py   ──►  tools/drive-tree.tsv
                                   tools/build_catalog.py  ──►  assets/js/catalog.js  ──►  static site
```

* All study files live in one public Google Drive folder.
* `tools/crawl_drive.py` lists every file and folder in it (no API key needed).
* `tools/build_catalog.py` maps Drive folders and files to subjects (the `SUBJECTS` list) and writes `assets/js/catalog.js`.
* The site is plain HTML, CSS and JavaScript with no build step, hosted on Vercel.

```
scholarspace main/
├── index.html        Home: search, years, courses
├── browse.html       Course / year listing   (?program=btech-cse&year=2)
├── subject.html      One subject's files     (?id=dbms)
├── sgpa.html         SGPA calculator
├── about.html, feedback.html, 404.html
├── assets/css/style.css
├── assets/js/app.js       Layout, search and page rendering
├── assets/js/catalog.js   Generated: every subject and file
└── tools/                 Drive crawler and catalog builder
```

## 🚀 Run locally

```bash
git clone https://github.com/Rahul-web01/Scholarspace-main.git
cd "Scholarspace-main/scholarspace main"
python3 -m http.server 8000
```

Open http://localhost:8000.

## ➕ Adding new study material

1. Upload the files to the public **ScholarSpace Data** folder on Google Drive.
2. Refresh the file list and rebuild the catalog:
   ```bash
   cd "scholarspace main"
   python3 tools/crawl_drive.py 1KDEa-DkdkNl6FuhUDO9upWKTaSeQlRNC tools/drive-tree.tsv
   python3 tools/crawl_drive.py 1GhW9UVlo35eLvbHPEsSv4NiCul0hkml6 tools/bba-drive-tree.tsv   # BBA folder
   python3 tools/build_catalog.py
   ```
3. If the script prints `NOT LINKED:` lines, add those files or their folder to a subject in `SUBJECTS`
   (in `tools/build_catalog.py`; BBD University subjects use program `B`, ITM College subjects use `I`) and run it again. Optionally add a clean title in `tools/titles.tsv`.
4. Commit and push; Vercel redeploys automatically.

## 🔮 Roadmap

* [ ] Upload form that sends contributed notes straight to a review folder
* [ ] Year-wise pages for more programmes (B.Pharm, other B.Tech branches)
* [ ] Bookmark favourite subjects

## 📬 Author

**Rahul Singh**, Backend Developer and B.Tech CSE student at BBD University

<p align="left">
<a href="https://www.linkedin.com/in/rahul-singh-cs/" target="blank"><img align="center" src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn" /></a>
<a href="mailto:contact.rahul82@gmail.com" target="blank"><img align="center" src="https://img.shields.io/badge/Gmail-D14836?style=for-the-badge&logo=gmail&logoColor=white" alt="Email" /></a>
<a href="https://github.com/Rahul-web01" target="blank"><img align="center" src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub" /></a>
</p>
