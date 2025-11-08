Dev:

```shell
npm ci
npm run dev
```

Deploy:

```shell
npm ci
npm run build
firebase deploy --only hosting
```

Fix formatting:

```shell
npm run fix:prettier
```

Features:

- everything is markdown with codeblocks support
- image resizing
- RSS feed
- mobile UI
- dark mode
- "edit on GitHub"
- Youtube/Bluesky embeds, .mdx support
- social card previews

Missing:

- anchor links
- admonitions
- site map (left column)
- table of contents (right column)
- comments (mastodon integration? like on https://www.liutikas.net/2025/01/10/Conservative-Librarian.html)
