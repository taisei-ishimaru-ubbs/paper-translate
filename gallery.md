---
cssclasses:
  - paper-gallery
---

# Papers

```dataviewjs
const adapter = app.vault.adapter;

const notes = dv
  .pages("#paper")
  .sort((page) => page.published, "desc")
  .array();

async function exists(path) {
  try { return await adapter.exists(path); } catch { return false; }
}

function dirname(path) {
  const i = path.lastIndexOf("/");
  return i === -1 ? "" : path.slice(0, i);
}

function openVaultPath(path, event) {
  event.preventDefault();
  app.workspace.openLinkText(path, "", false);
}

function resourceUrl(path) {
  const file = app.vault.getAbstractFileByPath(path);
  return file ? app.vault.getResourcePath(file) : "";
}

async function imageFor(page) {
  const thumb = page.thumbnail ? String(page.thumbnail) : "";
  if (thumb && (await exists(thumb))) return thumb;
  if (thumb) {
    const fallback = `${dirname(thumb)}/overview.png`;
    if (await exists(fallback)) return fallback;
  }
  return "";
}

async function linksFor(page) {
  const out = [["note", page.file.path]];
  const folder = page.thumbnail ? dirname(String(page.thumbnail)) : "";
  if (folder) {
    const summary = `${folder}/summary.md`;
    const ja = `${folder}/paper_ja.pdf`;
    const pdf = `${folder}/paper.pdf`;
    if (await exists(summary)) out.push(["summary", summary]);
    if (await exists(ja)) out.push(["日本語PDF", ja]);
    if (await exists(pdf)) out.push(["原文PDF", pdf]);
  }
  return out;
}

const papers = [];
for (const page of notes) {
  papers.push({
    title: page.title ? String(page.title) : page.file.name,
    folder: page.thumbnail ? dirname(String(page.thumbnail)) : page.file.folder,
    notePath: page.file.path,
    imagePath: await imageFor(page),
    links: await linksFor(page),
  });
}

const view = dv.el("div", "", { cls: "paper-gallery-view" });
const tools = view.createDiv({ cls: "paper-gallery-tools" });
const search = tools.createEl("input", {
  cls: "paper-gallery-search",
  attr: { type: "search", placeholder: "Search papers", "aria-label": "Search papers" },
});
const count = tools.createSpan({ cls: "paper-gallery-count" });
const grid = view.createDiv({ cls: "paper-gallery-grid" });

function addInternalLink(parent, label, path, cls) {
  const link = parent.createEl("a", { text: label, cls });
  link.href = path;
  link.setAttr("data-href", path);
  link.addEventListener("click", (event) => openVaultPath(path, event));
  return link;
}

function render(filter = "") {
  const needle = filter.trim().toLowerCase();
  const shown = papers.filter((paper) =>
    `${paper.title} ${paper.folder}`.toLowerCase().includes(needle)
  );

  grid.empty();
  count.setText(`${shown.length} / ${papers.length}`);

  for (const paper of shown) {
    const card = grid.createDiv({ cls: "paper-card" });
    const imageBox = card.createDiv({ cls: "paper-card-image" });
    const imageUrl = paper.imagePath ? resourceUrl(paper.imagePath) : "";
    if (imageUrl) {
      imageBox.createEl("img", { attr: { src: imageUrl, alt: paper.title, loading: "lazy" } });
    } else {
      imageBox.createDiv({ cls: "paper-card-placeholder", text: "NO IMAGE" });
    }

    const body = card.createDiv({ cls: "paper-card-body" });
    addInternalLink(body, paper.title, paper.notePath, "paper-card-title");
    body.createDiv({ cls: "paper-card-folder", text: paper.folder });

    const links = body.createDiv({ cls: "paper-card-links" });
    for (const [label, path] of paper.links) {
      addInternalLink(links, label, path, "paper-card-link");
    }
  }
}

search.addEventListener("input", () => render(search.value));
render();
```
