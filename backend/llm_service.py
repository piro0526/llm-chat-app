from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.agents import AgentType, initialize_agent, create_tool_calling_agent
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import AgentExecutor
from models import LLMSetting
from config import settings
from mcp_tools import mcp_registry
from mcp_client import get_mcp_client, get_mcp_server_manager
import json


class LLMService:
    def __init__(self):
        self.models = {}
    
    def get_model(self, provider: str, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """Get LLM model instance based on provider"""
        if provider == "openai":
            return ChatOpenAI(
                api_key=api_key or settings.openai_api_key,
                model=model_name or "gpt-3.5-turbo"
            )
        elif provider == "claude":
            return ChatAnthropic(
                api_key=api_key or settings.anthropic_api_key,
                model=model_name or "claude-3-sonnet-20240229"
            )
        elif provider == "gemini":
            return ChatGoogleGenerativeAI(
                google_api_key=api_key or settings.google_api_key,
                model=model_name or "gemini-pro"
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
        tools: Optional[list] = None
    ) -> str:
        """Generate response from LLM with MCP tool integration"""
        try:
            model = self.get_model(provider, api_key, model_name)
            
            # Prepare messages
            messages = []
            
            # Add system message for MCP tools awareness
            system_msg = """You are an AI assistant with access to various tools through the Model Context Protocol (MCP).
You can help with document analysis, research assistance, file operations, and web searches.
When a user's request could benefit from using a tool, analyze the request and use the appropriate tool.
Always explain what you're doing when using tools."""
            messages.append(SystemMessage(content=system_msg))
            
            if chat_history:
                for log in chat_history:
                    if log.role == "user":
                        messages.append(HumanMessage(content=log.content))
                    else:
                        messages.append(AIMessage(content=log.content))
            
            messages.append(HumanMessage(content=message))
            
            # Get MCP tools
            mcp_tools = await self.get_mcp_tools()
            
            # Combine legacy tools with MCP tools
            all_tools = (tools or []) + mcp_tools
            
            if all_tools:
                # Create agent with tools
                if provider == "openai":
                    # Use tool calling agent for OpenAI
                    prompt = ChatPromptTemplate.from_messages([
                        ("system", system_msg),
                        ("placeholder", "{chat_history}"),
                        ("human", "{input}"),
                        ("placeholder", "{agent_scratchpad}"),
                    ])
                    
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
                    
                    response = await agent_executor.ainvoke({
                        "input": message,
                        "chat_history": chat_history_msgs
                    })
                    return response["output"]
                else:
                    # Fallback to simple agent for other providers
                    agent = initialize_agent(
                        all_tools,
                        model,
                        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                        verbose=True,
                        handle_parsing_errors=True
                    )
                    response = await agent.arun(message)
                    return response
            else:
                # No tools, direct model invocation
                response_msg = await model.ainvoke(messages)
                return response_msg.content
            
        except Exception as e:
            raise Exception(f"Error generating response: {str(e)}")
    
    async def get_mcp_tools(self) -> List[Tool]:
        """Get available MCP tools as LangChain tools"""
        langchain_tools = []
        
        try:
            # Get MCP server manager instance
            server_manager = get_mcp_server_manager()
            mcp_tools = server_manager.get_all_tools()
            
            for tool_spec in mcp_tools:
                try:
                    # Create LangChain Tool from MCP tool spec
                    def create_tool_func(server_name: str, tool_name: str, full_name: str):
                        async def tool_func(input_str: str) -> str:
                            try:
                                # Parse input as JSON if it looks like JSON, otherwise use as string
                                if input_str.strip().startswith('{'):
                                    arguments = json.loads(input_str)
                                else:
                                    # For simple string inputs, create a generic parameter
                                    arguments = {"input": input_str}
                                
                                manager = get_mcp_server_manager()
                                result = await manager.call_tool(server_name, tool_name, arguments)
                                return result
                            except Exception as e:
                                return f"Error executing {full_name}: {str(e)}"
                        return tool_func
                    
                    langchain_tool = Tool(
                        name=tool_spec["full_name"],
                        description=f"{tool_spec['description']}\nServer: {tool_spec['server']}\nInput schema: {json.dumps(tool_spec['input_schema'])}",
                        func=create_tool_func(tool_spec["server"], tool_spec["name"], tool_spec["full_name"]),
                        coroutine=create_tool_func(tool_spec["server"], tool_spec["name"], tool_spec["full_name"])
                    )
                    langchain_tools.append(langchain_tool)
                except Exception as e:
                    print(f"Error creating MCP tool {tool_spec['full_name']}: {e}")
            
            # Also add legacy tools from registry
            legacy_tools = mcp_registry.get_all_tools()
            for tool_spec in legacy_tools:
                try:
                    def create_legacy_func(tool_name: str):
                        def legacy_func(input_str: str) -> str:
                            try:
                                if input_str.strip().startswith('{'):
                                    arguments = json.loads(input_str)
                                else:
                                    arguments = {"input": input_str}
                                return mcp_registry.execute_tool(tool_name, arguments)
                            except Exception as e:
                                return f"Error executing {tool_name}: {str(e)}"
                        return legacy_func
                    
                    langchain_tool = Tool(
                        name=f"legacy_{tool_spec.name}",
                        description=tool_spec.description,
                        func=create_legacy_func(tool_spec.name)
                    )
                    langchain_tools.append(langchain_tool)
                except Exception as e:
                    print(f"Error creating legacy tool {tool_spec.name}: {e}")
                    
        except Exception as e:
            print(f"Error getting MCP tools: {e}")
            # Fallback to legacy tools only
            legacy_tools = mcp_registry.get_all_tools()
            for tool_spec in legacy_tools:
                try:
                    def create_fallback_func(tool_name: str):
                        def fallback_func(input_str: str) -> str:
                            try:
                                if input_str.strip().startswith('{'):
                                    arguments = json.loads(input_str)
                                else:
                                    arguments = {"input": input_str}
                                return mcp_registry.execute_tool(tool_name, arguments)
                            except Exception as e:
                                return f"Error executing {tool_name}: {str(e)}"
                        return fallback_func
                    
                    langchain_tool = Tool(
                        name=tool_spec.name,
                        description=tool_spec.description,
                        func=create_fallback_func(tool_spec.name)
                    )
                    langchain_tools.append(langchain_tool)
                except Exception as e:
                    print(f"Error creating fallback tool {tool_spec.name}: {e}")
        
        return langchain_tools


llm_service = LLMService()