// Assemble everything the Worker deploys, into shapes wrangler expects:
//   1. src/eigencircuits_engine/  - the pure-Python engine (Pyodide import)
//   2. assets/                    - built SPA + TeX Live mirror + _headers
//
// `assets/` and the vendored engine are build output and are not checked in.
import { cpSync, existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..', '..');

// 1. Vendor the engine next to entry.py.
const engineSrc = join(root, 'packages/engine/eigencircuits_engine');
const engineDst = join(here, 'src/eigencircuits_engine');
rmSync(engineDst, { recursive: true, force: true });
cpSync(engineSrc, engineDst, {
  recursive: true,
  filter: (src) => !src.includes('__pycache__'),
});

// 2. Assemble static assets: SPA build, then the TeX Live mirror.
const dist = join(root, 'apps/web/dist');
if (!existsSync(dist)) {
  console.error('No web build found. Run `pnpm --filter @eigencircuits/web build` first.');
  process.exit(1);
}
const assets = join(here, 'assets');
rmSync(assets, { recursive: true, force: true });
mkdirSync(assets, { recursive: true });
cpSync(dist, assets, { recursive: true });
cpSync(join(here, 'texlive'), join(assets, 'texlive'), { recursive: true });

// 3. Generate _headers so each TeX file carries the `fileid` header the pdfTeX
//    worker uses to name it in its virtual filesystem.
const manifest = JSON.parse(readFileSync(join(here, 'texlive/manifest.json'), 'utf8'));
const blocks = Object.entries(manifest).map(
  ([rel, fileid]) =>
    `/texlive/${rel}\n` +
    `  fileid: ${fileid}\n` +
    `  Access-Control-Expose-Headers: fileid\n` +
    `  Cache-Control: public, max-age=31536000, immutable\n`,
);
writeFileSync(join(assets, '_headers'), blocks.join('\n') + '\n');

console.log(`vendored engine and assembled ${blocks.length} TeX files into assets/`);
