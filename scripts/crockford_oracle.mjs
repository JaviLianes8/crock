// Reads {"encode": [hex, ...], "decode": [text, ...]} as JSON on stdin and prints what the
// base32-encode and base32-decode npm packages (Crockford variant) make of each: the code for
// every hex byte string, and the hex bytes (or null when it throws) for every text.
// Usage: node scripts/crockford_oracle.mjs <folder holding node_modules>
import { createRequire } from "node:module";
import path from "node:path";
import { pathToFileURL } from "node:url";

const folder = path.join(process.argv[2], "node_modules");
const encoder = await import(pathToFileURL(path.join(folder, "base32-encode", "index.js")).href);
const base32Decode = createRequire(path.join(folder, "noop.js"))("base32-decode");
const base32Encode = encoder.default;

let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => {
  input += chunk;
});
process.stdin.on("end", () => {
  const request = JSON.parse(input);
  const encoded = request.encode.map((hex) => base32Encode(Buffer.from(hex, "hex"), "Crockford"));
  const decoded = request.decode.map((text) => {
    try {
      return Buffer.from(base32Decode(text, "Crockford")).toString("hex");
    } catch {
      return null;
    }
  });
  process.stdout.write(JSON.stringify({ encode: encoded, decode: decoded }));
});
