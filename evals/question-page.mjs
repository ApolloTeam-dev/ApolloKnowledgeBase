#!/usr/bin/env node
// question-page.mjs - the question-page benchmark eval of ApolloKnowledgeBase
// (step 5). The eval itself is the section "the question-page eval" below;
// the rest is the build-eval runner scaffold of the claude-api skill.
//
//   node evals/question-page.mjs --variant baseline|v1 [--only id,id] [--include-drafts]
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

// --- the question-page eval (AKB step 5) -------------------------------------
//
// Runs the tasks of ApolloKnowledgeBase-Tasks/question-page/tasks.yaml against
// Opus 5.5 in two conditions, one per variant directory:
//
//   baseline   without the knowledge base: the question alone, with a short
//              system prompt that names the platform and asks the model not
//              to invent facts (so "I don't know" is possible in both)
//   v1 (v<N>)  with the knowledge base: the real question page, ask() from
//              ApolloKnowledgeBase-Manager src/ask.js, bundled with a corpus
//              built from this AKB checkout at HEAD
//
// Sonnet 5.5 grades each answer against the task's checklist (facts that must
// be in it, wrong claims that must not), with structured output.
//
//   node evals/question-page.mjs --variant baseline [--only id,id] [--include-drafts]
//   node evals/question-page.mjs --variant v1       [--only id,id] [--include-drafts]
//
// Environment:
//   AKB_TASKS     the ApolloKnowledgeBase-Tasks clone (default ~/ApolloKnowledgeBase-Tasks)
//   AKB_MANAGER   the ApolloKnowledgeBase-Manager clone, with npm ci done
//                 (default ~/ApolloKnowledgeBase-Manager)
// The API key comes from the macOS Keychain (service akb-evals-anthropic).
// Results go to build/evals/question-page/<variant>/ (git-ignored: the
// answers reveal the private tasks; never commit them).

import { execFileSync } from 'node:child_process';
import { homedir } from 'node:os';

const AKB_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const TASKS_REPO = process.env.AKB_TASKS || join(homedir(), 'ApolloKnowledgeBase-Tasks');
const MANAGER = process.env.AKB_MANAGER || join(homedir(), 'ApolloKnowledgeBase-Manager');
const JUDGE_MODEL = 'claude-sonnet-5-5';
const EFFORT = 'medium';            // the question page's EFFORT in wrangler.toml

const BASELINE_SYSTEM = `You answer questions from Apollo V4 developers. Apollo V4 is a hardware platform built around the 68080 CPU (a successor of the Motorola 68000 family, with the AMMX SIMD extension) and the SAGA chipset; it runs ApolloOS, AmigaOS 3.9 and AmigaOS 3.2, and is programmed with the ApolloCrossDev toolchain (a patched GCC 6.5 and vasm).

- Never invent register addresses, bit meanings, function signatures, instruction timings or compiler flags. If you don't know, say so.
- Write in the language of the question. Use Markdown. Be concise: answer the question, then stop.`;

let M = null;        // the bundled ask.js: { ask, kbInfo, Anthropic }
let client = null;   // for the baseline and the judge
let apiKey = null;

function sh(cmd, args, opts = {}) {
  return execFileSync(cmd, args, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], ...opts }).trim();
}

/** Build the corpus from this checkout, bundle ask.js with it, load it. */
async function prepare(ctx) {
  apiKey = sh('security', ['find-generic-password', '-s', 'akb-evals-anthropic', '-w']);
  if (!apiKey) throw new Error('no API key in the Keychain (service akb-evals-anthropic)');
  const sha = sh('git', ['-C', AKB_ROOT, 'rev-parse', 'HEAD']);
  if (sh('git', ['-C', AKB_ROOT, 'status', '--porcelain', '--untracked-files=no']))
    eprint('note: the AKB checkout has uncommitted changes; the corpus is built from the files on disk');
  if (!existsSync(join(MANAGER, 'node_modules', '.bin', 'esbuild')))
    throw new Error(`${MANAGER}: run npm ci there first`);
  sh('node', ['tools/build-corpus.mjs', AKB_ROOT, sha], { cwd: MANAGER });
  const out = join(AKB_ROOT, 'build', 'evals', 'ask-bundle.mjs');
  mkdirSync(dirname(out), { recursive: true });
  execFileSync(join(MANAGER, 'node_modules', '.bin', 'esbuild'),
    ['--bundle', '--platform=node', '--format=esm', '--log-level=warning', `--outfile=${out}`],
    { cwd: join(MANAGER, 'src'), stdio: ['pipe', 'inherit', 'inherit'],
      input: 'export { ask, kbInfo } from "./ask.js";\nexport { default as Anthropic } from "@anthropic-ai/sdk";\n' });
  M = await import(out + `?t=${Date.now()}`);
  client = new M.Anthropic({ apiKey });
  const kb = M.kbInfo();
  ctx.kb = { sha: kb.sha, files: kb.files, manager: sh('git', ['-C', MANAGER, 'rev-parse', '--short', 'HEAD']) };
  eprint(`corpus: AKB ${kb.sha.slice(0, 7)}, ${kb.files} files; ask.js from Manager ${ctx.kb.manager}`);
}

/** The tasks: reviewed ones only, unless --include-drafts. */
async function loadCases(ctx) {
  await prepare(ctx);
  const file = join(TASKS_REPO, 'question-page', 'tasks.yaml');
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
  return tasks.map(t => ({
    id: t.id, prompt: t.question.trim(), tags: [...t.tags, ...(t.status === 'reviewed' ? [] : ['draft'])],
    task: t, meta: { tasks_commit: ctx.tasksCommit, akb_sha: ctx.kb.sha.slice(0, 7), based_on: t.based_on },
  }));
}

const toUsage = (u) => ({ input_tokens: u.input || 0, output_tokens: u.output || 0,
  cache_read_input_tokens: u.cached || 0, cache_creation_input_tokens: u.cache_write || 0 });

/** With the KB: the real ask() entry point, its NDJSON stream read to the end. */
async function runWithKb(c, ctx) {
  const env = { ANTHROPIC_API_KEY: apiKey, MODEL: ctx.model, EFFORT };
  const req = new Request('https://apolloknowledgebase.com/api/ask', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question: c.prompt }) });
  const res = await M.ask(req, env, { login: 'akb-eval' }, async () => 999);
  const transcript = [{ role: 'system', content: `(the question page's system prompt: ask.js from Manager ${ctx.kb.manager}, AKB ${ctx.kb.sha.slice(0, 7)})` },
                      { role: 'user', content: c.prompt }];
  let text = '', done = null, error = null, toolCalls = 0;
  const sources = [];
  const reader = res.body.getReader(); const dec = new TextDecoder(); let buf = '';
  const handle = (ln) => {
    if (!ln.trim()) return;
    const m = JSON.parse(ln);
    if (m.t === 'text') text += m.d;
    else if (m.t === 'discard') text = '';
    else if (m.t === 'status') {
      toolCalls++;
      const [, kind, arg] = m.text.match(/^(Searching|Reading): (.*)$/s) || [];
      transcript.push(kind
        ? { role: 'tool_call', name: kind === 'Searching' ? 'search_kb' : 'read_files', content: JSON.stringify(kind === 'Searching' ? { query: arg } : { path: arg }, null, 2) }
        : { role: 'tool_call', name: 'status', content: m.text });
    }
    else if (m.t === 'source') sources.push(m.path);
    else if (m.t === 'done') done = m;
    else if (m.t === 'error') error = m.text;
  };
  for (;;) {
    const { value, done: end } = await reader.read();
    if (end) break;
    buf += dec.decode(value, { stream: true });
    let i; while ((i = buf.indexOf('\n')) >= 0) { handle(buf.slice(0, i)); buf = buf.slice(i + 1); }
  }
  handle(buf);
  if (error || !done) {
    const e = new Error(`question page: ${error || 'stream ended without done'}`);
    const st = /\((\d{3})\)/.exec(error || '')?.[1];
    if (/^Too many questions/.test(error || '')) e.status = 429; else if (st) e.status = +st;
    e.failure_class = /declined/.test(error || '') ? 'refusal' : 'harness_or_serving';
    throw e;
  }
  const truncated = text.includes('*(The answer was cut off');
  transcript.push({ role: 'assistant', content: text });
  return { output: text, transcript, model: done.model, usage: toUsage(done.usage),
           stop_reason: truncated ? 'max_tokens' : 'end_turn', tool_calls: toolCalls, rounds: done.rounds, sources };
}

/** Without the KB: the same model and effort, the question alone. */
async function runWithoutKb(c, ctx) {
  const msg = await client.messages.stream({
    model: ctx.model, max_tokens: 32000, output_config: { effort: EFFORT },
    system: BASELINE_SYSTEM, messages: [{ role: 'user', content: c.prompt }],
  }).finalMessage();
  if (msg.stop_reason === 'refusal') { const e = new Error('refusal'); e.failure_class = 'refusal'; throw e; }
  const text = msg.content.filter(b => b.type === 'text').map(b => b.text).join('');
  const thinking = msg.content.filter(b => b.type === 'thinking').map(b => b.thinking).join('\n') || undefined;
  const u = msg.usage;
  return { output: text, model: msg.model, stop_reason: msg.stop_reason, tool_calls: 0,
    usage: { input_tokens: u.input_tokens, output_tokens: u.output_tokens,
             cache_read_input_tokens: u.cache_read_input_tokens || 0, cache_creation_input_tokens: u.cache_creation_input_tokens || 0 },
    transcript: [{ role: 'system', content: BASELINE_SYSTEM }, { role: 'user', content: c.prompt },
                 { role: 'assistant', content: text, ...(thinking ? { thinking } : {}) }] };
}

async function runCase(c, ctx) {
  return ctx.variant === 'baseline' ? runWithoutKb(c, ctx) : runWithKb(c, ctx);
}

const JUDGE_SYSTEM = `You grade answers to questions from Apollo V4 developers (68080 CPU, SAGA chipset, ApolloOS and AmigaOS, the ApolloCrossDev toolchain). The maintainers of the Apollo knowledge base wrote a checklist for each question. The checklist is the reference: don't use your own knowledge of the 68080, the Amiga or GCC to decide what is true.

For each required fact, decide whether the answer states it. The wording may differ; the meaning must be the same. A fact with several parts counts only when every part is there. A fact is not present when the answer only hints at it, gives it as one possibility among others, or contradicts it.

For each wrong claim, decide whether the answer makes it. Mentioning a claim in order to reject it is not making it.

Give short evidence for every decision: a quote from the answer of at most 25 words, or "not in the answer".`;

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
  const msg = await client.messages.create({
    model: JUDGE_MODEL, max_tokens: 8000,
    system: JUDGE_SYSTEM,
    output_config: { format: { type: 'json_schema', schema: JUDGE_SCHEMA } },
    messages: [{ role: 'user', content:
      `<question>\n${c.prompt}\n</question>\n\n<answer>\n${run.output}\n</answer>\n\n` +
      `<required_facts>\n${list(t.facts)}\n</required_facts>\n\n<wrong_claims>\n${list(wrong)}\n</wrong_claims>\n\n` +
      `Return one entry per required fact and one per wrong claim, numbered as above.` }],
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
  const g = { pass: found === facts.length && madeN === 0 ? 1 : 0, facts: found / facts.length, no_wrong: madeN === 0 ? 1 : 0 };
  const missing = t.facts.filter((_, i) => !facts[i].present);
  const madeList = wrong.filter((_, i) => made[i].made);
  return {
    grade: g, ...judge,
    explanation: {
      pass: g.pass ? 'All facts present, no wrong claims.' :
        [missing.length ? `Missing: ${missing.join(' | ')}` : '', madeList.length ? `Wrong: ${madeList.join(' | ')}` : ''].filter(Boolean).join('\n'),
      facts: t.facts.map((f, i) => `${facts[i].present ? '✓' : '✗'} ${f} — ${facts[i].evidence}`).join('\n'),
      no_wrong: wrong.length ? wrong.map((w, i) => `${made[i].made ? '✗ made' : '✓ not made'}: ${w} — ${made[i].evidence}`).join('\n') : '(no wrong claims listed)',
    },
  };
}

/** Side-channel perf fields beyond the built-ins (latency_s etc.). */
function perfFrom(run) {
  return { tool_calls: run.tool_calls, ...(run.rounds != null ? { rounds: run.rounds, sources: run.sources } : {}) };
}

// --- harness (you usually won't need to touch below this line) --------------

function parseArgs(argv) {
  const a = { flow: join(AKB_ROOT, 'build', 'evals', 'question-page'), variant: 'baseline',
              model: 'claude-opus-5-5', reps: 1, concurrency: 2, timeoutS: 900,
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
  eprint('usage: node evals/question-page.mjs --variant baseline|v<N> [--only id,id] [--include-drafts] [--dry-run] [--flow DIR] [--model ID] [--reps N] [--concurrency N] [--timeout-s N (0 = no ceiling)] [--approve-harness]');
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
  const ctx = { ...args, state: st };

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
          const run = await withBackoff(() => { tAttempt = Date.now(); return runCase(c, ctx); },
            appRetry, deadline);
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
