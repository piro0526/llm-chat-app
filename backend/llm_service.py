from typing import Annotated, Optional, Sequence

from config import settings
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from mcp import get_mcp_tools


class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


class LLMService:
    def __init__(self):
        self.models = {}
        self.graphs = {}

    def get_model(self, provider: str, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """Get LLM model instance based on provider"""
        if provider == "openai":
            return ChatOpenAI(api_key=api_key or settings.openai_api_key, model=model_name or "gpt-3.5-turbo")
        elif provider == "claude":
            return ChatAnthropic(
                api_key=api_key or settings.anthropic_api_key, model=model_name or "claude-3-sonnet-20240229"
            )
        elif provider == "gemini":
            return ChatGoogleGenerativeAI(
                google_api_key=api_key or settings.google_api_key, model=model_name or "gemini-pro"
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def create_graph(self, model, tools):
        """Create LangGraph workflow"""
        def should_continue(state: State) -> str:
            messages = state["messages"]
            last_message = messages[-1]
            if last_message.tool_calls:
                return "tools"
            return END

        def call_model(state: State):
            messages = state["messages"]
            response = model.invoke(messages)
            return {"messages": [response]}

        workflow = StateGraph(State)
        workflow.add_node("agent", call_model)
        if tools:
            workflow.add_node("tools", ToolNode(tools))
            workflow.add_edge(START, "agent")
            workflow.add_conditional_edges("agent", should_continue, ["tools", END])
            workflow.add_edge("tools", "agent")
        else:
            workflow.add_edge(START, "agent")
            workflow.add_edge("agent", END)

        return workflow.compile()

    async def generate_response(
        self,
        message: str,
        provider: str,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        chat_history: Optional[list] = None,
        tools: Optional[list] = None,
    ) -> str:
        """Generate response from LLM with MCP tool integration using LangGraph"""
        try:
            model = self.get_model(provider, api_key, model_name)

            # Get MCP tools
            mcp_tools = get_mcp_tools()

            # Combine provided tools with MCP tools
            all_tools = (tools or []) + mcp_tools

            # Bind tools to model if available
            if all_tools:
                model = model.bind_tools(all_tools)

            # Create or get cached graph
            graph_key = f"{provider}_{model_name}_{len(all_tools)}"
            if graph_key not in self.graphs:
                self.graphs[graph_key] = self.create_graph(model, all_tools)
            
            graph = self.graphs[graph_key]

            # Prepare messages
            messages = []

            # Add system message for MCP tools awareness
            system_msg = (
                "You are an AI assistant with access to various tools through the Model Context Protocol (MCP). "
                "You can help with document analysis, research assistance, file operations, and web searches. "
                "When a user's request could benefit from using a tool, analyze the request and use the appropriate tool. "
                "Always explain what you're doing when using tools."
            )
            messages.append(SystemMessage(content=system_msg))

            # Add chat history
            if chat_history:
                for log in chat_history:
                    if log.role == "user":
                        messages.append(HumanMessage(content=log.content))
                    else:
                        messages.append(AIMessage(content=log.content))

            # Add current message
            messages.append(HumanMessage(content=message))

            # Execute the graph
            result = await graph.ainvoke({"messages": messages})
            
            # Extract the final response
            final_message = result["messages"][-1]
            return final_message.content

        except Exception as e:
            raise Exception(f"Error generating response: {str(e)}")


llm_service = LLMService()
