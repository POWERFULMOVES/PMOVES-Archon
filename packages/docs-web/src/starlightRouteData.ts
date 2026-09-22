import { defineRouteMiddleware } from '@astrojs/starlight/route-data';
import { hasRawMarkdownMirror } from './raw-markdown';

export const onRequest = defineRouteMiddleware(async (context, next) => {
  await next();

  // Starlight uses this same boundary to distinguish content routes from its synthetic 404.
  if (!('slug' in context.params)) return;

  const { entry, head } = context.locals.starlightRoute;
  const siteUrl = context.site ?? new URL(context.url.origin);
  const pageUrl = new URL(context.url.pathname, siteUrl).href;
  const pageTitle = entry.data.title;
  const pageDescription = entry.data.description ?? 'Archon documentation';

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'TechArticle',
    headline: pageTitle,
    description: pageDescription,
    url: pageUrl,
    isPartOf: {
      '@type': 'WebSite',
      name: 'Archon',
      url: siteUrl.href,
    },
  };

  head.push({
    tag: 'script',
    attrs: { type: 'application/ld+json' },
    content: JSON.stringify(jsonLd).replace(/</g, '\\u003c'),
  });

  if (!hasRawMarkdownMirror(entry.filePath)) return;

  const pathname = context.url.pathname;
  const markdownPath =
    pathname === '/'
      ? 'index.md'
      : `${pathname.endsWith('/') ? pathname.slice(0, -1) : pathname}.md`;

  head.push({
    tag: 'link',
    attrs: {
      rel: 'alternate',
      type: 'text/markdown',
      href: new URL(markdownPath, siteUrl).href,
      title: `${pageTitle} (Markdown)`,
    },
  });
});
