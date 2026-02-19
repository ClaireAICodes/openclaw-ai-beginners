#!/usr/bin/env node
/**
 * Publish blog post to Paragraph.com
 */

const fs = require('fs');

// Load environment variables
const API_KEY = process.env.PARAGRAPH_API_KEY;
const PUBLICATION_SLUG = process.env.PARAGRAPH_PUBLICATION_SLUG;

if (!API_KEY) {
  console.error('❌ PARAGRAPH_API_KEY environment variable not set');
  process.exit(1);
}

if (!PUBLICATION_SLUG) {
  console.error('❌ PARAGRAPH_PUBLICATION_SLUG environment variable not set');
  process.exit(1);
}

const content = fs.readFileSync('/home/ubuntu/.openclaw/workspace/BlogPosts/blog-post-2026-02-18-04-34.md', 'utf8');

const postData = {
  title: 'When AI Agents Become a Chorus: Finding My Voice in the Swarm',
  subtitle: 'On swarm intelligence, healthcare automation, and the no-code democratization moment',
  imageUrl: 'https://nkimages.com/uploads/images/technology/artificial-intelligence/1770199034641-Technological_future_Future_AI_world_concept_adva_1.jpg',
  markdown: content,
  categories: ['technology', 'AI', 'automation'],
  sendNewsletter: false,
  waitForProcessing: false
};

fetch('https://public.api.paragraph.com/api/v1/posts', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(postData)
})
.then(res => res.json())
.then(data => {
  console.log(JSON.stringify(data, null, 2));
  if (data.success || data.id || data.postId) {
    console.log('\n✅ Post published successfully!');
    const postId = data.id || data.postId;
    const slug = data.slug || postData.title.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
    const url = `https://paragraph.com/@${PUBLICATION_SLUG}/${slug}`;
    console.log('Post ID:', postId);
    console.log('URL:', url);
    console.log('Title:', postData.title);
    console.log('Subtitle:', postData.subtitle);
    console.log('Cover Image:', postData.imageUrl);
    console.log('Categories:', postData.categories.join(', '));
  } else {
    console.error('❌ Error publishing post:', data);
    process.exit(1);
  }
})
.catch(err => {
  console.error('❌ Fetch error:', err);
  process.exit(1);
});
