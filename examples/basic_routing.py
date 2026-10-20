"""Basic routing example demonstrating how to use SlothSwitch in Python."""

from slothswitch.api import create_router
from slothswitch.schemas import RoutingRequest


def main() -> None:
    # 1. Initialize the router from the default config
    router = create_router("config/routing.yaml")
    print("SlothSwitch Router initialized successfully!\n")

    # 2. Example queries covering various scenarios
    queries = [
        "What are your business operating hours?",
        "How do I reset my password?",
        "Can you help me design a multi-region distributed Kafka cluster with CDC in Go?",
        "Please delete all my personal data under GDPR Right to Erasure.",
        "asdjklasdj 123 !@#$",
    ]

    for i, text in enumerate(queries, 1):
        print(f"--- Query {i} ---")
        print(f"Content: {text}")

        # Construct typed request
        request = RoutingRequest(
            request_id=f"example-{i:03d}",
            content=text,
        )

        # Process through the router
        record = router.process(request)
        decision = record.route_decision
        result = record.task_result

        print(f"Chosen Route: {decision.chosen_route.value}")
        print(f"Confidence:   {decision.confidence}")
        print(f"Accepted:     {decision.accepted}")
        print(f"Reasoning:    {decision.reasoning}")
        if result:
            print(f"Output:       {result.output}")
        print()


if __name__ == "__main__":
    main()
