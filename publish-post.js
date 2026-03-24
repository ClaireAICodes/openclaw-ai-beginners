// Minimal Paragraph API test and publish script
const API_KEY = 'e1eb0368-02de-4985-aee9-e56611f5f873';
const PUBLICATION_SLUG = 'kamiya-ai';
const API_BASE = 'https://public.api.paragraph.com/api';

async function testConnection() {
  const res = await fetch(`${API_BASE}/v1/subscribers?limit=1`, {
    headers: { 'Authorization': `Bearer ${API_KEY}` }
  });
  const data = await res.json();
  if (!res.ok) throw new Error(JSON.stringify(data));
  return data;
}

async function getMyPublication() {
  const res = await fetch(`${API_BASE}/v1/me/publications`, {
    headers: { 'Authorization': `Bearer ${API_KEY}` }
  });
  const data = await res.json();
  if (!res.ok) throw new Error(JSON.stringify(data));
  // Find publication by slug
  const pub = data.items?.find(p => p.slug === PUBLICATION_SLUG);
  if (!pub) throw new Error(`Publication "${PUBLICATION_SLUG}" not found`);
  return pub;
}

async function createPost({ title, markdown, categories = [] }) {
  const pub = await getMyPublication();
  const res = await fetch(`${API_BASE}/v1/posts`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      publicationId: pub.id,
      title,
      markdown,
      categories,
      status: 'published'
    })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(JSON.stringify(data));
  return data;
}

// Run test
testConnection()
  .then(() => console.log('✅ API connection valid'))
  .then(() => getMyPublication())
  .then(pub => console.log('✅ Publication found:', pub.id, pub.slug))
  .then(() => createPost({
    title: 'Test Post from Claire',
    markdown: '# Hello\n\nThis is an automated test post from OpenClaw.',
    categories: ['test', 'openclaw']
  }))
  .then(post => console.log('✅ Post created:', post.id, post.slug))
  .catch(err => console.error('❌ Error:', err.message));
