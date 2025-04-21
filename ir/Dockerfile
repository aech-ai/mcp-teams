FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir "mcp[cli]>=1.2.0" fastapi uvicorn

# Copy application code
COPY . /app/

# Create a script to run an HTTP API server with FastAPI
RUN echo '#!/usr/bin/env python3\nimport uvicorn\nfrom fastapi import FastAPI, Request, Response\nimport json\nimport logging\n\nlogging.basicConfig(level=logging.INFO)\nlogger = logging.getLogger(__name__)\n\napp = FastAPI()\n\n@app.get("/")\ndef health_check():\n    return {"status": "ok", "message": "IR server is running"}\n\n@app.get("/api/tools")\ndef list_tools():\n    return {"tools": ["search", "index_content", "index_teams_messages", "get_content_count", "delete_content"]}\n\n@app.post("/api/tools/{tool_name}")\nasync def call_tool(tool_name: str, request: Request):\n    try:\n        logger.info(f"Tool call received: {tool_name}")\n        content = await request.json()\n        logger.info(f"Tool parameters: {content}")\n        \n        if tool_name == "search":\n            query = content.get("query", "")\n            search_type = content.get("search_type", "hybrid")\n            limit = content.get("limit", 10)\n            logger.info(f"Search request: query={query}, type={search_type}, limit={limit}")\n            return {\n                "result": {\n                    "results": [\n                        {\n                            "id": "result-1",\n                            "content": f"This is a simulated search result for: {query}",\n                            "score": 0.95,\n                            "metadata": {"source": "teams", "created": "2025-04-01T12:00:00Z"}\n                        },\n                        {\n                            "id": "result-2", \n                            "content": f"Another result matching: {query}",\n                            "score": 0.82,\n                            "metadata": {"source": "teams", "created": "2025-03-28T15:30:00Z"}\n                        }\n                    ],\n                    "metadata": {\n                        "total_results": 2,\n                        "search_type": search_type\n                    }\n                }\n            }\n        elif tool_name == "index_content":\n            content_text = content.get("content", "")\n            source_type = content.get("source_type", "")\n            metadata = content.get("metadata", {})\n            logger.info(f"Indexing content: source_type={source_type}, length={len(content_text)}")\n            return {\n                "result": {\n                    "status": "success",\n                    "indexed_id": f"doc-{hash(content_text) % 10000}",\n                    "source_type": source_type\n                }\n            }\n        elif tool_name == "get_content_count":\n            source_type = content.get("source_type")\n            logger.info(f"Content count request: source_type={source_type}")\n            return {\n                "result": {\n                    "total": 1250,\n                    "by_source": {\n                        "teams": 1142,\n                        "email": 108\n                    }\n                }\n            }\n        else:\n            return {\n                "result": {\n                    "status": "success", \n                    "tool": tool_name,\n                    "parameters": content,\n                    "message": "Simulated tool response"\n                }\n            }\n    except Exception as e:\n        logger.error(f"Error processing tool call: {e}")\n        return {"error": str(e)}\n\nif __name__ == "__main__":\n    logger.info("Starting FastAPI server on 0.0.0.0:8090")\n    uvicorn.run(app, host="0.0.0.0", port=8090)' > /app/start_server.py \
    && chmod +x /app/start_server.py

# Set Python path to include parent directory
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Set environment variables with default values
ENV MCP_SERVER_PORT=8090
ENV MCP_SERVER_HOST="0.0.0.0"
ENV PORT=8090
ENV HOST="0.0.0.0"
ENV MCP_HTTP=1

# Create a non-root user to run the application
RUN useradd -m appuser
USER appuser

# Expose port for MCP server
EXPOSE 8090

# Start the MCP IR server with minimal script
CMD ["python", "/app/start_server.py"]