"""Custom LLM client for GLM API that handles reasoning_content format."""

import json
import logging
import re
from typing import Any

import openai
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

from graphiti_core.llm_client.config import DEFAULT_MAX_TOKENS, LLMConfig, ModelSize
from graphiti_core.llm_client.openai_generic_client import OpenAIGenericClient
from graphiti_core.prompts.models import Message

logger = logging.getLogger(__name__)

# Version marker for debugging - should appear in logs if module is loaded
logger.info("GLMClient v2 loaded - with ExtractedEdges fix")


def strip_markdown_code_blocks(text: str) -> str:
    """Remove markdown code blocks from text."""
    # Remove ```json ... ``` or ``` ... ``` blocks
    text = re.sub(r"^```(?:json)?\s*\n?", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n?```\s*$", "", text, flags=re.MULTILINE)
    return text.strip()


# Known field name variations for entity name
ENTITY_NAME_VARIATIONS = [
    "name",
    "entity_name",
    "entity",
    "entity_value",
    "entity_text",
    "node_name",
    "text",
]


class GLMClient(OpenAIGenericClient):
    """Custom OpenAI client for GLM API.

    GLM API returns responses in a non-standard format:
    1. content is empty but reasoning_content has data
    2. JSON may be wrapped in markdown code blocks
    3. Entity field names vary (entity_name, entity_text, etc.)

    This client handles all these issues.
    """

    @staticmethod
    def _fix_entity_fields(entities: list[dict]) -> list[dict]:
        """Fix entity field names to match graphiti's expected schema."""
        fixed_entities = []
        for item in entities:
            if not isinstance(item, dict):
                continue

            fixed_item = {}

            # Find the name field from various possible keys
            name_value = None
            for variant in ENTITY_NAME_VARIATIONS:
                if variant in item and item[variant]:
                    name_value = item[variant]
                    break

            if name_value:
                fixed_item["name"] = name_value
            else:
                # If no name found, skip this entity
                logger.warning(f"Could not find name field in entity: {item}")
                continue

            # Ensure entity_type_id exists
            fixed_item["entity_type_id"] = item.get("entity_type_id", 0)

            # Copy other fields
            for key, value in item.items():
                if key not in fixed_item:
                    fixed_item[key] = value

            fixed_entities.append(fixed_item)

        return fixed_entities

    @staticmethod
    def _fix_resolution_fields(resolutions: list[dict]) -> list[dict]:
        """Fix resolution field names to match graphiti's NodeDuplicate schema."""
        fixed_resolutions = []
        for item in resolutions:
            if not isinstance(item, dict):
                continue

            fixed_item = {}

            # Find the name field
            name_value = None
            for variant in ENTITY_NAME_VARIATIONS:
                if variant in item and item[variant]:
                    name_value = item[variant]
                    break

            if name_value:
                fixed_item["name"] = name_value
            else:
                logger.warning(f"Could not find name field in resolution: {item}")
                continue

            # id field (required)
            if "id" in item:
                fixed_item["id"] = item["id"]
            else:
                fixed_item["id"] = 0

            # duplicate_name field (required)
            if "duplicate_name" in item:
                fixed_item["duplicate_name"] = item["duplicate_name"]
            else:
                fixed_item["duplicate_name"] = ""

            # Copy other fields
            for key, value in item.items():
                if key not in fixed_item:
                    fixed_item[key] = value

            fixed_resolutions.append(fixed_item)

        return fixed_resolutions

    @staticmethod
    def _fix_edge_fields(edges: list[dict]) -> list[dict]:
        """Fix edge field names to match graphiti's Edge schema."""
        fixed_edges = []
        for item in edges:
            if not isinstance(item, dict):
                continue

            # Check if this looks like edge data
            if "source_entity_name" not in item and "target_entity_name" not in item:
                # Not edge data, skip
                continue

            fixed_item = {}

            # Required fields for Edge
            fixed_item["source_entity_name"] = item.get("source_entity_name", "")
            fixed_item["target_entity_name"] = item.get("target_entity_name", "")
            fixed_item["relation_type"] = item.get("relation_type", "RELATED_TO")
            fixed_item["fact"] = item.get("fact", "")

            # Optional fields
            fixed_item["valid_at"] = item.get("valid_at")
            fixed_item["invalid_at"] = item.get("invalid_at")

            # Copy other fields
            for key, value in item.items():
                if key not in fixed_item:
                    fixed_item[key] = value

            # Validate required fields
            if fixed_item["source_entity_name"] and fixed_item["target_entity_name"]:
                fixed_edges.append(fixed_item)

        return fixed_edges

    async def _generate_response(
        self,
        messages: list[Message],
        response_model: type[BaseModel] | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        model_size: ModelSize = ModelSize.medium,
    ) -> dict[str, Any]:
        """Override to handle GLM's quirks."""
        openai_messages: list[ChatCompletionMessageParam] = []
        for m in messages:
            m.content = self._clean_input(m.content)
            if m.role == "user":
                openai_messages.append({"role": "user", "content": m.content})
            elif m.role == "system":
                openai_messages.append({"role": "system", "content": m.content})

        try:
            # Prepare response format
            response_format: dict[str, Any] = {"type": "json_object"}
            if response_model is not None:
                schema_name = getattr(response_model, "__name__", "structured_response")
                json_schema = response_model.model_json_schema()
                response_format = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema_name,
                        "schema": json_schema,
                    },
                }

            # Build extra body with thinking disabled for GLM-5
            extra_body = {
                "thinking": {"type": "disabled"},
            }

            response = await self.client.chat.completions.create(
                model=self.model or "glm-5",
                messages=openai_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format=response_format,  # type: ignore[arg-type]
                extra_body=extra_body,  # type: ignore[arg-type]
            )

            # Extract content, handling GLM's reasoning_content format
            message = response.choices[0].message
            result = message.content or ""

            # GLM-specific: if content is empty, try reasoning_content
            if not result and hasattr(message, "model_extra") and message.model_extra:
                reasoning_content = message.model_extra.get("reasoning_content", "")
                if reasoning_content:
                    logger.debug("GLM: Using reasoning_content instead of empty content")
                    result = reasoning_content

            # Also try to get from raw response if available
            if not result:
                try:
                    raw_response = response.model_dump()
                    choices = raw_response.get("choices", [])
                    if choices:
                        msg = choices[0].get("message", {})
                        result = msg.get("content", "") or msg.get("reasoning_content", "")
                        if result:
                            logger.debug("GLM: Extracted from raw response")
                except Exception as e:
                    logger.debug(f"Could not access raw response: {e}")

            if not result:
                raise ValueError("GLM returned empty content and reasoning_content")

            # Strip markdown code blocks if present
            result = strip_markdown_code_blocks(result)

            # Try to parse as JSON
            try:
                parsed = json.loads(result)

                # GLM sometimes returns a list instead of a dict
                # Fix the format to match graphiti's expected schema
                if isinstance(parsed, list):
                    logger.debug("GLM returned a list, converting to expected format")

                    # Detect what type of data is in the list
                    is_edge_data = False
                    if parsed and isinstance(parsed[0], dict):
                        is_edge_data = "source_entity_name" in parsed[0] or "target_entity_name" in parsed[0]

                    # Check response_model to determine expected format
                    if response_model and hasattr(response_model, "model_fields"):
                        fields = response_model.model_fields

                        # ExtractedEdges expects edges
                        if "edges" in fields:
                            if is_edge_data:
                                return {"edges": self._fix_edge_fields(parsed)}
                            else:
                                # Empty list or wrong format
                                return {"edges": []}

                        # NodeResolutions expects entity_resolutions
                        if "entity_resolutions" in fields:
                            return {"entity_resolutions": self._fix_resolution_fields(parsed)}

                    # Default: ExtractedEntities
                    if is_edge_data:
                        # Edge data but model expects entities - return empty
                        logger.warning("GLM returned edge data but expected entities")
                        return {"extracted_entities": []}
                    fixed_entities = self._fix_entity_fields(parsed)
                    return {"extracted_entities": fixed_entities}

                # Handle dict with wrong keys
                if isinstance(parsed, dict):
                    # Debug: log response_model info
                    if response_model:
                        logger.debug(f"GLM: response_model={response_model.__name__}, fields={list(response_model.model_fields.keys())}")
                    else:
                        logger.debug("GLM: No response_model provided")

                    # Fix extracted_entities field names
                    if "extracted_entities" in parsed:
                        parsed["extracted_entities"] = self._fix_entity_fields(parsed["extracted_entities"])

                    # Fix entities -> extracted_entities
                    if "entities" in parsed and "extracted_entities" not in parsed:
                        parsed["extracted_entities"] = self._fix_entity_fields(parsed.pop("entities"))

                    # Fix entity_resolutions field names
                    if "entity_resolutions" in parsed:
                        parsed["entity_resolutions"] = self._fix_resolution_fields(parsed["entity_resolutions"])

                    # Fix extracted_entities -> entity_resolutions (for NodeResolutions)
                    if response_model and hasattr(response_model, "model_fields"):
                        fields = response_model.model_fields
                        if "entity_resolutions" in fields and "extracted_entities" in parsed:
                            # Move extracted_entities to entity_resolutions
                            parsed["entity_resolutions"] = self._fix_resolution_fields(parsed.pop("extracted_entities"))

                        # Handle ExtractedEdges - convert extracted_entities with edge fields to edges
                        if "edges" in fields:
                            logger.debug(f"GLM: Detected ExtractedEdges model, parsed keys: {list(parsed.keys())}")
                            # Check if extracted_entities contains edge data
                            if "extracted_entities" in parsed:
                                entities = parsed["extracted_entities"]
                                logger.debug(f"GLM: found extracted_entities, len={len(entities)}")
                                # Handle non-empty list with edge data
                                if entities and isinstance(entities, list) and isinstance(entities[0], dict):
                                    if "source_entity_name" in entities[0] or "target_entity_name" in entities[0]:
                                        # This is edge data, not entity data
                                        parsed["edges"] = self._fix_edge_fields(parsed.pop("extracted_entities"))
                                        logger.debug(f"GLM: Converted extracted_entities to edges (non-empty)")
                                else:
                                    # Empty list or wrong format - set edges to empty
                                    parsed["edges"] = []
                                    parsed.pop("extracted_entities", None)
                                    logger.debug("GLM: Set edges=[] for empty extracted_entities")

                    # Ensure edges field exists for ExtractedEdges (final fallback)
                    if "edges" not in parsed and response_model and hasattr(response_model, "model_fields"):
                        if "edges" in response_model.model_fields:
                            parsed["edges"] = []

                return parsed
            except json.JSONDecodeError as e:
                logger.warning(f"GLM response is not valid JSON after stripping: {result[:200]}...")
                raise ValueError(f"GLM response is not valid JSON: {e}") from e

        except openai.RateLimitError as e:
            from graphiti_core.llm_client.errors import RateLimitError

            raise RateLimitError from e
        except Exception as e:
            logger.error(f"Error in GLM response generation: {e}")
            raise
