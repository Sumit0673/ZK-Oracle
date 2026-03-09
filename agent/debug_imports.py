import langchain
print(f"LangChain version: {langchain.__version__}")

try:
    from langchain.agents import AgentExecutor
    print("Successfully imported AgentExecutor from langchain.agents")
except ImportError as e:
    print(f"Failed to import from langchain.agents: {e}")

try:
    from langchain.agents.agent import AgentExecutor
    print("Successfully imported AgentExecutor from langchain.agents.agent")
except ImportError as e:
    print(f"Failed to import from langchain.agents.agent: {e}")

try:
    from langchain_core.runnables import Runnable
    print("Successfully imported from langchain_core")
except ImportError as e:
    print(f"Failed to import from langchain_core: {e}")
