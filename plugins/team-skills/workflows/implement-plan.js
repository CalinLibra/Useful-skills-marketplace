export const meta = {
  name: 'implement-plan',
  description: 'Implement an approved plan: code and tests per task, one review, one fix round, final checks',
  whenToUse: 'Started by the team-skills ship skill after the user approves a plan',
  phases: [
    { title: 'Code', detail: 'one coder per task, in order; each runs the tests' },
    { title: 'Review', detail: 'one reviewer over the whole change' },
    { title: 'Fix', detail: 'one fix round for critical/important findings' },
    { title: 'Verify', detail: 'final test, lint and build run' },
  ],
}

// args: { goal, baseCommit, profile: {test, lint, build, conventions, ...},
//         tasks: [{ title, details, files, tests }] }

const CODER = `You are the coder in the team's ship pipeline.
- Implement exactly the task below. Touch only the files it needs; follow the existing code style, patterns and the project conventions.
- Write or update tests for the new behavior with the project's existing test framework and layout.
- Run the project's test command (from the profile; scope it to the affected tests first if the runner supports it, then the full command). If tests fail, fix and re-run, up to 3 attempts.
- Do not add dependencies unless the task says so. Do not commit, push, stash, switch branches or otherwise change git state.
- Report honestly: testsPassed is true only if the last full test run passed. List every file you created or modified (repo-relative).`

const REVIEWER = `You are the reviewer in the team's ship pipeline. You are read-only: never modify files or git state.
Review the whole change: run \`git diff <baseCommit>\` and \`git status --porcelain\`, and read new untracked files in full.
Report real defects only:
- correctness bugs and unhandled edge cases
- security: injection, secrets in code or logs, missing authorization or validation
- error handling that swallows failures
- new behavior without tests, or tests that assert nothing
- breaking changes to public APIs or contracts not asked for by the goal
- clear violations of the project conventions
Severity: critical = wrong or unsafe behavior; important = should not ship as is; minor = polish. No style nitpicks. Cite file and line. Return an empty list if the change is sound.`

const TESTER = `You are the tester in the team's ship pipeline. Run each command below in order from the repository root, exactly as written.
Do not modify any file or git state and do not try to fix anything. For each command report the exit code and the last 30 lines of output.
passed is true only if every command exited with 0.`

const RESULT = {
  type: 'object',
  properties: {
    status: { type: 'string', enum: ['done', 'blocked'] },
    files: { type: 'array', items: { type: 'string' } },
    testsPassed: { type: 'boolean' },
    summary: { type: 'string' },
    notes: { type: 'string' },
  },
  required: ['status', 'files', 'testsPassed', 'summary'],
}

const FINDINGS = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          severity: { type: 'string', enum: ['critical', 'important', 'minor'] },
          file: { type: 'string' },
          line: { type: 'number' },
          problem: { type: 'string' },
          fix: { type: 'string' },
        },
        required: ['severity', 'file', 'problem'],
      },
    },
  },
  required: ['findings'],
}

const CHECK = {
  type: 'object',
  properties: {
    passed: { type: 'boolean' },
    results: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          command: { type: 'string' },
          exitCode: { type: 'number' },
          tail: { type: 'string' },
        },
        required: ['command', 'exitCode'],
      },
    },
  },
  required: ['passed', 'results'],
}

if (!args || !Array.isArray(args.tasks) || !args.tasks.length) {
  throw new Error('implement-plan needs args.tasks (a non-empty array); start it from the ship skill')
}
if (!args.baseCommit) throw new Error('implement-plan needs args.baseCommit')

const profile = args.profile || {}
const context = `Goal: ${args.goal || '(not given)'}
Base commit: ${args.baseCommit}
Project profile: ${JSON.stringify(profile)}`

phase('Code')
const completed = []
for (const [i, task] of args.tasks.entries()) {
  const prompt = `${CODER}

${context}

Task ${i + 1} of ${args.tasks.length}: ${task.title}
${task.details || ''}
Files expected: ${(task.files || []).join(', ') || 'decide from the code'}
Tests to write: ${task.tests || 'as appropriate for the change'}
Already completed: ${completed.map(c => `${c.title}: ${c.summary}`).join(' | ') || 'nothing yet'}`
  const result = await agent(prompt, { label: `code:${i + 1}`, phase: 'Code', schema: RESULT })
  if (!result || result.status !== 'done' || !result.testsPassed) {
    log(`Stopped at task ${i + 1} (${task.title}): ${result ? (result.notes || result.summary) : 'coder failed'}`)
    return { status: 'stopped', stoppedAt: task.title, completed, last: result }
  }
  completed.push({ title: task.title, ...result })
  log(`Task ${i + 1}/${args.tasks.length} done: ${task.title}`)
}

phase('Review')
const review = await agent(`${REVIEWER}

${context}
Tasks implemented: ${completed.map(c => `${c.title} (${c.files.join(', ')})`).join('; ')}`,
  { label: 'review', phase: 'Review', schema: FINDINGS })
const findings = review ? review.findings : []
const toFix = findings.filter(f => f.severity !== 'minor')

let fix = null
if (toFix.length) {
  phase('Fix')
  fix = await agent(`${CODER}

${context}

Fix these review findings, then run the full test command:
${JSON.stringify(toFix, null, 2)}`,
    { label: 'fix', phase: 'Fix', schema: RESULT })
  if (!fix || fix.status !== 'done' || !fix.testsPassed) {
    return { status: 'fix_failed', completed, findings, fix }
  }
} else {
  log(review ? 'Review found nothing to fix' : 'Reviewer failed; continuing to final checks')
}

phase('Verify')
const commands = [profile.test, profile.lint, profile.build].filter(Boolean)
let check = null
if (commands.length) {
  check = await agent(`${TESTER}

Commands:
${commands.map(c => `- ${c}`).join('\n')}`,
    { label: 'verify', phase: 'Verify', schema: CHECK, effort: 'low' })
} else {
  log('No test/lint/build commands in the profile; final checks skipped')
}

return {
  status: commands.length && (!check || !check.passed) ? 'checks_failed' : 'completed',
  completed,
  findings,
  fixed: toFix.length,
  fix,
  check,
  reviewed: Boolean(review),
}
