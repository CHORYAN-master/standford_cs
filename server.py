# My First MCP Server

from mcp.server.fastmcp import FastMCP

# 1. 서버 이름 설정 (AI가 식별할 이름)
mcp = FastMCP("My Desktop Assistant")

# 2. 기능 만들기: AI가 사용할 도구(Tool) 정의
@mcp.tool()
def add_two_numbers(a: int, b: int) -> int:
    """Add two numbers together. Use this for basic math."""
    return a + b

@mcp.tool()
def list_files(directory: str = ".") -> str:
    """List all files in the given directory."""
    import os
    try:
        files = os.listdir(directory)
        return "\n".join(sorted(files))
    except FileNotFoundError:
        return f"Error: Directory not found: {directory}"
    except PermissionError:
        return f"Error: Permission denied accessing: {directory}"
    except Exception as e:
        return f"Error reading directory: {str(e)}"

# 3. 서버 실행 (터미널에서 이 파일을 실행하면 작동 시작)
if __name__ == "__main__":
    mcp.run()
@mcp.tool()
def check_status() -> str:
    return "Server is running perfectly!"
