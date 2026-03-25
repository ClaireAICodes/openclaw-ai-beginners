#!/usr/bin/env node
import tools from "/home/node/.openclaw/workspace/skills/paragraph/skill.js";

async function publish() {
  try {
    const title = "The Trust Deficit: Building AI Agents in an Era of Malicious Skills";
    const subtitle = "What the latest OpenClaw research teaches us about responsible automation";
    const coverImage = "https://nkimages.com/uploads/images/saas/ai-features/1767080314905-AI_summarization_of_documents_and_data_in_SaaS_au_1.jpg";
    const categories = ["ai-agents", "openclaw", "security", "automation", "web3"];

    // Read markdown body
    const fs = await import("fs");
    const path = await import("path");
    const markdown = fs.readFileSync("/home/node/.openclaw/workspace/BlogPosts/blog-post-20260217-trust-deficit.md", "utf-8");

    console.log("Publishing to Paragraph...");

    const result = await tools.paragraph_createPost({
      title,
      markdown,
      subtitle,
      imageUrl: coverImage,
      categories,
      sendNewsletter: false,
      waitForProcessing: true
    });

    if (result.success) {
      console.log("✅ Publish succeeded!");
      console.log("Post ID:", result.data.id);
      console.log("Slug:", result.data.slug);
      console.log("URL:", result.data.url);
    } else {
      console.error("❌ Publish failed:", result.error);
      process.exit(1);
    }
  } catch (err) {
    console.error("Script error:", err);
    process.exit(1);
  }
}

publish();
