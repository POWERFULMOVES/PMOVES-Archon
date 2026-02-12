# PR Review Integration for PMOVES.AI

**Purpose:** Document how PR review comments are parsed, analyzed, and integrated with Supabase/BoTZ for continuous learning.

**Last Updated:** 2026-02-12

---

## Overview

PMOVES.AI uses an intelligent PR review system that:
1. **Parses** review comments for actionable feedback
2. **Extracts** learnings and patterns
3. **Stores** feedback in Supabase for tracking
4. **Distributes** via BoTZ network for awareness
5. **Evolves** guidelines based on review history

```
Review Comment → Parser → Supabase → BoTZ → Updated Guidelines
```

### Goals

- **Targeted Reviews:** Ensure all comments are actionable
- **Pattern Learning:** Identify recurring issues for documentation
- **PMOVES.AI Awareness:** Reviews consider integration patterns
- **Feedback Loop:** Continuously improve code quality

---

## PR Comment Parser

### Comment Categories

```python
# Comment classification
class ReviewCategory(str, Enum):
    """Categories of PR review comments."""
    NITPICK = "nitpick"           # Style, minor improvements
    BUG = "bug"                   # Actual bug found
    SECURITY = "security"           # Security vulnerability
    INTEGRATION = "integration"       # PMOVES.AI integration issue
    API_CONTRACT = "api_contract"  # API breaking change
    PERFORMANCE = "performance"       # Performance concern
    TESTING = "testing"             # Missing or inadequate tests
    DOCUMENTATION = "documentation"   # Doc issues
    OUT_OF_SCOPE = "out_of_scope"   # Unrelated to PR
    SUGGESTION = "suggestion"       # Optional improvement
    PMOVES_PATTERN = "pmoves_pattern"  # PMOVES.AI pattern violation
```

### Parser Implementation

```python
# pmoves/docs/pr_review_parser.py
import re
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class ReviewCategory(Enum):
    NITPICK = "nitpick"
    BUG = "bug"
    SECURITY = "security"
    INTEGRATION = "integration"
    API_CONTRACT = "api_contract"
    PERFORMANCE = "performance"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    OUT_OF_SCOPE = "out_of_scope"
    SUGGESTION = "suggestion"
    PMOVES_PATTERN = "pmoves_pattern"

@dataclass
class ParsedComment:
    """Parsed PR review comment."""
    category: ReviewCategory
    severity: str  # "critical", "major", "minor"
    file_path: Optional[str]
    line_number: Optional[int]
    description: str
    suggestion: Optional[str]
    is_actionable: bool
    pmoves_aware: bool  # Does comment reference PMOVES.AI patterns?

def parse_review_comment(comment_body: str) -> ParsedComment:
    """Parse a GitHub PR review comment into structured data."""

    # Check for PMOVES.AI pattern references
    pmoves_patterns = [
        r"pmoves_announcer", r"pmoves_registry", r"pmoves_health",
        r"pmoves_common", r"/healthz", r"/metrics",
        r"NATS", r"CHIT", r"TensorZero", r"Hi-RAG"
    ]
    pmoves_aware = any(re.search(p, comment_body, re.I) for p in pmoves_patterns)

    # Detect category
    if re.search(r"security|vulnerability|exploit", comment_body, re.I):
        category = ReviewCategory.SECURITY
        severity = "critical"
    elif re.search(r"bug|error|fail|crash", comment_body, re.I):
        category = ReviewCategory.BUG
        severity = "major"
    elif re.search(r"integration|NATS|pmoves_", comment_body, re.I):
        category = ReviewCategory.INTEGRATION
        severity = "major"
    elif re.search(r"API|contract|breaking", comment_body, re.I):
        category = ReviewCategory.API_CONTRACT
        severity = "critical"
    elif re.search(r"performance|slow|optimize", comment_body, re.I):
        category = ReviewCategory.PERFORMANCE
        severity = "major"
    elif re.search(r"test|coverage|spec", comment_body, re.I):
        category = ReviewCategory.TESTING
        severity = "major"
    elif re.search(r"doc|README|comment", comment_body, re.I):
        category = ReviewCategory.DOCUMENTATION
        severity = "minor"
    elif re.search(r"nitpick|style|formatting", comment_body, re.I):
        category = ReviewCategory.NITPICK
        severity = "minor"
    else:
        category = ReviewCategory.SUGGESTION
        severity = "minor"

    # Extract file location if present
    # Pattern: "In file.py:123" or "file.py line 123"
    file_match = re.search(r"(\w+\.(?:py|ts|js|yaml|yml)):(\d+)", comment_body)
    file_path = file_match.group(1) if file_match else None
    line_number = int(file_match.group(2)) if file_match else None

    # Extract suggestion (code block or explicit suggestion)
    suggestion_block = re.search(r"```(?:python|javascript|bash)?\n(.*?)```", comment_body, re.S)
    suggestion = suggestion_block.group(1).strip() if suggestion_block else None

    # Determine if actionable
    actionable = category != ReviewCategory.OUT_OF_SCOPE and category != ReviewCategory.NITPICK

    return ParsedComment(
        category=category,
        severity=severity,
        file_path=file_path,
        line_number=line_number,
        description=comment_body[:200],  # Truncate for storage
        suggestion=suggestion,
        is_actionable=actionable,
        pmoves_aware=pmoves_aware
    )
```

---

## Supabase Storage Schema

### Review Feedback Table

```sql
-- pmoves/docs/schema/pr_reviews.sql
CREATE TABLE IF NOT EXISTS pr_reviews (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- PR reference
    pr_number INTEGER NOT NULL,
    pr_repo VARCHAR(255) NOT NULL,
    pr_sha VARCHAR(40) NOT NULL,

    -- Comment reference
    comment_id BIGINT NOT NULL,
    comment_author VARCHAR(255) NOT NULL,
    comment_body TEXT NOT NULL,
    comment_created_at TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Parsed data
    category VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    file_path VARCHAR(512),
    line_number INTEGER,
    suggestion TEXT,

    -- Actionability
    is_actionable BOOLEAN NOT NULL DEFAULT TRUE,
    was_addressed BOOLEAN DEFAULT FALSE,
    addressed_at TIMESTAMP WITH TIME ZONE,

    -- PMOVES.AI awareness
    pmoves_aware BOOLEAN NOT NULL DEFAULT FALSE,
    pmoves_pattern_referenced VARCHAR(100),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_pr_reviews_pr ON pr_reviews(pr_number, pr_repo);
CREATE INDEX IF NOT EXISTS idx_pr_reviews_category ON pr_reviews(category);
CREATE INDEX IF NOT EXISTS idx_pr_reviews_actionable ON pr_reviews(is_actionable, was_addressed);
CREATE INDEX IF NOT EXISTS idx_pr_reviews_pmoves ON pr_reviews(pmoves_aware);
```

### Learning Patterns Table

```sql
-- For tracking recurring issues
CREATE TABLE IF NOT EXISTS review_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Pattern identification
    pattern_name VARCHAR(255) NOT NULL,
    pattern_category VARCHAR(50) NOT NULL,

    -- Occurrence tracking
    occurrence_count INTEGER DEFAULT 1,
    first_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Related PRs
    affected_prs INTEGER[],  -- Array of PR numbers

    -- Resolution guidance
    suggested_fix TEXT,
    documentation_reference VARCHAR(512),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(pattern_name, pattern_category)
);
```

---

## BoTZ Network Distribution

### Publishing Review Learnings

```python
# BoTZ skill for distributing review learnings
# features/skills/repos/review-learner/learn.py
from pmoves_announcer import announce_service
from pmoves_registry import get_service_url
import asyncpg

async def publish_review_learning(
    pattern_name: str,
    category: str,
    suggested_fix: str
):
    """Publish review learning to BoTZ network."""

    # Post to NATS for network-wide awareness
    nats_url = os.getenv("NATS_URL")
    js = await nats.connect(nats_url)

    await js.publish(
        "pmoves.review.pattern.v1",
        {
            "pattern_name": pattern_name,
            "category": category,
            "suggested_fix": suggested_fix,
            "documentation": f"See: {DOCS_URL}",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

    # Store in Supabase
    conn = await asyncpg.connect(SUPABASE_URL)
    await conn.execute("""
        INSERT INTO review_patterns (pattern_name, pattern_category, suggested_fix)
        VALUES ($1, $2, $3)
        ON CONFLICT (pattern_name, pattern_category)
        DO UPDATE SET
            occurrence_count = review_patterns.occurrence_count + 1,
            last_seen_at = NOW()
    """, pattern_name, category, suggested_fix)
```

### NATS Subjects

**Review Learning Subjects:**
- `pmoves.review.pattern.v1` - New pattern discovered
- `pmoves.review.addressed.v1` - Pattern was addressed
- `pmoves.review.guidance.v1` - Updated guidelines

---

## Common PMOVES.AI Patterns

### Integration Patterns Tracked

| Pattern | Category | Common Locations | Guidance |
|----------|----------|-------------------|----------|
| Missing `/healthz` endpoint | INTEGRATION | New services | All services must expose health endpoint |
| Missing `/metrics` endpoint | INTEGRATION | All services | Prometheus scraping required |
| No NATS announcement | INTEGRATION | New services | Use `pmoves_announcer` |
| Hardcoded service URLs | PMOVES_PATTERN | All services | Use `pmoves_registry` for discovery |
| Missing CHIT manifest | INTEGRATION | New services | Register secrets in `chit/secrets_manifest_v2.yaml` |
| No `pmoves_common` types | PMOVES_PATTERN | Python services | Use shared type definitions |

### Security Patterns Tracked

| Pattern | Category | Severity | Guidance |
|----------|----------|----------|----------|
| PII in logs | SECURITY | critical | Use `logError()` not `console.error` |
| JWT in query params | SECURITY | critical | Use Authorization header only |
| Unvalidated input | SECURITY | critical | Validate all user inputs |
| Hardcoded secrets | SECURITY | critical | Never commit secrets, use env vars |

### Testing Patterns Tracked

| Pattern | Category | Severity | Guidance |
|----------|----------|----------|----------|
| No unit tests | TESTING | major | Add tests for new functions |
| No integration tests | TESTING | major | Test service integration points |
| Missing edge cases | TESTING | minor | Add tests for error conditions |

---

## Review Command Integration

### `/pr-comments` Command

```python
# skills/repos/pr-review-toolkit/pr_comments.py
from .pr_review_parser import parse_review_comment
from .supabase_client import store_review, get_pattern_count
import click

@click.command()
@click.argument('pr_number', type=int)
def pr_comments(pr_number: int):
    """Analyze PR review comments and extract learnings."""

    # Fetch PR comments via GitHub CLI
    result = subprocess.run(
        ["gh", "pr", "view", str(pr_number), "--json", "comments"],
        capture_output=True
    )
    comments = json.loads(result.stdout)

    actionable_count = 0
    pmoves_aware_count = 0

    for comment in comments:
        parsed = parse_review_comment(comment['body'])

        # Store in Supabase
        store_review(parsed, pr_number, comment['id'])

        # Track metrics
        if parsed.is_actionable:
            actionable_count += 1
        if parsed.pmoves_aware:
            pmoves_aware_count += 1

        # Check for recurring patterns
        pattern_count = get_pattern_count(parsed.description)
        if pattern_count > 3:
            click.echo(f"⚠️  Recurring pattern detected: {parsed.category}")

    # Summary
    click.echo(f"\n📊 Review Summary:")
    click.echo(f"   Total comments: {len(comments)}")
    click.echo(f"   Actionable items: {actionable_count}")
    click.echo(f"   PMOVES.AI aware: {pmoves_aware_count}")

    # Publish to BoTZ
    publish_review_summary(pr_number, actionable_count, pmoves_aware_count)
```

### Usage

```bash
# Analyze PR #1234
/pr-comments 1234

# Output:
# 📊 Review Summary:
#    Total comments: 15
#    Actionable items: 8
#    PMOVES.AI aware: 5
# ℹ️  Patterns stored in Supabase
# ℹ️  Learnings published to BoTZ network
```

---

## Learning Loop

### Pattern Evolution

```python
# Weekly pattern analysis
async def analyze_weekly_patterns():
    """Identify patterns requiring guideline updates."""

    # Get top patterns from Supabase
    patterns = await get_top_patterns(days=7, limit=10)

    for pattern in patterns:
        if pattern.occurrence_count > 5:
            # Update relevant documentation
            await update_guideline(
                category=pattern.category,
                pattern=pattern.pattern_name,
                guidance=pattern.suggested_fix
            )

            # Publish updated guidance
            await publish_guidance_update(
                category=pattern.category,
                updated_guidance=True
            )
```

### Documentation Updates

When patterns recur more than **5 times in a week**:

1. **Update** relevant documentation (ATOMIC_COMMIT_WORKFLOW.md, TARGETED_PR_WORKFLOW.md)
2. **Add** example to SUBMODULE_INTEGRATION_CHECKLIST.md
3. **Publish** to `pmoves.review.guidance.v1` NATS subject
4. **Track** documentation effectiveness

---

## Review Quality Metrics

### Tracked Metrics

```sql
-- Review quality dashboard query
SELECT
    category,
    COUNT(*) as total_comments,
    SUM(CASE WHEN is_actionable THEN 1 ELSE 0 END) as actionable_count,
    SUM(CASE WHEN pmoves_aware THEN 1 ELSE 0 END) as pmoves_aware_count,
    AVG(CASE WHEN was_addressed THEN 1 ELSE 0 END) as address_rate
FROM pr_reviews
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY category;
```

### Quality Indicators

| Metric | Target | Meaning |
|---------|---------|-----------|
| Actionable Rate | > 80% | Reviews are focused and useful |
| PMOVES.AI Aware Rate | > 60% | Reviews consider integration patterns |
| Address Rate | > 90% | Actionable items are being fixed |
| Pattern Recurrence | < 3 | New patterns documented quickly |

---

## Example Workflow

### Complete Review Integration Flow

```
1. Developer submits PR
   ↓
2. Reviewer adds comments
   ↓
3. /pr-comments parser analyzes comments
   ↓
4. Actionable items stored in Supabase
   ↓
5. Recurring patterns identified
   ↓
6. Learnings published to BoTZ network
   ↓
7. Documentation updated if needed
   ↓
8. Developer addresses comments
   ↓
9. PR merged (addressed items tracked)
   ↓
10. Patterns analyzed for guideline updates
```

---

## Related Documentation

- [ATOMIC_COMMIT_WORKFLOW.md](ATOMIC_COMMIT_WORKFLOW.md) - Atomic commit guidelines
- [TARGETED_PR_WORKFLOW.md](TARGETED_PR_WORKFLOW.md) - Targeted PR workflow
- [SUBMODULE_INTEGRATION_CHECKLIST.md](SUBMODULE_INTEGRATION_CHECKLIST.md) - Integration checklist
- [CHIT_V2_SPECIFICATION.md](CHIT_V2_SPECIFICATION.md) - CHIT manifest format

---

**Maintainer:** PMOVES.AI Team
