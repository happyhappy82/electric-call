import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';

export async function GET(context: APIContext) {
  const posts = await getCollection('blog');
  return rss({
    title: '전기공사콜 — 전기공사 가이드',
    description: '전기공사 비용, 수리 방법, 업체 선택 기준까지. 전기 관련 모든 정보를 한곳에서.',
    site: context.site!.toString(),
    items: posts.map((post) => ({
      title: post.data.title,
      description: post.data.description,
      link: `/blog/${post.id}/`,
      pubDate: post.data.publishedAt ? new Date(post.data.publishedAt) : new Date(),
    })),
  });
}
