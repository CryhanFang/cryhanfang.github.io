# Han Fang Homepage

A small, dependency-free academic homepage. Content lives in Markdown and the
site is generated as plain HTML.

## Edit content

- `content/about.md`
- `content/news.md`
- `content/publications.md`
- `content/honors.md`
- `content/education.md`

Selected publications use a small metadata block documented directly in
`content/publications.md`. Put publication images in `assets/images/`.

## Build

```powershell
python build.py
```

Then open `index.html` directly in a browser. No Ruby, Jekyll, Node.js, or web
server is required.
