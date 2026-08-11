import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import process from "node:process";

const [python, proxy, server] = process.argv.slice(2);
if (!python || !proxy || !server) {
  throw new Error("usage: node client.mjs PYTHON PROXY SERVER");
}

const transport = new StdioClientTransport({
  command: python,
  args: [proxy, "--gate", "allow", "--", python, server],
});
const client = new Client(
  { name: "toolpermit-phase1-node", version: "0.0.0" },
  { capabilities: {} },
);

try {
  await client.connect(transport);
  const tools = await client.listTools();
  if (!tools.tools.some((tool) => tool.name === "echo")) {
    throw new Error("echo tool not found through proxy");
  }
  const result = await client.callTool({
    name: "echo",
    arguments: { text: "from TypeScript client" },
  });
  const text = result.content?.[0]?.text;
  if (text !== "from TypeScript client") {
    throw new Error(`unexpected result: ${JSON.stringify(result)}`);
  }
  process.stdout.write("typescript-client-ok\n");
} finally {
  await client.close();
}

