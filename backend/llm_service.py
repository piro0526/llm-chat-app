from typing import Optional

from config import settings
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from backend.mcp import get_mcp_tools


class LLMService:
    def __init__(self):
        self.models = {}

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

    async def generate_response(
        self,
        message: str,
        provider: str,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        chat_history: Optional[list] = None,
        tools: Optional[list] = None,
    ) -> str:
        """Generate response from LLM with MCP tool integration"""
        try:
            model = self.get_model(provider, api_key, model_name)

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

            if chat_history:
                for log in chat_history:
                    if log.role == "user":
                        messages.append(HumanMessage(content=log.content))
                    else:
                        messages.append(AIMessage(content=log.content))

            messages.append(HumanMessage(content=message))

            # TODO: mcpに対応したツールを追加する
            # Get MCP tools
            mcp_tools = get_mcp_tools()

            # Combine provided tools with MCP tools
            all_tools = (tools or []) + mcp_tools

            if all_tools:
                # Use tool calling agent for OpenAI
                prompt = ChatPromptTemplate.from_messages(
                    [
                        ("system", system_msg),
                        ("placeholder", "{chat_history}"),
                        ("human", "{input}"),
                        ("placeholder", "{agent_scratchpad}"),
                    ]
                )

                agent = create_tool_calling_agent(model, all_tools, prompt)
                agent_executor = AgentExecutor(agent=agent, tools=all_tools, verbose=True)

                # Prepare chat history for agent
                chat_history_msgs = []
                if chat_history:
                    for log in chat_history:
                        if log.role == "user":
                            chat_history_msgs.append(HumanMessage(content=log.content))
                        else:
                            chat_history_msgs.append(AIMessage(content=log.content))

                response = await agent_executor.ainvoke({"input": message, "chat_history": chat_history_msgs})
                return response["output"]
            else:
                # No tools, direct model invocation
                response_msg = await model.ainvoke(messages)
                return response_msg.content

        except Exception as e:
            raise Exception(f"Error generating response: {str(e)}")


llm_service = LLMService()
