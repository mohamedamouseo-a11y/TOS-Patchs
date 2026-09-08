import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

const sidebar = fs.readFileSync(new URL("./Sidebar.jsx", import.meta.url), "utf8");
const routes = fs.readFileSync(new URL("../../lib/pageRoutes.js", import.meta.url), "utf8");

function groupChildren(groupId) {
  const pattern = new RegExp(`\\{ id: "${groupId}"[^\\n]*children: \\[([^\\]]*)\\] \\}`);
  const match = sidebar.match(pattern);
  assert.ok(match, `missing sidebar group ${groupId}`);
  return match[1].match(/"([^"]+)"/g)?.map((value) => value.slice(1, -1)) || [];
}

test("TWS is owned by Workspace navigation group", () => {
  const workspace = groupChildren("workspaceGroup");
  const system = groupChildren("systemGroup");
  assert.ok(workspace.includes("tws"));
  assert.ok(!system.includes("tws"));
});

test("TWS appears exactly once across sidebar groups", () => {
  const occurrences = ["workspaceGroup", "teamGroup", "systemGroup"]
    .flatMap(groupChildren)
    .filter((id) => id === "tws");
  assert.equal(occurrences.length, 1);
});

test("active TWS page resolves its parent group from SIDEBAR_GROUPS", () => {
  assert.ok(sidebar.includes("SIDEBAR_GROUPS.find((item) => item.children.includes(active))"));
  assert.ok(sidebar.includes("SIDEBAR_GROUPS.find((item) => item.children.includes(pageId))"));
});

test("TWS route and deep-route ownership stay unchanged", () => {
  assert.ok(routes.includes('tws: "/tws"'));
  assert.ok(routes.includes('normalized === "/tws" || normalized.startsWith("/tws/")'));
  assert.ok(routes.includes('return "tws"'));
});

test("TWS navigation keeps the existing page id and icon wiring", () => {
  assert.ok(sidebar.includes("tws: FileText"));
  assert.ok(sidebar.includes("getNavItemAccess(childId, user)"));
  assert.ok(sidebar.includes("pathForPage"));
});
