// Direct test of paragraph skill - bypass agent tool system
import { readFile } from 'node:fs/promises';
import { moduleProvider } from 'node:module';

async function loadSkill() {
  const skillPath = '/home/node/.openclaw/workspace/skills/paragraph/skill.js';
  const skillCode = await readFile(skillPath, 'utf-8');

  // Create a module context with proper env vars
  const sandbox = {
    process: {
      env: {
        PARAGRAPH_API_KEY: 'e1eb0368-02de-4985-aee9-e56611f5f873',
        PARAGRAPH_PUBLICATION_SLUG: 'kamiya-ai',
        PARAGRAPH_API_BASE_URL: 'https://public.api.paragraph.com/api'
      },
      // Stub console to capture output
      console: console,
      // Stub fetch - Node doesn't have global fetch in older versions, but skill uses native fetch
    },
    // Provide global fetch if not available
    globalThis: {
      fetch: async (...args) => {
        const res = await (await import('node-fetch')).default(...args);
        return res;
      }
    }
  };

  // Since skill.js is ES module, we need to evaluate it in a clean context
  // But simpler: just run the skill's test.js which already does this
  const { exec } = await import('node:child_process');
  const { promisify } = await import('node:util');
  const execAsync = promisify(exec);

  try {
    // Run test.js with explicit env vars
    const { stdout, stderr } = await execAsync(
      `PARAGRAPH_API_KEY="e1eb0368-02de-4985-aee9-e56611f5f873" PARAGRAPH_PUBLICATION_SLUG="kamiya-ai" node /home/node/.openclaw/workspace/skills/paragraph/test.js`,
      { maxBuffer: 1024 * 1024 }
    );
    console.log('STDOUT:', stdout);
    if (stderr) console.error('STDERR:', stderr);
  } catch (err) {
    console.error('Execution error:', err);
  }
}

loadSkill().catch(console.error);
