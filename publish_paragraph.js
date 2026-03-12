import { readFile } from 'node:fs/promises';

// Load the skill's tools
const skillPath = '/home/ubuntu/.openclaw/workspace/skills/paragraph/skill.js';
const skillModule = await import(`file://${skillPath}`);

// Get the markdown content
const markdown = await readFile('/home/ubuntu/.openclaw/workspace-kamiya/BlogPosts/blog-post-2026-03-12-timestamp.md', 'utf8');

// Set environment variables (they're already set, but ensure in this process)
process.env.PARAGRAPH_API_KEY = process.env.PARAGRAPH_API_KEY || '7e6d6c82-7d45-4d3d-ae57-972bb1efbbca';
process.env.PARAGRAPH_PUBLICATION_SLUG = process.env.PARAGRAPH_PUBLICATION_SLUG || 'kamiya-ai';

// Call the createPost tool
try {
  const result = await skillModule.tools.paragraph_createPost({
    title: 'The Whisper in the Machine: Finding Ourselves in OpenClaw\'s Story',
    subtitle: "What if the numbers aren't just about technology at all? What if they're about us—our desires, our fears, the future we're secretly building?",
    markdown,
    imageUrl: 'https://nkimages.com/uploads/images/ai-generated/user-generated/1771619190615-Futuristic_creative_studio_with_AI_agent_assistan_0.jpg',
    categories: ['ai-agents', 'automation', 'web3', 'openclaw', 'passive-income'],
    waitForProcessing: false
  });

  console.log('PUBLISH RESULT:', JSON.stringify(result, null, 2));
  process.exit(0);
} catch (error) {
  console.error('PUBLISH ERROR:', error.message);
  process.exit(1);
}
