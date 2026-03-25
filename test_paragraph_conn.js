import { readFile } from 'node:fs/promises';

const skillPath = '/home/node/.openclaw/workspace/skills/paragraph/skill.js';
const skillModule = await import(`file://${skillPath}`);

process.env.PARAGRAPH_API_KEY = process.env.PARAGRAPH_API_KEY || '7e6d6c82-7d45-4d3d-ae57-972bb1efbbca';
process.env.PARAGRAPH_PUBLICATION_SLUG = process.env.PARAGRAPH_PUBLICATION_SLUG || 'kamiya-ai';

try {
  const result = await skillModule.tools.paragraph_testConnection();
  console.log('TEST RESULT:', JSON.stringify(result, null, 2));
  process.exit(0);
} catch (error) {
  console.error('TEST ERROR:', error.message);
  process.exit(1);
}
