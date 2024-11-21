# ecommerce-ai-assistant/core/assistant/base.py
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime

from app.config import settings
from utils.logger import get_logger
from core.metadata import SchemaRegistry
from core.sql import SQLGenerator, SQLValidator
from core.bigquery import BigQueryClient
from .memory import ConversationMemory
from .router import QueryRouter

class AssistantManager:
    """
    Core AI Assistant manager that handles query processing,
    memory management, and response generation.
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.memory = ConversationMemory()
        self.schema_registry = SchemaRegistry()
        self.sql_generator = SQLGenerator(self.schema_registry)
        self.sql_validator = SQLValidator(self.schema_registry)
        self.bq_client = BigQueryClient()
        self.query_router = QueryRouter()
        
    async def initialize(self) -> None:
        """Initialize all components."""
        try:
            await self.schema_registry.initialize()
            await self.bq_client.initialize()
            self.logger.info("Assistant manager initialized successfully")
        except Exception as e:
            self.logger.error(
                "Failed to initialize assistant manager",
                error=str(e),
                exc_info=True
            )
            raise
    
    async def process_message(
        self,
        message: str,
        conversation_id: str,
        active_platforms: Set[str],
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Process a user message and generate a response.
        
        Args:
            message: User's message
            conversation_id: Unique conversation identifier
            active_platforms: Set of active e-commerce platforms
            context: Additional context for processing
            
        Returns:
            Dict containing response and metadata
        """
        try:
            # Log message processing
            self.logger.info(
                "Processing message",
                conversation_id=conversation_id,
                message_length=len(message),
                platforms=list(active_platforms)
            )
            
            # Update conversation memory
            self.memory.add_message(conversation_id, "user", message)
            
            # Determine query type and required tables
            query_type = await self.query_router.classify_query(message)
            
            # Generate SQL query if appropriate
            if query_type:
                response = await self._handle_data_query(
                    message=message,
                    query_type=query_type,
                    active_platforms=active_platforms,
                    context=context
                )
            else:
                response = await self._handle_general_query(
                    message=message,
                    conversation_id=conversation_id
                )
            
            # Add to conversation memory
            self.memory.add_message(
                conversation_id,
                "assistant",
                response["message"]
            )
            
            return response
            
        except Exception as e:
            self.logger.error(
                "Error processing message",
                error=str(e),
                conversation_id=conversation_id,
                exc_info=True
            )
            raise
    
    async def _handle_data_query(
        self,
        message: str,
        query_type: str,
        active_platforms: Set[str],
        context: Optional[Dict] = None
    ) -> Dict:
        """Handle queries that require data access."""
        try:
            # Generate SQL query
            sql_query, params, tables = await self.sql_generator.generate_query(
                text=message,
                platforms=active_platforms,
                query_type=query_type
            )
            
            # Validate query
            is_valid, error = await self.sql_validator.validate_query(
                sql_query,
                params
            )
            
            if not is_valid:
                raise ValueError(f"Invalid query: {error}")
            
            # Execute query
            results = await self.bq_client.execute_query(
                sql_query,
                params
            )
            
            # Generate natural language response
            response_text = await self._generate_response(
                message,
                results,
                query_type
            )
            
            return {
                "message": response_text,
                "sql_query": sql_query,
                "results": results,
                "query_type": query_type,
                "tables_used": tables,
                "metadata": {
                    "platforms": list(active_platforms),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(
                "Error handling data query",
                error=str(e),
                query_type=query_type,
                exc_info=True
            )
            raise
    
    async def _handle_general_query(
        self,
        message: str,
        conversation_id: str
    ) -> Dict:
        """Handle general conversation queries."""
        try:
            # Get conversation context
            context = self.memory.get_context(conversation_id)
            
            # Generate response
            response_text = await self._generate_general_response(
                message,
                context
            )
            
            return {
                "message": response_text,
                "query_type": "general",
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "context_length": len(context)
                }
            }
            
        except Exception as e:
            self.logger.error(
                "Error handling general query",
                error=str(e),
                conversation_id=conversation_id,
                exc_info=True
            )
            raise
    
    async def _generate_response(
        self,
        query: str,
        results: List[Dict],
        query_type: str
    ) -> str:
        """Generate natural language response from query results."""
        try:
            if not results:
                return "I found no data matching your query."
            
            # Get response template
            template = self.schema_registry.get_response_template(query_type)
            
            # Format results
            formatted_results = self._format_results(results, query_type)
            
            # Generate response using template
            response = template.format(**formatted_results)
            
            return response
            
        except Exception as e:
            self.logger.error(
                "Error generating response",
                error=str(e),
                exc_info=True
            )
            raise
    
    async def _generate_general_response(
        self,
        message: str,
        context: List[Dict]
    ) -> str:
        """Generate response for general queries."""
        # Implement general response logic
        # This could use a different LLM model or template system
        return "I understand you're asking a general question. [Response logic to be implemented]"
    
    def _format_results(
        self,
        results: List[Dict],
        query_type: str
    ) -> Dict:
        """Format query results for response generation."""
        formatted = {}
        
        if query_type == "sales":
            total_sales = sum(row.get("total_sales", 0) for row in results)
            formatted["total_sales"] = f"${total_sales:,.2f}"
            
            by_platform = {}
            for row in results:
                if "platform" in row and "total_sales" in row:
                    by_platform[row["platform"]] = f"${row['total_sales']:,.2f}"
            formatted["by_platform"] = by_platform
            
        # Add more query type formatters as needed
        
        return formatted

    async def close(self) -> None:
        """Clean up resources."""
        await self.bq_client.close()
        self.logger.info("Assistant manager closed")