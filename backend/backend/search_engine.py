TOOLS = []

def search(tool_name):
    TOOLS.append(tool_name)

    return {
        "query": tool_name,
        "status": "received",
        "count": len(TOOLS)
    }
