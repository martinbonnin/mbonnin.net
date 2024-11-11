import { getPermalink, getBlogPermalink, getAsset } from './utils/permalinks';

export const headerData = {
  links: [
    {
      text: 'Blog',
      href: getBlogPermalink()
    },
    {
      text: 'About',
      href: 'about',
    },
  ],
  socialLinks: [
    { ariaLabel: 'Bluesky', icon: 'tabler:brand-bluesky', href: 'https://bsky.app/profile/hcmartin.bsky.social' },
    { ariaLabel: 'Mastodon', icon: 'tabler:brand-mastodon', href: 'https://mastodon.mbonnin.net/@mb' },
    { ariaLabel: 'Github', icon: 'tabler:brand-github', href: 'https://github.com/martinbonnin/' },
  ],
};

export const footerData = {
  secondaryLinks: [
    { text: 'Contact', href: "mailto:webmaster@mbonnin.net" },
    { text: 'Public key', href: "/public_key" },
  ],
};
