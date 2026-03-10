// End-to-end test: Load Paragraph skill directly and publish a test post
process.env.PARAGRAPH_API_KEY = 'e1eb0368-02de-4985-aee9-e56611f5f873';
process.env.PARAGRAPH_PUBLICATION_SLUG = 'kamiya-ai';

const skillPath = '/home/ubuntu/.openclaw/workspace/skills/paragraph/skill.js';

async function run() {
  try {
    // Dynamically import the skill module
    const skillModule = await import(`file://${skillPath}`);
    const tools = skillModule.tools;

    console.log('🧪 Testing Paragraph skill...\n');

    // 1. Test connection
    console.log('1️⃣ Testing connection with paragraph_testConnection...');
    const connResult = await tools.paragraph_testConnection({});
    if (!connResult.success) {
      throw new Error(`Connection failed: ${connResult.error}`);
    }
    console.log('✅ Connection successful!');
    console.log(`   Subscribers: ${connResult.data.totalSubscribers}\n`);

    // 2. Get publication info
    console.log('2️⃣ Getting publication info...');
    const pubResult = await tools.paragraph_getMyPublication({});
    if (!pubResult.success) {
      throw new Error(`Get publication failed: ${pubResult.error}`);
    }
    const pub = pubResult.data;
    console.log(`✅ Publication: ${pub.name} (${pub.slug || pub.customDomain})\n`);

    // 3. Create a test post
    console.log('3️⃣ Creating test post...');
    const timestamp = new Date().toISOString().slice(0,19).replace(/[:T]/g,'-');
    const testTitle = `OpenClaw Skill Test - ${timestamp}`;
    const testMarkdown = `# ${testTitle}\n\nThis is an automated test post from OpenClaw to verify the Paragraph skill is working correctly.\n\n**Test time:** ${new Date().toISOString()}\n\n---\n*If you see this, the skill is functioning!*`;

    const createResult = await tools.paragraph_createPost({
      title: testTitle,
      markdown: testMarkdown,
      categories: ['test', 'openclaw', 'automation'],
      sendNewsletter: false
    });

    if (!createResult.success) {
      throw new Error(`Create post failed: ${createResult.error}`);
    }

    const post = createResult.data;
    console.log('✅ Post created successfully!');
    console.log(`   ID: ${post.id}`);
    console.log(`   Slug: ${post.slug || '(processing...)'}`);
    console.log(`   URL: ${post.url || '(pending...)'}\n`);

    // 4. Construct full URL if not immediate
    if (!post.url && pub.slug) {
      const expectedUrl = `https://paragraph.com/@${pub.slug}/${post.slug}`;
      console.log(`⚠️  Post is processing. Full URL should be: ${expectedUrl}\n`);
    }

    console.log('🎉 All tests passed! The Paragraph skill is fully functional.');

  } catch (err) {
    console.error('\n❌ TEST FAILED:', err.message);
    process.exit(1);
  }
}

run();
