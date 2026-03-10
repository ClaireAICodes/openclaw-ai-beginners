// Standalone test: simulate agent environment and call paragraph_testConnection
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Set env as would be injected by gateway
process.env.PARAGRAPH_API_KEY = 'e1eb0368-02de-4985-aee9-e56611f5f873';
process.env.PARAGRAPH_PUBLICATION_SLUG = 'kamiya-ai';

// Dynamically import the skill from shared location
async function test() {
  try {
    const skillPath = join(__dirname, '..', '.openclaw', 'skills', 'paragraph', 'skill.js');
    const skillModule = await import(skillPath);

    // The skill exports a tools object
    const { tools } = skillModule;

    console.log('Available tools:', Object.keys(tools));

    // Call testConnection
    const result = await tools.paragraph_testConnection();
    console.log('Test connection result:', JSON.stringify(result, null, 2));
  } catch (err) {
    console.error('Test failed:', err);
    process.exit(1);
  }
}

test();
