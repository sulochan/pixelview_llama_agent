import asyncio
import json
import os
import textwrap
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional

from mongo import AlertsDataTool
from common.client_utils import *
from dotenv import load_dotenv
from llama_stack_client import LlamaStackClient
from llama_stack_client.lib.agents.event_logger import EventLogger
from llama_stack_client.types import Attachment, SamplingParams, UserMessage
from llama_stack_client.types.agent_create_params import (
    AgentConfig,
    AgentConfigToolMemoryToolDefinition,
    AgentConfigToolMemoryToolDefinitionMemoryBankConfigUnionMember0,
    AgentConfigToolSearchToolDefinition,
)
from llama_stack_client.types.agents.agents_turn_stream_chunk import (
    AgentsTurnStreamChunk,
)
from llama_stack_client.types.memory_insert_params import Document

from utils import data_url_from_file

load_dotenv()


class Agent:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.agent_id = None
        self.session_id = None
        self.client = LlamaStackClient(
            base_url=f"http://{host}:{port}",
        )
        self.tool_definitions = [AlertsDataTool()]
        self.agent_config = None

    async def async_init(self):
        # Move the async part here
        self.agent_config = await make_agent_config_with_custom_tools(
            model="Llama3.1-8B-Instruct",
            tool_config=QuickToolConfig(
                custom_tools=self.tool_definitions,
                prompt_format="function_tag",
            ),
            disable_safety=True,
        )

    async def create_agent(self, agent_config: AgentConfig):
        agentic_system_create_response = self.client.agents.create(
            agent_config=agent_config,
        )
        self.agent_id = agentic_system_create_response.agent_id
        agentic_system_create_session_response = self.client.agents.session.create(
            agent_id=agentic_system_create_response.agent_id,
            session_name="test_session",
        )
        self.session_id = agentic_system_create_session_response.session_id
        return AgentWithCustomToolExecutor(
            self.client,
            self.agent_id,
            self.session_id,
            agent_config,
            self.tool_definitions,
        )
