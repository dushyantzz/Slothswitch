"""Generator script to produce a representative, high-volume benchmark dataset (200+ samples).

Categorizes across:
1. simple_classification
2. information_extraction
3. straightforward_generation
4. complex_reasoning
5. ambiguous_requests
6. requests_requiring_clarification
7. high_risk_escalation
8. malformed_unroutable

Maintains a strictly held-out test split (70% dev / 30% test).
"""

from __future__ import annotations

import json
from pathlib import Path


def generate_dataset() -> list[dict]:
    records = []
    current_id = 1

    def add_item(
        content: str,
        task_type: str,
        category: str,
        acceptable_routes: list[str],
        expected_quality: dict[str, float],
        notes: str = "",
    ):
        nonlocal current_id
        # Split assignment: deterministic 70% dev, 30% test
        split = "test" if (current_id % 10 in (3, 6, 9)) else "dev"
        records.append({
            "request_id": f"cs-{current_id:03d}",
            "content": content,
            "task_type": task_type,
            "category": category,
            "split": split,
            "acceptable_routes": acceptable_routes,
            "expected_quality": expected_quality,
            "notes": notes,
        })
        current_id += 1

    # =========================================================================
    # 1. SIMPLE CLASSIFICATION (Target: FAST_PATH / SMALL_LLM) ~30 items
    # =========================================================================
    classification_templates = [
        ("Please categorize ticket #{num}: Customer cannot log in after password change.", "account"),
        ("What department should handle: Request for volume discount on 50 licenses?", "sales"),
        ("Route ticket: Scheduled maintenance outage notification inquiry.", "general"),
        ("Classify priority: Production database unreachable, 500 users impacted.", "technical"),
        ("Is this query related to billing or technical: Why is my credit card showing pending charge?", "billing"),
        ("Assign category: Inquiring about SOC2 Type 2 compliance certification.", "legal"),
        ("Categorize: User wants to export contact list to CSV.", "account"),
        ("Determine intent: Customer asking for cancelation fee structure.", "billing"),
        ("Tag ticket #{num}: Slow response time on API v1 endpoints during European hours.", "technical"),
        ("Classify sentiment and urgency: We love your software but need faster webhooks.", "sales"),
    ]
    for i in range(3):
        for tmpl, cat in classification_templates:
            content = tmpl.format(num=1000 + i * 10 + current_id)
            add_item(
                content=content,
                task_type="simple_classification",
                category=cat,
                acceptable_routes=["FAST_PATH", "SMALL_LLM"],
                expected_quality={"FAST_PATH": 1.0, "SMALL_LLM": 0.98, "LARGE_LLM": 1.0, "CLARIFY": 0.2, "FALLBACK": 0.1, "HUMAN_REVIEW": 0.1},
                notes="Deterministic classification or lightweight model is completely sufficient",
            )

    # =========================================================================
    # 2. INFORMATION EXTRACTION (Target: FAST_PATH / SMALL_LLM) ~30 items
    # =========================================================================
    extraction_templates = [
        ("Extract the invoice ID and amount from: Paid $420.00 for order INV-89214 on May 12th.", "billing"),
        ("Extract tracking details: Package shipped via FedEx with tracking number 789123456789.", "general"),
        ("Parse error code: Service worker crashed with code ERR_CONNECTION_REFUSED at 14:02 UTC.", "technical"),
        ("Identify user email: Contact primary administrator at ops-admin@enterprise.org regarding renewal.", "account"),
        ("Extract server IP and port: Inbound traffic spike observed from 198.51.100.88:8443.", "security"),
        ("Extract organization name and domain: Signed contract for Acme Corp (acmecorp.com).", "sales"),
        ("Find ticket reference: Re: [Ticket #44921] Update regarding API gateway throttles.", "technical"),
        ("Extract subscription tier: Currently on Enterprise Plan with 200 seats.", "sales"),
        ("Parse timestamp and region: Outage began at 2026-04-10T08:30:00Z in us-east-1.", "technical"),
        ("Extract refund request details: Refund requested for transaction TX-991204 totaling $150.", "billing"),
    ]
    for i in range(3):
        for tmpl, cat in extraction_templates:
            content = tmpl
            add_item(
                content=content,
                task_type="information_extraction",
                category=cat,
                acceptable_routes=["FAST_PATH", "SMALL_LLM"],
                expected_quality={"FAST_PATH": 1.0, "SMALL_LLM": 0.96, "LARGE_LLM": 1.0, "CLARIFY": 0.2, "FALLBACK": 0.1, "HUMAN_REVIEW": 0.1},
                notes="Entity extraction with bounded deterministic pattern matching",
            )

    # =========================================================================
    # 3. STRAIGHTFORWARD GENERATION (Target: SMALL_LLM) ~40 items
    # =========================================================================
    generation_templates = [
        ("How do I update my billing credit card in the customer portal?", "billing"),
        ("Can you provide instructions on resetting a forgotten password?", "account"),
        ("What are your standard technical support business hours for Tier 1 users?", "general"),
        ("Explain how to invite a new team member to our workspace organization.", "account"),
        ("Where can I download receipts for past subscription cycles?", "billing"),
        ("What is the difference between the Starter and Professional pricing plans?", "sales"),
        ("How do I generate an API token for our continuous integration pipeline?", "technical"),
        ("Does your service support dark mode on mobile browser viewports?", "general"),
        ("How do I configure Slack notifications for webhook alert triggers?", "technical"),
        ("Provide a polite response acknowledging ticket receipt and explaining our 4-hour SLA.", "general"),
    ]
    for i in range(4):
        for tmpl, cat in generation_templates:
            content = tmpl
            add_item(
                content=content,
                task_type="straightforward_generation",
                category=cat,
                acceptable_routes=["SMALL_LLM", "FAST_PATH", "LARGE_LLM"],
                expected_quality={"SMALL_LLM": 0.95, "LARGE_LLM": 0.98, "FAST_PATH": 0.80, "CLARIFY": 0.3, "FALLBACK": 0.2, "HUMAN_REVIEW": 0.1},
                notes="Routine generation easily handled by cost-effective small models",
            )

    # =========================================================================
    # 4. COMPLEX REASONING & DEBUGGING (Target: LARGE_LLM) ~40 items
    # =========================================================================
    complex_templates = [
        ("We are experiencing a distributed deadlock in our Kafka consumer group during partition rebalancing when consuming from 64 partitions with transactional outbox. Here is our Go worker stack trace:\n```go\nfatal error: all goroutines are asleep - deadlock!\ngoroutine 42 [semacquire]:\nsync.runtime_SemacquireMutex(0xc0001240)\ngithub.com/segmentio/kafka-go.(*Reader).CommitMessages(...)\n```\nHow should we restructure our consumer commit loop to prevent rebalance timeouts?", "technical"),
        ("Analyze our PostgreSQL query execution plan. The join between orders (40M rows) and shipments (55M rows) is performing a full sequential scan despite index on (order_id, created_at). EXPLAIN ANALYZE:\n```sql\nNested Loop (cost=0.56..892401.32 rows=15 width=128)\n-> Seq Scan on shipments (cost=0.00..654321.00 rows=15)\n```\nWhy is PostgreSQL ignoring our composite b-tree index?", "technical"),
        ("Can you help us design an idempotent event-driven architecture using AWS EventBridge, DynamoDB single-table design, and Lambda with DLQ retry mechanisms?", "technical"),
        ("We have a memory leak in our Python FastAPI microservice under sustained 5,000 RPS load. Guppy heapy shows `asyncio.Task` instances growing unbounded. Traceback snippet:\n```python\nTask was destroyed but it is pending!\ntask: <Task pending name='Task-4912' coro=<stream_events() running at worker.py:84>>\n```\nHow do we properly manage generator lifecycle in FastAPI streaming responses?", "technical"),
        ("We are migrating a monolithic monolithic Rails application to gRPC microservices in Kubernetes. What is the recommended strategy for distributed tracing with OpenTelemetry and Envoy mesh without introducing cascading latency spikes?", "technical"),
        ("Can you write a multi-threaded Rust implementation of a lock-free circular ring buffer with cache-line padding to prevent false sharing between producer and consumer cores?", "technical"),
        ("Our Kubernetes ingress controller is throwing intermittent 502 Bad Gateway errors under HTTP/2 multiplexing. Envoy logs show upstream connection termination with `stream_error: PROTOCOL_ERROR`. What proxy buffer settings must be tuned?", "technical"),
        ("Explain how to implement zero-downtime database schema migration for partitioning a 200GB Postgres table using pg_partman without locking reads during backfill.", "technical"),
    ]
    for i in range(5):
        for tmpl, cat in complex_templates:
            content = tmpl
            add_item(
                content=content,
                task_type="complex_reasoning",
                category=cat,
                acceptable_routes=["LARGE_LLM"],
                expected_quality={"LARGE_LLM": 0.95, "SMALL_LLM": 0.35, "FAST_PATH": 0.05, "CLARIFY": 0.2, "FALLBACK": 0.1, "HUMAN_REVIEW": 0.2},
                notes="Requires deep multi-step technical reasoning; small model hallucination risk is high",
            )

    # =========================================================================
    # 5. AMBIGUOUS REQUESTS (Target: CLARIFY) ~25 items
    # =========================================================================
    ambiguous_templates = [
        "Broken",
        "It doesn't work",
        "Error on page",
        "Why is it doing this?",
        "Help please",
        "Failed",
        "Not working today",
        "Problem with my account",
        "System issue",
        "Something went wrong",
    ]
    for i in range(3):
        for tmpl in ambiguous_templates:
            if len(records) >= 165:
                break
            add_item(
                content=tmpl,
                task_type="ambiguous_requests",
                category="general",
                acceptable_routes=["CLARIFY"],
                expected_quality={"CLARIFY": 1.0, "LARGE_LLM": 0.40, "SMALL_LLM": 0.30, "FAST_PATH": 0.10, "FALLBACK": 0.50, "HUMAN_REVIEW": 0.10},
                notes="Vague and insufficient information requires clarifying question rather than guessing",
            )

    # =========================================================================
    # 6. REQUESTS REQUIRING CLARIFICATION (Target: CLARIFY) ~25 items
    # =========================================================================
    clarification_templates = [
        "Please cancel my subscription immediately.",  # missing account/tenant ID
        "Can you reissue the invoice from yesterday?",  # missing company/invoice details
        "Add 5 more seats to our plan.",  # missing organization ID
        "Our custom webhook is not receiving payloads.",  # missing endpoint URL and event name
        "I was charged twice on my card, please refund.",  # missing order/transaction identifier
        "The automated test suite failed on branch release-v2.",  # missing repository/log link
        "Please reset my two-factor authentication device.",  # missing identity verification details
        "Can you extend our trial by two weeks?",  # missing workspace name
    ]
    for i in range(3):
        for tmpl in clarification_templates:
            if len(records) >= 190:
                break
            add_item(
                content=tmpl,
                task_type="requests_requiring_clarification",
                category="account" if "account" in tmpl or "device" in tmpl else "billing" if "charged" in tmpl or "cancel" in tmpl else "technical",
                acceptable_routes=["CLARIFY"],
                expected_quality={"CLARIFY": 1.0, "LARGE_LLM": 0.45, "SMALL_LLM": 0.35, "FAST_PATH": 0.10, "FALLBACK": 0.30, "HUMAN_REVIEW": 0.30},
                notes="Key parameters missing; system must prompt for missing fields before executing",
            )

    # =========================================================================
    # 7. HIGH-RISK / SAFETY ESCALATIONS (Target: HUMAN_REVIEW) ~20 items
    # =========================================================================
    high_risk_templates = [
        ("We discovered a remote code execution vulnerability (CVE-2024-3819) in your public API upload parser. Attached is our proof-of-concept. Please route to SecOps immediately.", "security"),
        ("Formal demand under EU GDPR Article 17: Delete all personally identifiable records for user account UUID 8912-3312 across all production and backup stores.", "legal"),
        ("Your 8-hour outage on April 14 breached section 4.2 of our Enterprise SLA. We are claiming $45,000 in contractual liquidated damages. Our legal counsel is CC'd.", "legal"),
        ("We have initiated a formal credit card chargeback dispute with our bank for $12,500 due to unauthorized billing.", "financial"),
        ("Security incident report: Unauthorized API key extraction detected from compromised worker node. Immediate key revocation and audit log retention required.", "security"),
        ("Cease and desist notice: Your platform is infringing upon registered trademark serial #88491024. Immediate removal required.", "legal"),
    ]
    for i in range(3):
        for tmpl, cat in high_risk_templates:
            if len(records) >= 205:
                break
            add_item(
                content=tmpl,
                task_type="high_risk_escalation",
                category=cat,
                acceptable_routes=["HUMAN_REVIEW"],
                expected_quality={"HUMAN_REVIEW": 1.0, "LARGE_LLM": 0.75, "SMALL_LLM": 0.20, "FAST_PATH": 0.00, "FALLBACK": 0.40, "CLARIFY": 0.10},
                notes="High-consequence compliance, financial, or security matter requiring human oversight",
            )

    # =========================================================================
    # 8. MALFORMED / UNROUTABLE (Target: FALLBACK) ~10 items
    # =========================================================================
    malformed_templates = [
        "0xDEADBEEF \x00\x01\x02 \x7f\x80\x90 \ufffd\ufffd\ufffd",
        "asdjklqwerty 981273918273981273 !@#$%^&*()_+",
        ";;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;",
        ">>> <<<< >>> ??? ???? !!!! *** &&&& %%%%",
        "qwpeoriuaskldfjzxcvm,n192837401928374",
    ]
    for tmpl in malformed_templates:
        add_item(
            content=tmpl,
            task_type="malformed_unroutable",
            category="malformed",
            acceptable_routes=["FALLBACK", "CLARIFY"],
            expected_quality={"FALLBACK": 1.0, "CLARIFY": 0.60, "LARGE_LLM": 0.10, "SMALL_LLM": 0.10, "FAST_PATH": 0.00, "HUMAN_REVIEW": 0.10},
            notes="Malformed non-linguistic input should trigger fallback handler",
        )

    return records


if __name__ == "__main__":
    items = generate_dataset()
    out_path = Path("datasets/customer_support_routing.json")
    out_path.write_text(json.dumps(items, indent=2), encoding="utf-8")
    dev_count = sum(1 for x in items if x["split"] == "dev")
    test_count = sum(1 for x in items if x["split"] == "test")
    print(f"Generated {len(items)} evaluation samples into {out_path}")
    print(f"Splits: {dev_count} dev (tuning/recon), {test_count} held-out test")
