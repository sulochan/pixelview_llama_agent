import os
import json
from bson import json_util
from typing import Dict

from motor.motor_asyncio import AsyncIOMotorClient
from common.custom_tools import SingleMessageCustomTool
from llama_stack_client.types.tool_param_definition_param import (
    ToolParamDefinitionParam,
)


class AlertsDataTool(SingleMessageCustomTool):
    """Tool to get alerts data from MongoDB"""

    def get_name(self) -> str:
        return "get_alerts_data"

    def get_description(self) -> str:
        return "Get alerts data from database"

    def get_params_definition(self) -> Dict[str, ToolParamDefinitionParam]:
        return {
            "status": ToolParamDefinitionParam(
                param_type="str",
                description="Status",
                required=True,
            ),
        }

    async def run_impl(self, status: str, *args, **kwargs):
        # Connect to MongoDB
        try:
            print("Connecting to MongoDB", os.getenv("MONGODB_URI"))
            client = AsyncIOMotorClient(os.getenv("MONGODB_URI"), connectTimeoutMS=3000, serverSelectionTimeoutMS=3000, socketTimeoutMS=5000)
            db = client["alertagility"]
            collection = db["alertagility_alerts"]
        except Exception:
            print("Error connecting to MongoDB. Cant fetch alerts data.")
            response = "Error connecting to MongoDB. Cant fetch alerts data."
            return response

        # Query the MongoDB collection
        query = {"status": status}
        projection = {"_id": 0}
        try:
            cursor = collection.find(query, projection)
            result = await cursor.to_list(length=None)
            result_serialized = json.loads(json_util.dumps(result))
        except Exception as e:
            result_serialized = [str(e)]

        return result_serialized
