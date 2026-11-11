#!/usr/bin/env node
// coding-agent.mjs - the coding-agent benchmark eval of ApolloKnowledgeBase
// (step 5). The eval itself is the section "the coding-agent eval" below;
// the rest is the build-eval runner scaffold of the claude-api skill, as in
// question-page.mjs.
//
//   node evals/coding-agent.mjs --variant baseline|v1 [--only id,id] [--include-drafts]
//
// Structural properties this encodes (so you don't have to remember them):
//   - parameterized by --variant / --model / --reps (no hardcoded A/B pair)
//   - rep-aware filenames + resume (traces/<id>_rep<k>.json)
//   - reads _state.json, never writes it (loop state belongs to the orchestrator) - 
//     the ONE exception is --approve-harness recording `harness_sha` (see below)
//   - refuses to run when the harness (this file + _state.json.harness_paths) has
//     changed since the sha a human last approved with --approve-harness, so a
//     round that edits the runner cannot execute unreviewed under a standing
//     session allowlist
//   - pairwise graders judge against frozen baseline/ref/<id>.* on disk
//   - writes rows as cases complete (crash-safe)
//   - jittered exponential backoff on transient 429/overloaded/5xx errors
//   - hard per-case wall-clock ceiling (--timeout-s; stream keepalives don't reset it)
//   - served-model assertion (response model must match --model; documented alias->snapshot
//     shapes tolerated: 'foo-latest'/'foo-0'/'foo' -> 'foo-20250101' / 'foo@20250101' / 'foo-2025-01-01')
//   - failed attempts land in errors.jsonl with a failure class and, when the call
//     completed, the billed model/usage (never in results.jsonl)
//   - row ids, trace filenames, and frozen refs share one path-safe id
//     (original id kept in meta.original_id when sanitization changed it)

import { createHash } from 'node:crypto';
import { closeSync, constants as FS, existsSync, fstatSync, ftruncateSync, lstatSync, mkdirSync, openSync, readFileSync, realpathSync, writeFileSync, writeSync } from 'node:fs';
import { dirname, isAbsolute, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

// Every output write refuses symlinks: the flow dir is model-influenced, and a
// prompt-injected round can plant `results.jsonl -> ~/.bashrc` where the next
// unattended run would append. POSIX opens O_NOFOLLOW (a symlink fails with
// ELOOP); Windows - where Node leaves O_NOFOLLOW undefined and Bun defines a
// meaningless value - lstat-refuses first. Symlinked parent dirs are
// refused the same way. Same discipline as the report builders' reads.
const WIN = process.platform === 'win32';
const NOFOLLOW = WIN ? 0 : FS.O_NOFOLLOW;
// A guard that cannot tell must refuse: only "no such entry" reads as absent;
// any other lstat failure (EACCES, ENAMETOOLONG, ...) is rethrown, never "no".
const lstatOrNull = p => { try { return lstatSync(p); } catch (e) { if (e?.code === 'ENOENT') return null; throw e; } };
const isSymlink = p => lstatOrNull(p)?.isSymbolicLink() === true;
// Stderr lines interpolate model-influenced bytes (case ids, error text that
// can echo model output, JSON.parse messages). Strip escape sequences and
// control characters, as build-report-lite.mjs's eprint does, so a planted
// OSC/CSI can't retitle the terminal or forge output lines.
const ESC_SEQ = /\x1b\[[0-?]*[ -\/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)?|\x1b[@-_]/g;
const CONTROL = /[\x00-\x1f\x7f-\x9f]/g;
const termSafe = s => String(s).replace(ESC_SEQ, '').replace(CONTROL, '');
const eprint = (...a) => console.error(...a.map(termSafe));
// The leaf checks above can't see a symlink on an INTERMEDIATE component
// (lstat and open both resolve those silently), so every open is also bound
// to the flow root: main() captures realpathSync(flow) once, and any path
// whose resolved parent leaves it - e.g. `vdir` or the flow dir itself
// replaced by a directory symlink - is refused when the check sees it.
// Residual, all platforms: the check and the open are separate path lookups
// (Node's sync fs has no openat-style call), so a directory swapped for a
// symlink in between is still followed. This stops a planted link, not a
// writer racing the run.
let flowRealRoot = null;
function assertInFlow(dir, what) {
  if (flowRealRoot == null) throw new Error(`refusing to ${what}: flow root not resolved yet`);
  const dirReal = realpathSync(dir);
  if (dirReal !== flowRealRoot && !dirReal.startsWith(flowRealRoot + (WIN ? '\\' : '/')))
    throw new Error(`refusing to ${what}: ${dir} resolves outside the flow directory`);
}
function openNoFollow(p, flags) {
  if (isSymlink(dirname(p))) throw new Error(`refusing to open through symlinked directory: ${dirname(p)}`);
  assertInFlow(dirname(p), 'open');
  if (WIN && isSymlink(p)) throw new Error(`refusing to open through symlink: ${p}`);
  const fd = openSync(p, flags | NOFOLLOW, 0o644);
  try {
    const st = fstatSync(fd);
    if (!st.isFile()) throw new Error(`refusing to use non-regular file: ${p}`);
    // O_NOFOLLOW and lstat cannot see a hard link: a second name for a file
    // outside the flow dir opens as an ordinary regular file. Nothing the
    // runner creates has more than one link, so refuse any that does.
    if (st.nlink > 1) throw new Error(`refusing to use ${p}: it has a second hard link (another name for the same file); replace it with a plain copy if it is yours`);
  } catch (e) { closeSync(fd); throw e; }
  return fd;
}
// writeFileSync on the fd loops until every byte lands (a bare writeSync is
// one write(2) that may return short on ENOSPC and silently truncate a
// results row or trace).
// Opened without O_TRUNC and truncated only after openNoFollow's checks, so a
// refused file keeps its bytes.
function writeFileNoFollow(p, data) {
  const fd = openNoFollow(p, FS.O_WRONLY | FS.O_CREAT);
  try { ftruncateSync(fd, 0); writeFileSync(fd, data); } finally { closeSync(fd); }
}
// POSIX appends atomically under O_APPEND with no position. On Windows, Bun
// writes an O_APPEND handle at offset 0 unless given a position, so there the
// write starts at the current size and re-issues any short write.
function appendFileNoFollow(p, data) {
  const fd = openNoFollow(p, FS.O_WRONLY | FS.O_CREAT | FS.O_APPEND);
  try {
    if (!WIN) { writeFileSync(fd, data); return; }
    const buf = Buffer.from(data);
    const start = fstatSync(fd).size;
    for (let off = 0; off < buf.length;) {
      const n = writeSync(fd, buf, off, buf.length - off, start + off);
      if (n <= 0) throw new Error(`append to ${p} made no progress`);
      off += n;
    }
  } finally { closeSync(fd); }
}
// Reads of the frozen pairwise refs get the same discipline as writes (same
// open guard): the flow dir is model-influenced, so `baseline/ref/<id> ->
// ~/.ssh/id_rsa` planted after the startup preflight must not be read into
// the judge prompt. lexists probes with lstat so a planted symlink still
// counts as "present" at the freeze guard (never overwritten - or followed).
const lexists = p => lstatOrNull(p) != null;
function readFileNoFollow(p) {
  const fd = openNoFollow(p, FS.O_RDONLY);
  try { return readFileSync(fd, 'utf8'); } finally { closeSync(fd); }
}
// null when the file is absent; any other failure (a planted link included) throws.
function readIfPresent(p) {
  try { return readFileNoFollow(p); } catch (e) { if (e?.code === 'ENOENT') return null; throw e; }
}
function mkdirNoFollow(dir) {
  if (isSymlink(dir)) throw new Error(`refusing to use symlinked directory: ${dir}`);
  mkdirSync(dir, { recursive: true });
  // Check after creating: mkdirSync(recursive) follows symlinked ancestors,
  // so a dir minted through one resolves outside the flow root and is refused
  // here before any file lands in it.
  assertInFlow(dir, 'create directory');
}
// Frozen pairwise refs may carry an extension; reader and freeze-guard probe
// the same list so a suffixed ref never gets an extensionless shadow.
const REF_EXTS = ['', '.html', '.txt', '.json'];

// --- the coding-agent eval (AKB step 5) --------------------------------------
//
// Runs the tasks of ApolloKnowledgeBase-Tasks/coding-agent/tasks.yaml with
// Claude Code (headless, `claude -p`, Opus 5.5) in a fresh project folder per
// (task, rep), in two conditions, one per variant directory:
//
//   baseline   without the knowledge base: the project has the ApolloCrossDev
//              Makefile, the task's starting files and an AGENTS.md that
//              states the target (OS, mode, build command), nothing more
//   v1 (v<N>)  with the knowledge base: the same project, plus this AKB
//              checkout at HEAD as ApolloKnowledgeBase/, the AGENTS.md and
//              CLAUDE.md of the apollo-new-project skill, and the akb plugin
//
// In both, Claude Code runs with an empty config dir (no user settings,
// memory or plugins), no web tools, file edits only inside the project, and
// Bash only for make and the ApolloCrossDev compiler tools.
//
// Grading, per result:
//   build     `make` with ApolloCrossDev ends with exit 0, an executable and
//             no warnings
//   checks    the task's text checks on the project files (`file:`) or on
//             the assembly GCC emits for a C file with the project's flags
//             (`asm:`), each `expect` or `expect_not` a regular expression
//   facts / no_wrong   Sonnet 5.5 reads the project's sources and the agent's
//             final message and grades them against the task's checklist
//   pass      build and checks and every fact and no wrong item
//
//   node evals/coding-agent.mjs --variant baseline [--only id,id] [--include-drafts]
//   node evals/coding-agent.mjs --variant v1       [--only id,id] [--include-drafts]
//
// Environment:
//   AKB_TASKS       the ApolloKnowledgeBase-Tasks clone (default ~/ApolloKnowledgeBase-Tasks)
//   APOLLOCROSSDEV  the ApolloCrossDev folder (default ~/ApolloCrossDev)
//   AKB_CLAUDE      the claude binary (default: `claude` on PATH, else the
//                   newest one in the VS Code extension)
// The API key comes from the macOS Keychain (service akb-evals-anthropic).
// Results go to build/evals/coding-agent/<variant>/ (git-ignored: they reveal
// the private tasks; never commit them); the finished projects are in
// build/evals/coding-agent/<variant>/projects/<id>_rep<k>/.

import { execFileSync, spawn, spawnSync } from 'node:child_process';
import { cpSync, readdirSync, rmSync, statSync } from 'node:fs';
import { homedir, tmpdir } from 'node:os';

const AKB_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const TASKS_REPO = process.env.AKB_TASKS || join(homedir(), 'ApolloKnowledgeBase-Tasks');
const ACD = process.env.APOLLOCROSSDEV || join(homedir(), 'ApolloCrossDev');
const ACD_BIN = join(ACD, 'Compilers', 'GCC-6.50-Dev', 'bin');
const JUDGE_MODEL = 'claude-sonnet-5-5';
const AGENT_BUDGET_USD = 5;          // --max-budget-usd per agent run
const WORK = join(tmpdir(), 'akb-evals-coding');

const NONINTERACTIVE = 'You are running non-interactively: nobody can answer questions or approve anything. Make reasonable choices, state them in your final message, and finish the task.';

let client = null;   // the judge
let apiKey = null;
let claudeBin = null;

function sh(cmd, args, opts = {}) {
  return execFileSync(cmd, args, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], ...opts }).trim();
}

function findClaude() {
  if (process.env.AKB_CLAUDE) return process.env.AKB_CLAUDE;
  try { return sh('sh', ['-c', 'command -v claude']); } catch {}
  const ext = join(homedir(), '.vscode', 'extensions');
  const dirs = existsSync(ext) ? readdirSync(ext).filter(d => d.startsWith('anthropic.claude-code-')) : [];
  const ver = d => d.match(/(\d+)\.(\d+)\.(\d+)/).slice(1).map(Number);
  dirs.sort((a, b) => { const x = ver(a), y = ver(b); return x[0] - y[0] || x[1] - y[1] || x[2] - y[2]; });
  for (const d of dirs.reverse()) {
    const p = join(ext, d, 'resources', 'native-binary', 'claude');
    if (existsSync(p)) return p;
  }
  throw new Error('claude not found: set AKB_CLAUDE');
}

async function prepare(ctx) {
  apiKey = sh('security', ['find-generic-password', '-s', 'akb-evals-anthropic', '-w']);
  if (!apiKey) throw new Error('no API key in the Keychain (service akb-evals-anthropic)');
  const { default: Anthropic } = await import(join(homedir(), 'ApolloKnowledgeBase-Manager', 'node_modules', '@anthropic-ai', 'sdk', 'index.mjs'));
  client = new Anthropic({ apiKey });
  claudeBin = findClaude();
  if (!existsSync(join(ACD_BIN, 'm68k-amigaos-gcc'))) throw new Error(`no ApolloCrossDev compiler in ${ACD_BIN} (set APOLLOCROSSDEV)`);
  const sha = sh('git', ['-C', AKB_ROOT, 'rev-parse', 'HEAD']);
  if (sh('git', ['-C', AKB_ROOT, 'status', '--porcelain', '--untracked-files=no']))
    eprint('note: the AKB checkout has uncommitted changes; the KB given to the agent is HEAD, without them');
  // The KB the agent gets: HEAD exported once, copied into each project.
  const kbExport = join(WORK, `kb-${sha.slice(0, 12)}`);
  if (!existsSync(join(kbExport, 'AGENTS.md'))) {
    rmSync(kbExport, { recursive: true, force: true });
    mkdirSync(kbExport, { recursive: true });
    execFileSync('sh', ['-c', `git -C "$0" archive HEAD | tar -x -C "$1"`, AKB_ROOT, kbExport]);
  }
  ctx.kbExport = kbExport;
  ctx.kb = { sha, claude: sh(claudeBin, ['--version']).split(' ')[0] };
  ctx.template = readFileSync(join(ACD, 'Projects', '_makefiles', 'Makefile'), 'utf8');
  eprint(`AKB ${sha.slice(0, 7)}; Claude Code ${ctx.kb.claude}; ApolloCrossDev ${ACD}`);
}

async function loadCases(ctx) {
  await prepare(ctx);
  const file = join(TASKS_REPO, 'coding-agent', 'tasks.yaml');
  const json = sh('python3', ['-E', '-c',
    'import json,sys,yaml; print(json.dumps(yaml.safe_load(open(sys.argv[1], encoding="utf-8"))))', file]);
  let tasks = JSON.parse(json);
  ctx.tasksCommit = sh('git', ['-C', TASKS_REPO, 'rev-parse', '--short', 'HEAD']);
  if (!ctx.includeDrafts) tasks = tasks.filter(t => t.status === 'reviewed');
  if (ctx.only) {
    const want = new Set(ctx.only.split(','));
    const unknown = [...want].filter(id => !tasks.some(t => t.id === id));
    if (unknown.length) throw new Error(`--only: no such task (or not reviewed): ${unknown.join(', ')}`);
    tasks = tasks.filter(t => want.has(t.id));
  }
  if (!tasks.length) throw new Error('no tasks to run (only reviewed tasks count; --include-drafts runs drafts)');
  for (const t of tasks)
    if (!existsSync(join(TASKS_REPO, 'coding-agent', 'start', t.start))) throw new Error(`${t.id}: no start/${t.start}`);
  for (const t of tasks) for (const ch of t.checks || []) {
    if ((ch.expect == null) === (ch.expect_not == null) || (ch.file == null) === (ch.asm == null))
      throw new Error(`${t.id}: a check needs one of file/asm and one of expect/expect_not`);
    try { checkRe(ch); } catch (e) { throw new Error(`${t.id}: ${e.message}`); }
  }
  return tasks.map(t => ({
    id: t.id, prompt: t.prompt.trim(), tags: [...t.tags, ...(t.status === 'reviewed' ? [] : ['draft'])],
    task: t, meta: { tasks_commit: ctx.tasksCommit, akb_sha: ctx.kb.sha.slice(0, 7), claude_code: ctx.kb.claude, based_on: t.based_on },
  }));
}

// --- the project the agent starts in -----------------------------------------

function makefile(ctx) {
  // As the apollo-new-project skill sets it up: the name, and the NDK 3.9 headers.
  return ctx.template
    .replace(/^PROJECT_NAME\t= <project-name>$/m, 'PROJECT_NAME\t= evalapp')
    .replace(/^# C_INCL_NDK  = \$\(PREFIX\)\/\$\(TARGET\)\/ndk39-include\n/m, '')
    .replace(/^C_INCL_NDK  = .*ndk32.*$/m, 'C_INCL_NDK  = $(PREFIX)/$(TARGET)/ndk39-include');
}

function agentsMd(t, withKb) {
  const takeover = t.mode === 'os-takeover';
  const kind = takeover ? 'game' : 'tool';
  const repo = [
    '## This repository', '',
    `- **What it is:** a small ${kind} for the Apollo V4 (an evaluation project)`,
    `- **Kind:** ${kind}`,
    '- **Target core:** the latest core release',
    '- **Target model:** any V4 model',
    '- **Target OS:** ApolloOS R10, AmigaOS 3.9, AmigaOS 3.2',
    `- **Execution mode:** ${t.mode}`,
    '- **Languages:** C, 68080 assembly', '',
  ];
  const build = [
    '## Build and test', '',
    'ApolloCrossDev is installed and `APOLLOCROSSDEV` is set. Build with:', '',
    '```sh', 'make', '```', '',
    'There is no V4 attached: you can build, but not run the program.',
    'Build and fix all errors and warnings before presenting code.', '',
  ];
  if (!withKb) return ['# AGENTS.md: evalapp', '', ...repo, ...build].join('\n');
  return ['# AGENTS.md: evalapp', '',
    '## Read first', '',
    'This repository targets the Apollo V4 platform. Before doing anything else,',
    'read `ApolloKnowledgeBase/AGENTS.md` and follow it. It explains the platform,',
    'the assumptions you must not make, and which knowledge base files to read for',
    'your task. Paths in that file are relative to `ApolloKnowledgeBase/`.', '',
    ...repo,
    '## Relevant knowledge base areas', '',
    '- `ApolloKnowledgeBase/toolchain/`',
    '- `ApolloKnowledgeBase/toolchain/apollolib/`',
    '- `ApolloKnowledgeBase/core/`',
    ...(takeover ? ['- `ApolloKnowledgeBase/os/os-takeover.md`'] : []), '',
    ...build].join('\n');
}

function setupProject(c, ctx, dir) {
  const t = c.task, withKb = ctx.variant !== 'baseline';
  rmSync(dir, { recursive: true, force: true });
  mkdirSync(dir, { recursive: true });
  cpSync(join(TASKS_REPO, 'coding-agent', 'start', t.start), dir, { recursive: true });
  writeFileSync(join(dir, 'Makefile'), makefile(ctx));
  writeFileSync(join(dir, 'AGENTS.md'), agentsMd(t, withKb) + '\n');
  writeFileSync(join(dir, 'CLAUDE.md'), withKb ? '@AGENTS.md\n@ApolloKnowledgeBase/AGENTS.md\n' : '@AGENTS.md\n');
  if (withKb) cpSync(ctx.kbExport, join(dir, 'ApolloKnowledgeBase'), { recursive: true });
}

// --- running Claude Code ------------------------------------------------------

const SHORT = 4000;   // tool results longer than this are cut in the trace
const cut = s => (s.length > SHORT ? s.slice(0, SHORT) + `\n[... ${s.length - SHORT} more characters]` : s);

// No peeking: the AKB clones, the tasks, the results, Claude's own memory, and
// the other condition's work folders (the v1 ones hold a copy of the KB).
function denyReads(ctx) {
  const h = homedir().replace(/^\//, '');
  const other = ctx.variant === 'baseline' ? ['kb-*', 'v*'] : ['baseline'];
  return [`//${h}/ApolloKnowledgeBase/**`, `//${h}/ApolloKnowledgeBase-*/**`, `//${h}/.claude/**`,
          // macOS: $TMPDIR is under /var, which is a link to /private/var; deny both spellings.
          ...[WORK, realpathSync(tmpdir()) + '/akb-evals-coding'].flatMap(w => other.map(d => `//${w.replace(/^\//, '')}/${d}/**`))]
    .map(p => `Read(${p})`);
}

function runAgent(c, ctx, proj, cfg, seconds) {
  const withKb = ctx.variant !== 'baseline';
  const args = ['-p', c.prompt, '--model', ctx.model,
    '--output-format', 'stream-json', '--verbose',
    '--permission-mode', 'acceptEdits', '--permission-prompts', 'none',
    '--allowedTools', 'Read,Glob,Grep,Edit,Write,Skill,Bash(make),Bash(make:*),Bash(m68k-amigaos-gcc:*),Bash(m68k-amigaos-objdump:*),Bash(vasmm68k_mot:*)',
    '--disallowedTools', ['WebFetch', 'WebSearch', ...denyReads(ctx)].join(','),
    '--append-system-prompt', NONINTERACTIVE,
    '--max-budget-usd', String(AGENT_BUDGET_USD),
    '--no-session-persistence', '--setting-sources', 'project',
    ...(withKb ? ['--plugin-dir', join(proj, 'ApolloKnowledgeBase')] : [])];
  const env = { PATH: `${ACD_BIN}:/usr/bin:/bin:/usr/sbin:/sbin`, HOME: homedir(), TMPDIR: tmpdir(),
    LANG: 'en_US.UTF-8', ANTHROPIC_API_KEY: apiKey, CLAUDE_CONFIG_DIR: cfg, APOLLOCROSSDEV: ACD,
    DISABLE_AUTOUPDATER: '1', CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: '1' };
  return new Promise((resolveP, reject) => {
    const p = spawn(claudeBin, args, { cwd: proj, env, stdio: ['ignore', 'pipe', 'pipe'] });
    let out = '', err = '';
    const killer = setTimeout(() => p.kill('SIGTERM'), seconds * 1000);
    p.stdout.on('data', d => { out += d; });
    p.stderr.on('data', d => { err += d; });
    p.on('error', reject);
    p.on('close', code => { clearTimeout(killer); resolveP({ code, out, err }); });
  });
}

async function runCase(c, ctx) {
  const id = pathSafeId(c.id) + '_rep' + c.rep;
  const base = join(WORK, ctx.variant, id);
  const proj = join(base, 'proj'), cfg = join(base, 'config');
  setupProject(c, ctx, proj);
  rmSync(cfg, { recursive: true, force: true }); mkdirSync(cfg, { recursive: true });
  // Leave the judge and the build some of the case's ceiling.
  const seconds = Math.max(120, (ctx.timeoutS || 3600) - 300);
  const { code, out, err } = await runAgent(c, ctx, proj, cfg, seconds);

  const transcript = [{ role: 'user', content: c.prompt }];
  let init = null, result = null, toolCalls = 0;
  for (const ln of out.split('\n')) {
    if (!ln.trim()) continue;
    let m; try { m = JSON.parse(ln); } catch { continue; }
    if (m.type === 'system' && m.subtype === 'init') init = m;
    else if (m.type === 'result') result = m;
    else if (m.type === 'assistant') for (const b of m.message?.content || []) {
      if (b.type === 'text') transcript.push({ role: 'assistant', content: b.text });
      else if (b.type === 'tool_use') { toolCalls++; transcript.push({ role: 'tool_call', name: b.name, content: JSON.stringify(b.input, null, 2) }); }
    }
    else if (m.type === 'user') for (const b of m.message?.content || []) {
      if (b.type === 'tool_result') {
        const txt = typeof b.content === 'string' ? b.content : (b.content || []).map(x => x.text || '').join('');
        transcript.push({ role: 'tool_result', content: cut(txt) });
      }
    }
  }
  if (!result) {
    const e = new Error(`claude exited ${code} without a result${err ? ': ' + err.slice(-300) : ''}`);
    e.failure_class = code === null || code === 143 ? 'timeout' : 'harness_or_serving';
    throw e;
  }
  // Usage of the main model; other models (small helper calls) are in perf.
  const mu = result.modelUsage || {};
  const main = mu[ctx.model] || Object.entries(mu).find(([k]) => k.startsWith(ctx.model))?.[1] || {};
  const usage = { input_tokens: main.inputTokens || 0, output_tokens: main.outputTokens || 0,
    cache_read_input_tokens: main.cacheReadInputTokens || 0, cache_creation_input_tokens: main.cacheCreationInputTokens || 0 };
  const output = String(result.result ?? '');
  const g = gradeBuild(c, proj);
  // Keep the finished project (without the KB copy and build output) next to the results.
  const keep = join(ctx.flowVdir, 'projects', id);
  rmSync(keep, { recursive: true, force: true });
  cpSync(proj, keep, { recursive: true, filter: s => !/\/(ApolloKnowledgeBase|\.apollolib)(\/|$)|\/evalapp$|\.o$/.test(s) });
  return {
    output, transcript, model: init?.model || ctx.model, usage,
    stop_reason: result.subtype === 'success' ? 'end_turn' : result.subtype,
    status: 'ok',   // an unfinished run is graded like any other: it fails on its result
    tool_calls: toolCalls, turns: result.num_turns, cost_usd: result.total_cost_usd,
    other_models: Object.keys(mu).filter(k => !k.startsWith(ctx.model)),
    build: g, files: projectFiles(proj),
  };
}

// --- grading ------------------------------------------------------------------

const TEXT_EXT = /\.(c|h|s|i|asm|txt|md)$|^Makefile$/;
function projectFiles(proj) {
  const files = {};
  const walk = (d, rel) => {
    for (const n of readdirSync(d)) {
      if (n === 'ApolloKnowledgeBase' || n.startsWith('.')) continue;
      const p = join(d, n), r = rel ? `${rel}/${n}` : n;
      const s = statSync(p);
      if (s.isDirectory()) walk(p, r);
      else if (TEXT_EXT.test(n) && !['AGENTS.md', 'CLAUDE.md'].includes(r) && s.size < 200_000) files[r] = readFileSync(p, 'utf8');
    }
  };
  walk(proj, '');
  return files;
}

// A check's pattern; a leading (?i) makes it case-insensitive.
function checkRe(ch) {
  const src = String(ch.expect ?? ch.expect_not);
  return src.startsWith('(?i)') ? new RegExp(src.slice(4), 'mi') : new RegExp(src, 'm');
}
const globRe = g => new RegExp('^' + g.replace(/[.+^${}()|[\]\\]/g, '\\$&').replace(/\*/g, '[^/]*') + '$');

function gradeBuild(c, proj) {
  const env = { ...process.env, APOLLOCROSSDEV: ACD, PATH: `${ACD_BIN}:${process.env.PATH}` };
  // The template sends compiler stdout to /dev/null; errors and warnings arrive on stderr.
  const r = spawnSync('make', [], { cwd: proj, env, encoding: 'utf8', timeout: 300_000 });
  const ok = r.status === 0 && existsSync(join(proj, 'evalapp'));
  const log = String(r.stderr || '') + (r.error ? String(r.error.message) : '');
  const warnings = log.split('\n').filter(l => /warning:/i.test(l));
  const files = projectFiles(proj);
  const results = [];
  for (const ch of c.task.checks || []) {
    const re = checkRe(ch);
    let pass;
    if (ch.asm) {
      const asm = emitAsm(proj, ch.asm, env);
      pass = asm != null && (ch.expect != null ? re.test(asm) : !re.test(asm));
    } else {
      const g = globRe(ch.file);
      const hit = Object.entries(files).some(([k, v]) => (g.test(k) || g.test(k.split('/').pop())) && re.test(v));
      pass = ch.expect != null ? hit : !hit;
    }
    results.push({ check: ch, pass });
  }
  return { ok, warnings, log: log.slice(-2000), checks: results };
}

/** The assembly GCC emits for one C file, with the compile command the project's Makefile uses. */
function emitAsm(proj, file, env) {
  try {
    const n = execFileSync('make', ['-n', '-B', 'build'], { cwd: proj, env, encoding: 'utf8', timeout: 60_000 });
    const esc = file.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const line = n.split('\n').find(l => / -c /.test(l) && new RegExp(`[ /]${esc}(\\s|$)`).test(l));
    if (!line) return null;
    const cmd = line.replace(/ -c /, ' -S ').replace(/ -o \S+\.o /, ' -o - ').replace(/>>\s*\/dev\/null\s*$/, '');
    return execFileSync('sh', ['-c', cmd], { cwd: proj, env, encoding: 'utf8', timeout: 60_000 });
  } catch { return null; }
}

const JUDGE_SYSTEM = `You grade code written by an AI coding agent for the Apollo V4 (68080 CPU, SAGA chipset, ApolloOS and AmigaOS, the ApolloCrossDev toolchain). The maintainers of the Apollo knowledge base wrote a checklist for each task. The checklist is the reference: don't use your own knowledge of the 68080, the Amiga or GCC to decide what is true.

You get the task, the project's files after the agent finished (sources, Makefile) and the agent's final message to the developer. A fact about the code counts only when the code does it; a fact about what the agent tells the developer counts when the final message or a comment in the code says it.

For each required fact, decide whether it holds. A fact with several parts counts only when every part holds. Parts introduced with "for example", "such as" or "e.g." are illustrations. When a fact offers alternatives ("or"), one of them is enough.

For each wrong item, decide whether the code or the message does or claims it. Mentioning it in order to reject it does not count.

Give short evidence for every decision: a file name and a quote of at most 25 words, or "not found".`;

const JUDGE_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['facts', 'wrong'],
  properties: {
    facts: { type: 'array', items: { type: 'object', additionalProperties: false, required: ['n', 'present', 'evidence'],
      properties: { n: { type: 'integer' }, present: { type: 'boolean' }, evidence: { type: 'string' } } } },
    wrong: { type: 'array', items: { type: 'object', additionalProperties: false, required: ['n', 'made', 'evidence'],
      properties: { n: { type: 'integer' }, made: { type: 'boolean' }, evidence: { type: 'string' } } } },
  },
};

async function gradeCase(c, run, ref, ctx) {
  const t = c.task, wrong = t.wrong || [];
  const list = (xs) => xs.length ? xs.map((x, i) => `${i + 1}. ${x}`).join('\n') : '(none)';
  const files = Object.entries(run.files).map(([k, v]) => `<file name="${k}">\n${v}\n</file>`).join('\n\n') || '(no files)';
  const msg = await client.messages.create({
    model: JUDGE_MODEL, max_tokens: 8000,
    system: JUDGE_SYSTEM,
    output_config: { format: { type: 'json_schema', schema: JUDGE_SCHEMA } },
    messages: [{ role: 'user', content:
      `<task>\n${c.prompt}\n</task>\n\n<project_files>\n${files}\n</project_files>\n\n<final_message>\n${run.output}\n</final_message>\n\n` +
      `<required_facts>\n${list(t.facts)}\n</required_facts>\n\n<wrong_items>\n${list(wrong)}\n</wrong_items>\n\n` +
      `Return one entry per required fact and one per wrong item, numbered as above.` }],
  });
  const judge = { judge_model: msg.model, judge_usage: msg.usage };
  const fail = (why) => Object.assign(new Error(`judge: ${why}`), { failure_class: 'grader_error', ...judge });
  if (msg.stop_reason !== 'end_turn') throw fail(`stop_reason ${msg.stop_reason}`);
  let j;
  try { j = JSON.parse(msg.content.filter(b => b.type === 'text').map(b => b.text).join('')); }
  catch { throw fail('output is not JSON'); }
  const byN = (xs, n) => xs.find(x => x.n === n);
  const facts = t.facts.map((f, i) => byN(j.facts, i + 1));
  const made = wrong.map((w, i) => byN(j.wrong, i + 1));
  if (facts.some(x => !x) || made.some(x => !x)) throw fail('missing checklist entries');
  const found = facts.filter(x => x.present).length;
  const madeN = made.filter(x => x.made).length;
  const b = run.build;
  const build = b.ok && b.warnings.length === 0 ? 1 : 0;
  const checks = b.checks.every(x => x.pass) ? 1 : 0;
  const g = { pass: build && checks && found === facts.length && madeN === 0 ? 1 : 0,
              build, checks, facts: found / facts.length, no_wrong: madeN === 0 ? 1 : 0 };
  const missing = t.facts.filter((_, i) => !facts[i].present);
  const madeList = wrong.filter((_, i) => made[i].made);
  const descr = ch => `${ch.asm ? `asm of ${ch.asm}` : ch.file} ${ch.expect != null ? 'has' : 'lacks'} /${ch.expect ?? ch.expect_not}/`;
  return {
    grade: g, ...judge,
    explanation: {
      pass: g.pass ? 'Builds cleanly, checks pass, all facts, no wrong items.' :
        [!b.ok ? 'Build failed' : '', b.warnings.length ? `${b.warnings.length} warning(s)` : '',
         b.checks.filter(x => !x.pass).map(x => `Check failed: ${descr(x.check)}`).join(' | '),
         missing.length ? `Missing: ${missing.join(' | ')}` : '', madeList.length ? `Wrong: ${madeList.join(' | ')}` : ''].filter(Boolean).join('\n'),
      build: b.ok ? (b.warnings.length ? b.warnings.slice(0, 10).join('\n') : 'Built without warnings.') : `Build failed:\n${b.log}`,
      checks: b.checks.length ? b.checks.map(x => `${x.pass ? '✓' : '✗'} ${descr(x.check)}`).join('\n') : '(no checks)',
      facts: t.facts.map((f, i) => `${facts[i].present ? '✓' : '✗'} ${f} — ${facts[i].evidence}`).join('\n'),
      no_wrong: wrong.length ? wrong.map((w, i) => `${made[i].made ? '✗ made' : '✓ not made'}: ${w} — ${made[i].evidence}`).join('\n') : '(no wrong items listed)',
    },
  };
}

/** Side-channel perf fields beyond the built-ins (latency_s etc.). */
function perfFrom(run) {
  return { tool_calls: run.tool_calls, turns: run.turns, cost_usd: run.cost_usd,
           ...(run.other_models?.length ? { other_models: run.other_models } : {}) };
}


// --- harness (you usually won't need to touch below this line) --------------

function parseArgs(argv) {
  const a = { flow: join(AKB_ROOT, 'build', 'evals', 'coding-agent'), variant: 'baseline',
              model: 'claude-opus-5-5', reps: 1, concurrency: 2, timeoutS: 2700,
              approveHarness: false, only: null, includeDrafts: false, dryRun: false };
  // A flag at the end of argv would otherwise consume undefined - which for
  // --model equals the default and silently disables the served-model check.
  const val = (i) => { if (argv[i] === undefined) { eprint(`missing value for ${argv[i - 1]}`); usage(); process.exit(2); } return argv[i]; };
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i];
    if (k === '--flow') a.flow = val(++i);
    else if (k === '--variant') a.variant = val(++i);
    else if (k === '--model') a.model = val(++i);
    else if (k === '--reps') a.reps = +val(++i);
    else if (k === '--concurrency') a.concurrency = +val(++i);
    else if (k === '--timeout-s') a.timeoutS = +val(++i);
    else if (k === '--approve-harness') a.approveHarness = true;
    else if (k === '--only') a.only = val(++i);
    else if (k === '--include-drafts') a.includeDrafts = true;
    else if (k === '--dry-run') a.dryRun = true;
    else if (k === '-h' || k === '--help') { usage(); process.exit(0); }
    else { eprint(`unknown argument: ${k}`); usage(); process.exit(2); }
  }
  if (!/^(baseline|v[1-9]\d*)$/.test(a.variant)) {
    // The report only reads directories named 'baseline' or 'v<N>' - any other
    // name runs to completion but spends the pass into a directory the Summary,
    // trajectory, and budget arithmetic never see.
    eprint(`--variant must be 'baseline' or 'v<N>', got '${a.variant}'`);
    usage(); process.exit(2);
  }
  if (!Number.isFinite(a.timeoutS) || a.timeoutS < 0
      || a.timeoutS * 1000 > 2147483647 // setTimeout clamps >2^31-1 ms to 1 ms - the ceiling would fire instantly
      || !Number.isInteger(a.reps) || a.reps < 1
      || !Number.isInteger(a.concurrency) || a.concurrency < 1) { usage(); process.exit(2); }
  return a;
}
function usage() {
  eprint('usage: node evals/coding-agent.mjs --variant baseline|v<N> [--only id,id] [--include-drafts] [--dry-run] [--flow DIR] [--model ID] [--reps N] [--concurrency N] [--timeout-s N (0 = no ceiling)] [--approve-harness]');
}

// Harness integrity gate. The hillclimb loop gets this runner command
// allowlisted for the session and then runs rounds unattended, while the
// per-round change (proposed by an analyzer fed untrusted transcripts) may
// legitimately edit harness code. Without this gate a round that rewrites the
// runner would execute attacker-chosen code on the next unattended run under
// the user's one-time approval. So: sha256 over this file, any lockfile
// beside it or in the directory the runner is invoked from (dependency drift
// is harness drift too; with neither, a note says so), plus
// every path in `_state.json.harness_paths` (relative to the directory the
// runner is invoked from, i.e. the repo root); compare to
// `_state.json.harness_sha`; refuse on absent/mismatch unless a human passes
// --approve-harness, which records the new sha. That write is the one
// sanctioned exception to "never write _state.json".
//
// Scope, stated plainly: this is a change detector, not a security boundary.
// The sha, the path list and this file all live where the loop agent can
// write, so an agent that is already prompt-injected can forge the record or
// pass --approve-harness itself. What it catches is the common case - a
// round's harness edit reaching an unattended run unreviewed - and what
// actually bounds an unattended run is the permission allowlist the user
// grants the runner command (scope it to this exact command line, not a
// prefix). Installed dependencies beyond the lockfile are outside the digest.
function checkHarness(statePath, st, approve) {
  const self = fileURLToPath(import.meta.url);
  const listed = Array.isArray(st.harness_paths) ? st.harness_paths.map(String) : [];
  const lockfiles = [...new Set([dirname(self), process.cwd()].flatMap(d =>
    ['package-lock.json', 'bun.lock', 'bun.lockb', 'yarn.lock', 'pnpm-lock.yaml'].map(f => join(d, f))))]
    .filter(f => existsSync(f));
  const paths = [...new Set([self, ...lockfiles, ...listed.map(p => resolve(p))])].sort();
  const h = createHash('sha256');
  const hashed = [];
  for (const p of paths) {
    let buf;
    try { buf = readFileSync(p); }
    catch (e) {
      if (p === self) throw e;
      eprint(`warning: harness path '${relative(process.cwd(), p)}' not readable (${e?.code || 'error'}) - skipped`);
      continue;
    }
    h.update(relative(process.cwd(), p)).update('\0').update(buf).update('\0');
    hashed.push(relative(process.cwd(), p));
  }
  const sha = h.digest('hex');
  if (st.harness_sha === sha) return;
  // Said only here, where a person is about to approve or is being refused.
  if (!lockfiles.length) eprint('note: no lockfile beside the runner or in the current directory - dependency changes are outside the harness sha');
  if (approve) {
    st.harness_sha = sha;
    writeFileNoFollow(statePath, JSON.stringify(st, null, 2) + '\n');
    eprint(`harness approved: sha256 ${sha.slice(0, 12)} over ${hashed.length} file(s) recorded in ${statePath}`);
    return;
  }
  if (st.harness_sha == null) {
    eprint(`no approved harness sha in ${statePath} (computed ${sha.slice(0, 12)} over: ${hashed.join(', ')}).`);
    eprint('Review the harness, then run once with --approve-harness to record it.');
  } else {
    eprint(`harness changed since last approved run (files: ${hashed.join(', ')}); `
      + `approved ${String(st.harness_sha).slice(0, 12)}, now ${sha.slice(0, 12)}.`);
    eprint('Re-run with --approve-harness after reviewing the diff.');
  }
  process.exit(2);
}

// Transient provider errors (429 / overloaded / 5xx) retry with jittered
// exponential backoff - a zero-delay retry loop multiplies cost invisibly
// under rate limits and can turn one transient 429 into a torn-down batch.
// The attempt count lands in the row's meta (or the errors sidecar) so retry
// churn is visible in the data, not just the bill.
async function withBackoff(fn, retry, deadline = Infinity, tries = 5) {
  for (let attempt = 0; ; attempt++) {
    // Checked before every attempt, not just before sleeps: once the case's
    // ceiling has passed, an abandoned chain must not issue another call
    // (e.g. a judge call after the app call consumed the whole ceiling).
    if (Date.now() >= deadline) {
      const e = new Error('wall-clock ceiling exceeded before attempt');
      e.failure_class = 'timeout';
      throw e;
    }
    try { return await fn(); } catch (e) {
      const status = e?.status ?? e?.response?.status;
      const transient = status === 429 || status === 529 || (status >= 500 && status < 600)
        || /overloaded|rate.?limit/i.test(String(e?.message ?? ''));
      if (!transient || attempt >= tries - 1) throw e;
      const delay = Math.min(60_000, 1000 * 2 ** attempt) * (0.5 + Math.random());
      // Never start a retry that would outlive the case's wall-clock ceiling - 
      // otherwise an abandoned chain keeps issuing API calls after the case failed.
      if (Date.now() + delay >= deadline) throw e;
      retry.count++;
      await new Promise(r => setTimeout(r, delay));
    }
  }
}

// Hard per-case wall-clock ceiling, independent of stream liveness - a hung
// SSE stream can emit keepalives forever, defeating inactivity-based timers.
// The underlying call may keep running; the case fails and the slot is freed.
function withTimeout(promise, seconds, label) {
  if (!(seconds > 0)) return promise;
  let timer;
  const ceiling = new Promise((_, reject) => {
    timer = setTimeout(() => {
      const e = new Error(`${label}: exceeded ${seconds}s wall-clock ceiling`);
      e.failure_class = 'timeout';
      reject(e);
    }, seconds * 1000);
  });
  return Promise.race([promise, ceiling]).finally(() => clearTimeout(timer));
}

// Case ids appear in file paths AND as the row/file join key the report uses,
// so rows, trace filenames, and frozen refs all carry the same path-safe id.
// When sanitization changes the id, a short content hash keeps distinct ids
// distinct ('case/1' vs 'case_1'); the original rides in meta.original_id.
function pathSafeId(id) {
  const raw = String(id);
  const cleaned = raw.replace(/[^\w.-]/g, '_');
  // Idempotent by construction: anything already path-safe and within the
  // length bound - including this function's own truncated+suffixed output - 
  // passes through unchanged. Long ids (URLs, prompt text as id) truncate to
  // 120 chars plus an 8-hex hash of the full original, so they fail here, not
  // at the trace write after the spend, and distinct ids stay distinct.
  if (cleaned === raw && raw.length <= 129) return raw;
  return `${cleaned.slice(0, 120)}-${createHash('sha256').update(raw).digest('hex').slice(0, 8)}`;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  // lstat("link/") follows the final symlink, so a trailing separator on
  // --flow would blind every leaf isSymlink check below - strip it first.
  // Only Windows treats `\` as a separator; on POSIX it is a filename byte, so
  // splitting on it would walk prefixes that are not real path components.
  args.flow = args.flow.replace(WIN ? /(.)[\\/]+$/ : /(.)\/+$/, '$1');
  const flowSegments = args.flow.split(WIN ? /[\\/]/ : '/');
  // A `.`/`..` segment (e.g. a trailing `/.`) makes isSymlink(args.flow) below
  // resolve a different final component than the named dir - following a
  // planted link at the flow root - while join() collapses it and the absolute
  // branch skips the ancestor walk. Refuse dot segments outright
  // (absolute --flow stays supported).
  if (flowSegments.some(seg => seg === '.' || seg === '..')) {
    eprint(`refusing to run: --flow must not contain '.' or '..' segments, got '${args.flow}'`);
    process.exit(2);
  }
  const vdir = join(args.flow, args.variant);
  // Preflight every output path before the first model call: a planted
  // symlink would otherwise fail each case after its (billed) run.
  for (const p of [args.flow, join(args.flow, 'baseline'), vdir, join(vdir, 'traces'),
                   join(vdir, 'results.jsonl'), join(vdir, 'errors.jsonl'),
                   join(vdir, 'progress.txt'), join(args.flow, 'baseline', 'ref'), join(args.flow, '_state.json')])
    if (isSymlink(p)) { eprint(`refusing to run: ${p} is a symlink (the flow dir must hold regular files)`); process.exit(2); }
  // A relative --flow (the documented `.claude/hillclimb/<name>` layout) is
  // also lstat-walked component by component from the cwd: a pre-planted
  // link at an ancestor (`.claude/hillclimb -> elsewhere`) would otherwise
  // relocate the root capture below - the containment anchor itself - to the
  // attacker's target. An absolute --flow is the caller's own trust decision
  // and is not walked (an absolute ancestor link can be legitimate: /tmp on
  // macOS).
  if (!isAbsolute(args.flow)) {
    let walk = '';
    for (const part of flowSegments.filter(Boolean).slice(0, -1)) {
      walk = walk ? join(walk, part) : part;
      if (isSymlink(walk)) { eprint(`refusing to run: ${walk} is a symlink (ancestor of --flow)`); process.exit(2); }
    }
  }
  // Every later open/mkdir is bound to this resolved root (see assertInFlow):
  // create the flow dir when fresh (the preflight above refused a link at it
  // and, for a relative path, at every ancestor), then capture where it
  // really resolves.
  mkdirSync(args.flow, { recursive: true });
  flowRealRoot = realpathSync(args.flow);
  mkdirNoFollow(join(vdir, 'traces'));
  // _state.json is READ-ONLY here. The orchestrator owns it. Absent is fine
  // (a baseline-only run has no loop state yet), but present-and-unparsable
  // must not let the id-space gate below pass vacuously over a corrupt file.
  const statePath = join(args.flow, '_state.json');
  let st = {};
  // Read through the no-follow opener like every other flow-dir file; the
  // parse message is not echoed (it can quote the file's first bytes).
  const stateText = readIfPresent(statePath);
  if (stateText != null) {
    try { st = JSON.parse(stateText) || {}; }
    catch { eprint(`${statePath} exists but is not valid JSON - fix it before spending a pass`); process.exit(2); }
  }
  // --dry-run makes no API calls, so it may run before the harness is approved
  if (!args.dryRun) checkHarness(statePath, st, args.approveHarness);
  const ctx = { ...args, state: st, flowVdir: vdir };

  // Resume: which (id, rep) pairs already have a row?
  const resultsPath = join(vdir, 'results.jsonl');
  const done = new Set();
  for (const ln of (readIfPresent(resultsPath) ?? '').split('\n')) {
    if (!ln.trim()) continue;
    try { const r = JSON.parse(ln); done.add(`${r.prompt_id}\0${r.rep}`); } catch {}
  }
  // Rows key on the path-safe id (see pathSafeId), so resume must too.

  const cases = await loadCases(ctx);
  // Validate the id space before spending anything: duplicate path-safe ids - 
  // including case-insensitive twins, which macOS/Windows filesystems collapse - 
  // would silently overwrite traces and frozen refs; and a _state.json split id
  // that matches no case would silently shrink the scored denominator.
  const seen = new Map();
  for (const c of cases) {
    const k = pathSafeId(c.id).toLowerCase();
    if (seen.has(k)) {
      eprint(`duplicate case id after sanitization: '${c.id}' collides with '${seen.get(k)}'`);
      process.exit(2);
    }
    seen.set(k, c.id);
  }
  const safeIds = new Set(cases.map(c => pathSafeId(c.id)));
  for (const k of ['train_ids', 'val_ids', 'test_ids'])
    if (st[k] != null && !Array.isArray(st[k])) { eprint(`_state.json ${k} must be a list of ids`); process.exit(2); }
  for (const sid of [...(st.train_ids ?? []), ...(st.val_ids ?? []), ...(st.test_ids ?? [])]) {
    const s = String(sid); // the adapter joins with String() on both sides - numeric ids are fine
    if (safeIds.has(s)) continue; // matches a loaded case - definitionally valid
    if (s !== pathSafeId(s)) {
      // Can never match a row: rows key on path-safe ids. This is the silent
      // shrunken-denominator bug - fail before anything is spent.
      eprint(`_state.json split id '${s}' is not a path-safe id - record split ids exactly as they appear in results.jsonl's prompt_id`);
      process.exit(2);
    }
    // Well-formed but absent is legitimate (a trimmed top-K subset run) - note it, don't fail.
    eprint(`note: split id '${s}' matches no loaded case (expected for a trimmed subset run)`);
  }
  const refDir = join(args.flow, 'baseline', 'ref');
  const tasks = [];
  for (const c of cases) for (let rep = 0; rep < args.reps; rep++) {
    if (done.has(`${pathSafeId(c.id)}\0${rep}`)) continue;
    tasks.push({ c, rep });
  }
  eprint(`[${args.variant}] ${tasks.length} of ${cases.length * args.reps} (id,rep) to run`);
  if (args.dryRun) {
    for (const { c, rep } of tasks) eprint(`  would run ${c.id} rep${rep} [${c.tags.join(', ')}]`);
    eprint('dry run: no API calls made');
    process.exit(0);
  }

  let i = 0, ok = 0, fail = 0;
  const errorsPath = join(vdir, 'errors.jsonl');
  // A hard crash (power loss, ENOSPC) can leave a torn final line with no
  // trailing newline; the next append would merge two rows into one permanently
  // unparseable line. Isolate any fragment before appending anything.
  for (const p of [resultsPath, errorsPath]) {
    const tail = readIfPresent(p);
    if (tail && !tail.endsWith('\n')) appendFileNoFollow(p, '\n');
  }
  async function worker() {
    while (i < tasks.length) {
      const { c, rep } = tasks[i++];
      const safeId = pathSafeId(c.id);
      const t0 = Date.now();
      let lastRun = null;    // survives into the catch - billed spend on a failed attempt
      let rowWritten = false; // set once the results row lands - the attempt is scored
      const deadline = args.timeoutS > 0 ? t0 + args.timeoutS * 1000 : Infinity;
      const appRetry = { count: 0 }, judgeRetry = { count: 0 };
      try {
        // One ceiling over the whole case - app call, identity check, and grading - 
        // so a hung judge stream can't hold the slot either.
        const { run, g, latency_s } = await withTimeout((async () => {
          let tAttempt = t0;
          const run = await withBackoff(() => { tAttempt = Date.now(); return runCase({ ...c, rep }, ctx); },
            appRetry, deadline, 1);   // never re-run a whole agent session
          lastRun = run;
          // latency_s = the final app attempt only; backoff sleeps, failed
          // attempts, and judge time are excluded (retry counts are in meta).
          const latency_s = (Date.now() - tAttempt) / 1000;
          // Serving identity: fail loudly when the response was served by a model
          // other than the one requested. Accept exact match or a documented
          // alias->snapshot resolution - 'foo-latest'/'foo-0'/'foo' served as
          // 'foo-20250101', 'foo@20250101', or 'foo-2025-01-01'. Anything else - 
          // another snapshot of the requested pin, a sibling model, or the bare
          // base id ('foo-latest' served as 'foo', an unversioned echo that can
          // hide snapshot drift across rounds) - fails the attempt. Non-Anthropic
          // id schemes (e.g. Bedrock's 'anthropic.claude-...-v1:0') need their own
          // rule here.
          if (ctx.model && run.model && run.model !== ctx.model) {
            const base = ctx.model.replace(/-latest$|-0$/, '');
            const rest = String(run.model).startsWith(base)
              ? String(run.model).slice(base.length) : null;
            if (!(rest != null && /^[-@](\d{8}|\d{4}-\d{2}-\d{2})$/.test(rest))) {
              const e = new Error(`served model ${run.model} != requested ${ctx.model}`);
              e.failure_class = 'serving_substitution';
              throw e;
            }
          }
          // Frozen pairwise reference (never regenerated): baseline/ref/<id>.*
          let ref = null;
          if (args.variant !== 'baseline') {
            const p = join(refDir, safeId);
            // A planted symlink throws (ELOOP) rather than feeding the judge
            // its target; the case then fails loudly instead of leaking.
            for (const ext of REF_EXTS) {
              try { ref = readFileNoFollow(p + ext); break; }
              catch (e) { if (e?.code !== 'ENOENT') throw e; }
            }
          }
          const g = await withBackoff(() => gradeCase(c, run, ref, ctx), judgeRetry, deadline);
          return { run, g, latency_s };
        })(), args.timeoutS, `${c.id} rep${rep}`);
        const row = {
          prompt_id: safeId, rep, prompt: c.prompt ?? c.input ?? c.id,
          tags: c.tags, attachments: c.attachments,
          meta: safeId !== String(c.id) || appRetry.count || judgeRetry.count
            ? { ...(c.meta ?? {}),
                ...(safeId !== String(c.id) ? { original_id: String(c.id) } : {}),
                ...(appRetry.count ? { retries: appRetry.count } : {}),
                ...(judgeRetry.count ? { judge_retries: judgeRetry.count } : {}) }
            : c.meta,
          model: run.model, usage: run.usage, stop_reason: run.stop_reason,
          // The report keys on `status`, not stop_reason: a clipped answer is
          // counted and shown but kept out of the means. runCase may set
          // run.status to override the max_tokens rule.
          status: run.status ?? (run.stop_reason === 'max_tokens' ? 'truncated' : 'ok'),
          judge_model: g.judge_model ?? run.judge_model,
          judge_usage: g.judge_usage ?? run.judge_usage,
          latency_s, ...perfFrom(run),
          grade: g.grade, explanation: g.explanation,
        };
        appendFileNoFollow(resultsPath, JSON.stringify(row) + '\n');
        rowWritten = true; // past this point the attempt is scored - a later throw (trace write, ref freeze) must not also append an error row
        if (run.transcript)
          writeFileNoFollow(join(vdir, 'traces', `${safeId}_rep${rep}.json`),
            JSON.stringify(run.transcript, null, 2));
        // For pairwise: on the baseline run, freeze the reference output once.
        if (args.variant === 'baseline' && run.output != null
            && !REF_EXTS.some(ext => lexists(join(refDir, safeId) + ext))) {
          mkdirNoFollow(refDir);
          writeFileNoFollow(join(refDir, safeId),
            typeof run.output === 'string' ? run.output : JSON.stringify(run.output));
        }
        ok++;
      } catch (e) {
        fail++;
        if (rowWritten) {
          // The attempt scored; only a post-row write (trace, ref) failed. An error
          // row here would double-count the billed usage under the budget rule.
          eprint(`  [${args.variant}] ${c.id} rep${rep} scored, but a post-row write failed: ${e?.message || e}`);
          continue;
        }
        // Failed attempts are data too - but they must not occupy the (case, rep)
        // slot in results.jsonl, or resume would never re-run them.
        appendFileNoFollow(errorsPath, JSON.stringify({
          prompt_id: safeId, rep,
          ...(safeId !== String(c.id) ? { original_id: String(c.id) } : {}),
          failure_class: e?.failure_class ?? 'error',
          error: String(e?.message || e),
          retries: appRetry.count, judge_retries: judgeRetry.count,
          // Billed-but-failed spend stays countable: when the app call completed
          // before the failure (e.g. a served-model mismatch, a judge-stage
          // ceiling), carry its identity and usage on the error row.
          model: lastRun?.model, usage: lastRun?.usage,
          judge_model: e?.judge_model ?? lastRun?.judge_model,
          judge_usage: e?.judge_usage ?? lastRun?.judge_usage,
          latency_s: (Date.now() - t0) / 1000,
        }) + '\n');
        eprint(`  [${args.variant}] ${c.id} rep${rep} FAILED: ${e?.message || e}`);
      }
    }
  }
  // One progress line every 30s (and to <vdir>/progress.txt) so "how far along
  // is it?" is answerable from the background shell's output or one file read,
  // without the orchestrator parsing results.jsonl mid-write. ETA is a plain
  // rate extrapolation from this pass.
  const t0 = Date.now();
  const progress = () => {
    const done = ok + fail, total = tasks.length;
    const el = (Date.now() - t0) / 1000;
    const eta = done ? Math.round((el / done) * (total - done)) : null;
    const line = `[${args.variant}] ${done}/${total} done (${ok} ok, ${fail} failed), `
      + `${Math.round(el)}s elapsed` + (eta != null ? `, ~${eta}s left` : '');
    eprint(line);
    try { writeFileNoFollow(join(vdir, 'progress.txt'), line + '\n'); } catch {}
  };
  const tick = setInterval(progress, 30_000);
  workersStarted = true;
  await Promise.all(Array.from({ length: Math.max(1, args.concurrency) }, worker));
  clearInterval(tick); progress();
  eprint(`[${args.variant}] done - ${ok} ok, ${fail} failed -> ${resultsPath}`);
  process.exit(fail ? 1 : 0);
}

// Anything main() throws prints as one sanitized line, not a raw stack. Before
// the workers start it is a refusal (a planted link at _state.json or
// results.jsonl, an lstat that fails, an error from loadCases) and exits 2 like
// the preflight refusals. After they start, only a failed errors.jsonl append
// gets here; rows may already be on disk, so say that and exit 1.
let workersStarted = false;
main().catch(e => {
  const m = String(e?.message || e);
  if (workersStarted) { eprint('stopped mid-run (rows already written are kept; re-run to resume): ' + m); process.exit(1); }
  eprint(m.startsWith('refusing to ') ? m : 'refusing to run: ' + m);
  process.exit(2);
});
