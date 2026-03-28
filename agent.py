import asyncio
from config import get_model
from pydantic_deep import create_deep_agent, DeepAgentDeps
from pydantic_ai.tools import (
    DeferredToolRequests,
    DeferredToolResults,
    ToolApproved,
    ToolDenied,
)

from pydantic_ai_backends import LocalBackend


backend = LocalBackend("./back")


async def main():
    agent = create_deep_agent(
        model=get_model(),
        instructions="You are a helpful coding assistant.",
        interrupt_on={"write_file": True, "edit_file": True},
        skill_directories=[{"path": "./skills", "recursive": True}],
        include_skills=True
    )

    deps = DeepAgentDeps(backend=backend)

    while True:
        user_input = input("\nTy: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Papa")
            break

        result = await agent.run(user_input, deps=deps)

        # Obsługa DeferredToolRequests
        while isinstance(result.output, DeferredToolRequests):
            approvals = {}

            for call in result.output.approvals:
                print(f"\n⏳ {call.tool_name}: {call.args}")
                odp = input("Pozwolić? [y/n]: ").lower()

                if odp == "y":
                    approvals[call.tool_call_id] = ToolApproved()
                else:
                    approvals[call.tool_call_id] = ToolDenied(
                        message="Odrzucone przez użytkownika"
                    )

            # Kontynuuj z decyzjami
            result = await agent.run(
                None,
                deps=deps,
                message_history=result.all_messages(),
                deferred_tool_results=DeferredToolResults(approvals=approvals),
            )

        print(f"\nAgent: {result.output}")


asyncio.run(main())
