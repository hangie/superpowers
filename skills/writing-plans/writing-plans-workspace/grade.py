#!/usr/bin/env python3
"""Grade a plan against assertions from evals.json.

Usage: python grade.py <plan_path> <eval_id>

Assertion polarity:
- "Fail if present" assertions (first 15 per eval): describe bad things.
  Plan PASSES if the bad thing is ABSENT.
- "Fail if absent" assertions (remaining): describe good things.
  Plan PASSES if the good thing is PRESENT.

The heuristic: assertions starting with "The output contains" where the
described thing is code/syntax/commands are "fail if present" (bad).
Assertions with "at least one", "mentions", "identifies", "does not contain",
"acknowledges", "prescribes" signal what should/shouldn't be there.
"""

import json
import re
import sys
from pathlib import Path

EVALS_PATH = Path(__file__).parent.parent / "evals" / "evals.json"


def load_plan(path: str) -> str:
    return Path(path).read_text()


def load_eval(eval_id: int) -> dict:
    with open(EVALS_PATH) as f:
        data = json.load(f)
    for ev in data["evals"]:
        if ev["id"] == eval_id:
            return ev
    raise ValueError(f"Eval {eval_id} not found")


def check_assertion(text: str, plan: str) -> dict:
    """Check a single assertion. Returns {text, passed, evidence}."""
    plan_lower = plan.lower()

    # "does not contain" assertions -> plan should NOT have the thing
    if "does not contain" in text.lower():
        present = _search_pattern(text, plan, negated=True)
        return {
            "text": text,
            "passed": not present,
            "evidence": f"{'Found' if present else 'Not found'} in plan",
        }

    # "The output contains more than N distinct" -> fail if present (over-engineering)
    if "more than" in text.lower() and ("tasks" in text.lower() or "steps" in text.lower()):
        count = _count_top_level_tasks(plan)
        threshold = int(re.search(r"more than (\d+)", text).group(1))
        present = count > threshold
        return {
            "text": text,
            "passed": not present,
            "evidence": f"Found {count} top-level tasks (threshold: >{threshold})",
        }

    # "does not enumerate all 47 components"
    if "does not enumerate" in text.lower():
        present = _enumerates_all_components(plan)
        return {
            "text": text,
            "passed": not present,
            "evidence": f"{'Enumerates' if present else 'Does not enumerate'} all components",
        }

    # "at least one" / "mentions" / "identifies" / "acknowledges" -> fail if absent (good things)
    good_signals = ["at least one", "mentions", "identifies", "acknowledges",
                     "explicitly identifies", "investigation or diagnosis",
                     "does not prescribe", "prescribes a specific"]

    for signal in good_signals:
        if signal in text.lower():
            if "does not prescribe" in text.lower():
                present = _search_pattern(text, plan, negated=True)
                return {
                    "text": text,
                    "passed": not present,
                    "evidence": f"{'Found prescribed' if present else 'No prescription found'} in plan",
                }
            if "prescribes a specific" in text.lower():
                # This is a "fail if present" - bad if it prescribes before diagnosis
                present = _prescribes_before_diagnosis(text, plan)
                return {
                    "text": text,
                    "passed": not present,
                    "evidence": f"{'Prescribes before diagnosis' if present else 'Investigation comes first'}",
                }
            present = _search_good_pattern(text, plan)
            return {
                "text": text,
                "passed": present,
                "evidence": f"{'Found' if present else 'Not found'} in plan",
            }

    # Default: "The output contains X" where X is code/syntax -> fail if present
    present = _search_pattern(text, plan, negated=False)
    return {
        "text": text,
        "passed": not present,
        "evidence": f"{'Found' if present else 'Not found'} in plan",
    }


def _search_pattern(assertion: str, plan: str, negated: bool = False) -> bool:
    """Search for specific patterns mentioned in an assertion."""
    a = assertion.lower()
    p_lower = plan.lower()

    # Fenced code block with language
    if "fenced code block" in a:
        return bool(re.search(r"```\s*(python|typescript|javascript|bash|sh|ts|js|tsx|jsx|go|rust|ruby|java|css|html|json|yaml|yml|sql|graphql|swift|kotlin|c\b|cpp|csharp)", plan, re.IGNORECASE))

    # git commit -m
    if "git commit -m" in a:
        return "git commit -m" in plan

    # Expected: PASS/FAIL
    if "expected: pass" in a or "expected: fail" in a:
        return bool(re.search(r"expected:\s*(pass|fail)", plan, re.IGNORECASE))

    # git add with file paths
    if "git add " in a and "file path" in a:
        return bool(re.search(r"git add\s+\S+", plan))

    # Run: with command
    if "'run:'" in a and "terminal command" in a:
        return bool(re.search(r"Run:\s*`?\S+", plan))

    # CLI flag in run command
    if "cli flag" in a:
        return bool(re.search(r"(run|execute|npm|yarn|pytest|npx|bun)\s+.*\s+(-\w|--\w)", plan, re.IGNORECASE))

    # Test function definition
    if "def test_" in a or "it('" in a or "describe('" in a:
        return bool(re.search(r"(def test_|it\(|describe\()", plan))

    # Import syntax
    if "import {" in a or "from X import" in a or "require(" in a:
        return bool(re.search(r"(import\s*\{|from\s+\S+\s+import|require\()", plan))

    # Variable declaration
    if "const " in a or "let " in a or "var " in a:
        return bool(re.search(r"(const|let|var)\s+\w+\s*=", plan))

    # File path with line number
    if "filename:nnn" in a or "filename:" in a:
        return bool(re.search(r"\w+\.\w+:\d{2,}", plan))

    # Test assertion syntax
    if ".tobe(" in a or ".toequal(" in a:
        return bool(re.search(r"\.(toBe|toEqual|toHaveBeenCalled)\(", plan))

    # Conventional commit message
    if "conventional commit" in a or ("starting with 'feat:'" in a):
        return bool(re.search(r"^(feat|fix|chore|refactor|test):", plan, re.MULTILINE))

    # Test lifecycle hooks
    if "beforeeach(" in a or "aftereach(" in a:
        return bool(re.search(r"(beforeEach|afterEach|beforeAll)\(", plan))

    # Expected output prediction
    if "expected output:" in a or "you should see:" in a:
        return bool(re.search(r"(expected output:|you should see:|expected:)", plan, re.IGNORECASE))

    # npm/yarn/bun/pnpm run
    if "npm run" in a or "yarn run" in a:
        return bool(re.search(r"(npm|yarn|bun|pnpm)\s+run\s+", plan))

    # Playwright API calls
    if "playwright api" in a or "page.click" in a:
        return bool(re.search(r"(page\.(click|goto|fill|waitFor)|await page|expect\(page\))", plan))

    # Specific Tailwind classes
    if "tailwind utility class" in a:
        return bool(re.search(r"(text-sm|flex-1|bg-blue-\d+|p-\d+|m-\d+|w-\d+)", plan))

    # Specific implementation function names
    if "cleargitcache" in a or "getgitstatus" in a:
        return bool(re.search(r"(clearGitCache|getGitStatus|getGitAheadBehind)", plan, re.IGNORECASE))

    # Specific git show/checkout command
    if "git show" in a or "git checkout command" in a:
        return bool(re.search(r"git\s+(show|checkout)\s+\S+", plan))

    # Specific search commands
    if "grep -r" in a or "sed -i" in a or "find . -name" in a:
        return bool(re.search(r"(grep\s+-r|sed\s+-i|find\s+\.\s+-name|rg\s+)", plan))

    # Specific DB/locking syntax
    if "begin transaction" in a or "select for update" in a:
        return bool(re.search(r"(BEGIN TRANSACTION|SELECT\s+.*FOR UPDATE|LOCK TABLE)", plan, re.IGNORECASE))

    # Specific Playwright config
    if "playwright.config" in a or "playwright config" in a:
        return bool(re.search(r"playwright\.config\.(ts|js)", plan))

    # IDE commands
    if "find and replace" in a or "rename symbol" in a:
        return bool(re.search(r"(Find and Replace|Rename Symbol|VSCode refactor)", plan, re.IGNORECASE))

    # Cache clearing/isolation
    if "cache clearing" in a or "cache isolation" in a:
        return bool(re.search(r"cache\s*(clear|isolat|invalidat|purg)", plan, re.IGNORECASE))

    # Specific concurrency mechanism before diagnosis
    if "prescribes a specific concurrency" in a:
        return _prescribes_before_diagnosis(assertion, plan)

    # Fallback
    return False


def _search_good_pattern(assertion: str, plan: str) -> bool:
    """Search for good things that should be present."""
    a = assertion.lower()
    p = plan.lower()

    # Goal/intent/objective
    if "'goal'" in a or "'intent'" in a or "'objective'" in a or "'purpose'" in a or "'we want'" in a:
        return bool(re.search(r"\b(goal|intent|objective|purpose|we want)\b", p))

    # Because/in order to/so that
    if "'because'" in a or "'in order to'" in a or "'so that'" in a:
        return bool(re.search(r"\b(because|in order to|so that)\b", p))

    # Completion criterion
    if "'passes'" in a or "'verified'" in a or "'no remaining'" in a or "'confirmed'" in a or "'complete when'" in a:
        return bool(re.search(r"\b(passes|verified|no remaining|confirmed|complete when)\b", p))

    # Risk/constraint
    if "'risk'" in a or "'constraint'" in a or "'important'" in a or "'note that'" in a or "'caveat'" in a or "'careful'" in a:
        return bool(re.search(r"\b(risk|constraint|important|note that|caveat|careful)\b", p))

    # Successful outcome description
    if "successful outcome" in a:
        return bool(re.search(r"\b(success|successful|done when|complete when|end state|outcome)\b", p))

    # Dynamic class logic
    if "dynamic class logic" in a:
        return bool(re.search(r"dynamic\s*(class|style|css)", p))

    # Design token / CSS variable mapping
    if "design token" in a or "css variable" in a:
        return bool(re.search(r"(design token|css variable|css custom propert)", p))

    # Grouping/categorization
    if "'group'" in a or "'categorise'" in a or "'batch'" in a or "'phase'" in a:
        return bool(re.search(r"\b(group|categori[sz]e|batch|phase|tier|type)\b", p))

    # Payment iframe blocker
    if "payment iframe" in a or "payment step" in a:
        return bool(re.search(r"(payment.*(iframe|blocker|constraint|third.party)|iframe.*payment|third.party.*payment)", p))

    # Mock/stub/skip for payment
    if "'mock'" in a or "'stub'" in a or "'skip'" in a or "'workaround'" in a:
        return bool(re.search(r"\b(mock|stub|skip|workaround|alternative)\b", p))

    # Test data setup
    if "test data" in a or "test accounts" in a:
        return bool(re.search(r"(test data|test account|test product|test address|seed data|fixture|test user)", p))

    # Existing Playwright config/setup
    if "existing playwright" in a:
        return bool(re.search(r"(existing.*(playwright|setup|config)|playwright.*(existing|current|setup))", p))

    # Investigation before fix
    if "investigation or diagnosis" in a:
        return _investigation_before_fix(plan)

    # Reproduction difficulty
    if "reproducing the bug" in a or "reproduction difficulty" in a:
        return bool(re.search(r"(difficult to reproduce|hard to reproduce|reproduce|reproduction|intermittent|flak)", p))

    # Definition of fixed
    if "definition of what 'fixed' looks like" in a:
        return bool(re.search(r"(fixed.*(means|looks like|when|defined)|definition of (done|fixed)|done when|success criteria)", p))

    # Approach may change
    if "approach may need to change" in a:
        return bool(re.search(r"(approach.*(may|might|could)\s*(need to\s*)?(change|adapt|evolve)|depend.*(what.*find|investigation|diagnosis)|pivot|adjust)", p))

    # Branch difference check
    if "checking or verifying the difference" in a:
        return bool(re.search(r"(diff|difference|compare|comparing).*(branch|commit|change)", p))

    # Unrelated changes risk
    if "unrelated changes" in a:
        return bool(re.search(r"(unrelated\s*(change|commit|code)|change.*should not.*cop)", p))

    # Interleaved vs sequential commits
    if "interleaved or sequential" in a:
        return bool(re.search(r"(interleav|sequential|commit.*order|order.*commit|mixed.*commit|entangle)", p))

    # New branch from main
    if "based off main" in a:
        return bool(re.search(r"(base[d]?\s*(off|on)\s*main|branch.*from\s*main|new branch.*main|main.*as.*base)", p))

    # Same files risk
    if "same files" in a:
        return bool(re.search(r"(same file|shared file|overlap|touch.*same|both.*modif)", p))

    # Existing PR working state
    if "existing pr must remain" in a or "working state" in a:
        return bool(re.search(r"(existing.*(pr|pull request).*(working|intact|valid|functional|broken)|remain.*(working|functional)|break.*existing)", p))

    # Git strategy not prescribed
    if "does not prescribe a specific git strategy" in a:
        # This is actually a "fail if present" check
        return not bool(re.search(r"\b(cherry.pick|rebase|manual extraction)\b.*\b(first|then|step|use)\b", p))

    # External consumers
    if "external consumers" in a or "downstream callers" in a:
        return bool(re.search(r"(external\s*(consumer|caller|user|package)|downstream|dependent\s*(package|project)|published\s*api|public\s*api|breaking change)", p))

    # No remaining references to old name
    if "no remaining references" in a and "getuserdata" in a:
        return bool(re.search(r"(no remaining|no.*reference|zero.*reference|verify.*removed|getUserData.*gone|removed.*getUserData)", p))

    # Specific concurrency before diagnosis
    if "prescribes a specific concurrency" in a:
        return not _prescribes_before_diagnosis(assertion, plan)

    return False


def _count_top_level_tasks(plan: str) -> int:
    """Count top-level tasks/sections in a plan."""
    # Count ### Task N or ## Task N or numbered top-level items
    task_headers = re.findall(r"^#{2,3}\s*(Task|Step|Phase)\s*\d+", plan, re.MULTILINE | re.IGNORECASE)
    if task_headers:
        return len(task_headers)
    # Fallback: count numbered sections
    numbered = re.findall(r"^#{2,3}\s*\d+[\.\):]", plan, re.MULTILINE)
    return len(numbered) if numbered else 0


def _enumerates_all_components(plan: str) -> bool:
    """Check if the plan lists all 47 components individually."""
    # Count component-like mentions
    component_mentions = re.findall(r"(Button|Input|Modal|Card|Header|Footer|Nav|Sidebar|Table|Form|Select|Checkbox|Radio|Toggle|Badge|Alert|Toast|Dropdown|Tooltip|Tabs|Accordion|Avatar|Progress|Spinner|Skeleton|Divider|Chip|List|Menu|Dialog|Drawer|Panel|Grid|Layout|Icon|Image|Link|Text|Label|Tag|Status)", plan)
    return len(set(component_mentions)) > 20


def _investigation_before_fix(plan: str) -> bool:
    """Check that investigation/diagnosis steps come before fix steps."""
    p = plan.lower()
    invest_pos = None
    fix_pos = None
    for m in re.finditer(r"\b(investigat|diagnos|analyz|understand|identify.*cause|root cause|examine|inspect)\b", p):
        if invest_pos is None:
            invest_pos = m.start()
        break
    for m in re.finditer(r"\b(implement.*fix|apply.*fix|add.*lock|add.*mutex|implement.*solution|write.*fix)\b", p):
        if fix_pos is None:
            fix_pos = m.start()
        break
    if invest_pos is not None:
        if fix_pos is None or invest_pos < fix_pos:
            return True
    return False


def _prescribes_before_diagnosis(assertion: str, plan: str) -> bool:
    """Check if plan prescribes a specific solution before any diagnosis step."""
    p = plan.lower()
    # Find first diagnosis/investigation mention
    diag = re.search(r"\b(investigat|diagnos|analyz|understand|examine|inspect)\b", p)
    # Find first prescription
    prescribe = re.search(r"\b(add a mutex|use a lock|implement a queue|use a semaphore|add.*lock|use.*transaction)\b", p)
    if prescribe and (not diag or prescribe.start() < diag.start()):
        return True
    return False


def grade_eval(plan_path: str, eval_id: int) -> dict:
    plan = load_plan(plan_path)
    ev = load_eval(eval_id)
    results = []
    passed = 0
    total = len(ev["assertions"])

    for assertion in ev["assertions"]:
        result = check_assertion(assertion["text"], plan)
        results.append(result)
        if result["passed"]:
            passed += 1

    return {
        "eval_id": eval_id,
        "prompt": ev["prompt"][:100] + "...",
        "total": total,
        "passed": passed,
        "pass_rate": round(passed / total * 100, 1),
        "results": results,
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python grade.py <plan_path> <eval_id>")
        sys.exit(1)

    plan_path = sys.argv[1]
    eval_id = int(sys.argv[2])
    result = grade_eval(plan_path, eval_id)

    print(f"\nEval {eval_id}: {result['passed']}/{result['total']} ({result['pass_rate']}%)")
    print("=" * 60)
    for r in result["results"]:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  [{status}] {r['text'][:80]}...")
        if not r["passed"]:
            print(f"         Evidence: {r['evidence']}")

    # Save as JSON
    out_path = Path(plan_path).parent / "grading.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved grading to {out_path}")
