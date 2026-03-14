#!/usr/bin/env node
import tools from "/home/ubuntu/.openclaw/workspace/skills/paragraph/skill.js";

async function test() {
  const result = await tools.paragraph_testConnection({});
  console.log("Test connection result:", JSON.stringify(result, null, 2));
}
test();
