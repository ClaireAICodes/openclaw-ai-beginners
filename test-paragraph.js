// Test paragraph_testConnection()
import tools from '/home/ubuntu/.nvm/versions/node/v24.13.0/lib/node_modules/openclaw/skills/paragraph/skill.js';

async function run() {
  try {
    const result = await tools.paragraph_testConnection({});
    console.log('SUCCESS:', JSON.stringify(result, null, 2));
  } catch (err) {
    console.error('ERROR:', err);
  }
}

run();
