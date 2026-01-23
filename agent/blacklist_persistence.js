import fs from 'fs';
import path from 'path';

const BLACKLIST_PATH = path.join(process.cwd(), 'agent', 'blacklist.json');

export function loadBlacklist() {
  try {
    if (fs.existsSync(BLACKLIST_PATH)) {
      const raw = fs.readFileSync(BLACKLIST_PATH, 'utf-8');
      return new Set(JSON.parse(raw));
    }
  } catch {}
  return new Set();
}

export function saveBlacklist(blacklist: Set<string>) {
  fs.writeFileSync(BLACKLIST_PATH, JSON.stringify(Array.from(blacklist)), 'utf-8');
}
