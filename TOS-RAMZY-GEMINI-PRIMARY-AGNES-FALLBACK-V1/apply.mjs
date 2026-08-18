#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";

const targetRoot = path.resolve(process.argv[2] || "/var/www/TOS");

const ignoredDirs = new Set([
  ".git",
  "node_modules",
  "dist",
  "build",
  ".next",
  "coverage",
  ".cache",
  "vendor",
]);

const allowedExtensions = new Set([
  ".ts",
  ".tsx",
  ".js",
  ".jsx",
  ".mjs",
  ".cjs",
  ".json",
]);

const strongSignatures = [
  "AGENT_SETTINGS_ENCRYPTION_KEY",
  "OpenAI API key is not configured",
  "gpt-4.1-mini",
  "Mastra Agency Operator",
];

const weakSignatures = ["Ramzy", "رمزي"];
const providerHints = [
  "openai",
  "provider",
  "model",
  "agent",
  "mastra",
  "chat/completions",
];

function fail(message, code = 2) {
  if (message) console.error(message);
  console.log("PATCH_BASE_MISMATCH");
  process.exit(code);
}

if (!fs.existsSync(targetRoot) || !fs.statSync(targetRoot).isDirectory()) {
  fail(`Target directory does not exist: ${targetRoot}`);
}

const files = [];

function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.isDirectory()) {
      if (!ignoredDirs.has(entry.name)) walk(path.join(dir, entry.name));
      continue;
    }

    const fullPath = path.join(dir, entry.name);
    if (!allowedExtensions.has(path.extname(entry.name).toLowerCase())) continue;

    let stat;
    try {
      stat = fs.statSync(fullPath);
    } catch {
      continue;
    }

    if (stat.size > 2 * 1024 * 1024) continue;
    files.push(fullPath);
  }
}

walk(targetRoot);

const matches = new Map();
const candidateScores = [];

for (const file of files) {
  let content;
  try {
    content = fs.readFileSync(file, "utf8");
  } catch {
    continue;
  }

  const foundStrong = strongSignatures.filter((sig) => content.includes(sig));
  const foundWeak = weakSignatures.filter((sig) => content.includes(sig));

  if (foundStrong.length || foundWeak.length) {
    matches.set(file, { foundStrong, foundWeak });
  }

  const lower = `${file}\n${content}`.toLowerCase();
  let score = 0;
  for (const hint of providerHints) {
    if (lower.includes(hint.toLowerCase())) score += 1;
  }
  if (foundStrong.length) score += foundStrong.length * 5;
  if (foundWeak.length) score += foundWeak.length * 2;

  if (score >= 4) candidateScores.push({ file, score });
}

const strongFound = new Set();
for (const { foundStrong } of matches.values()) {
  for (const sig of foundStrong) strongFound.add(sig);
}

if (strongFound.size < 2) {
  console.error(
    `Expected live Ramzy source signatures were not found. Found ${strongFound.size}/4 strong signatures.`,
  );
  if (matches.size) {
    console.error("Partial Ramzy-related matches:");
    for (const [file, result] of matches.entries()) {
      console.error(
        `- ${path.relative(targetRoot, file)} :: ${[
          ...result.foundStrong,
          ...result.foundWeak,
        ].join(", ")}`,
      );
    }
  }
  fail();
}

candidateScores.sort((a, b) => b.score - a.score);
const candidates = candidateScores.slice(0, 12);

console.log("PATCH_BASE_MATCH");
console.log(`Target: ${targetRoot}`);
console.log(`Strong signatures matched: ${[...strongFound].join(", ")}`);
console.log("Matched files:");
for (const [file, result] of matches.entries()) {
  console.log(
    `- ${path.relative(targetRoot, file)} :: ${[
      ...result.foundStrong,
      ...result.foundWeak,
    ].join(", ")}`,
  );
}

console.log("Candidate Ramzy/provider files (highest confidence first):");
for (const item of candidates) {
  console.log(`- ${path.relative(targetRoot, item.file)} [score=${item.score}]`);
}

console.log(
  "NO_FILES_CHANGED: This guard only validates the live source. Apply RAMZY_PROVIDER_SPEC.md only to the matched Ramzy/model-provider integration point.",
);
