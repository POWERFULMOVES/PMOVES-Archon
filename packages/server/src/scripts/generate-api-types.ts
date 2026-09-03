import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { OpenAPIHono } from '@hono/zod-openapi';
import { format, resolveConfig } from 'prettier';
import { registerApiRoutes } from '../routes/api';

const OUTPUT_PATH = resolve(import.meta.dir, '../../../web/src/lib/api.generated.d.ts');
const GENERATOR_PATH = resolve(
  import.meta.dir,
  '../../../web/node_modules/openapi-typescript/bin/cli.js'
);

async function generateApiTypes(): Promise<string> {
  const app = new OpenAPIHono();
  registerApiRoutes(app, {} as never, {} as never);

  const response = await app.request('/api/openapi.json');
  if (!response.ok) {
    throw new Error(`OpenAPI route returned ${response.status}.`);
  }

  const generator = Bun.spawn([process.execPath, GENERATOR_PATH], {
    stdin: new TextEncoder().encode(JSON.stringify(await response.json())),
    stdout: 'pipe',
    stderr: 'inherit',
  });
  const output = await new Response(generator.stdout).text();
  if ((await generator.exited) !== 0) {
    throw new Error('openapi-typescript failed.');
  }
  return format(output, { ...(await resolveConfig(OUTPUT_PATH)), parser: 'typescript' });
}

export type ApiTypesOutcome = 'ok' | 'stale' | 'written';

/**
 * Decides what to do with freshly generated types. Check mode must never write:
 * the CI guard only means anything if a stale tree stays stale, so the same
 * `--check` a developer runs reproduces the failure instead of quietly fixing it.
 */
export async function applyApiTypes(options: {
  outputPath: string;
  generated: string;
  checkOnly: boolean;
}): Promise<ApiTypesOutcome> {
  const { outputPath, generated, checkOnly } = options;
  if (!checkOnly) {
    await writeFile(outputPath, generated);
    return 'written';
  }

  // A Windows checkout with core.autocrlf holds byte-different but equivalent
  // content, so compare on normalized line endings rather than failing the guard.
  const existing = await readFile(outputPath, 'utf8');
  return existing.replace(/\r\n/g, '\n') === generated ? 'ok' : 'stale';
}

if (import.meta.main) {
  try {
    const outcome = await applyApiTypes({
      outputPath: OUTPUT_PATH,
      generated: await generateApiTypes(),
      checkOnly: process.argv.includes('--check'),
    });
    if (outcome === 'stale') {
      console.error('api.generated.d.ts is stale.\nRun: bun run generate:api-types');
      process.exit(2);
    }
    console.log(outcome === 'ok' ? 'check:api-types OK' : `Generated ${OUTPUT_PATH}`);
  } catch (error) {
    console.error(error instanceof Error ? error.message : error);
    process.exit(1);
  }
}
