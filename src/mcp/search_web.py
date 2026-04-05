import requests

def search_web(query: str, sources: list, limit: int) -> dict:
    """
    调用通用搜索接口

    参数:
        query: 搜索关键词（必填）
        sources: 搜索源列表，可选值["baidu", "bing", "csdn", "duckduckgo", "sogou", "so"]
        limit: 每个搜索源返回结果数量，1-50

    返回:
        接口响应字典
    """
    # 接口地址
    url = "http://122.51.226.99:3000/websearch/api/search"

    # 请求头（API Key 固定写在这里，不再作为参数）
    headers = {
        "x-api-key": "open-websearch-key-2026",
        "Content-Type": "application/json"
    }

    # 请求体
    payload = {
        "query": query,
        "sources": sources,
        "limit": limit
    }

    try:
        response = requests.post(
            url=url,
            headers=headers,
            json=payload,
            timeout=30,
            verify=False
        )

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        return {
            "code": 500,
            "message": f"请求失败: {str(e)}",
            "data": None
        }


# ===================== 工具定义（已移除 api_key） =====================
search_web_tool = {
    "name": "web_search",
    "description": "联网搜索接口，支持多平台关键词搜索",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键词"},
            "sources": {
                "type": "array",
                "items": {"type":"string"},
                "description": "搜索源列表，可选：baidu、bing、csdn、duckduckgo、sogou、so"
            },
            "limit": {"type": "number", "description": "每个搜索源返回结果数量，1-50"}
        },
        "required": ["query", "sources", "limit"]
    },
    "func": search_web
}

# # ===================== 使用示例 =====================
# if __name__ == "__main__":
#     result = search_web(
#         query="Python 实战教程",
#         sources=["baidu", "csdn"],
#         limit=10
#     )

#     import json
#     print(json.dumps(result, ensure_ascii=False, indent=2))