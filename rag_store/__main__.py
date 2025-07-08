import typer
import uvicorn
import requests
import os

# --- Typer App ---
cli_app = typer.Typer(name="rag", help="RAG Store CLI for querying and data ingestion.")

# --- API 設定 ---
API_BASE_URL = "http://127.0.0.1:8000"

# --- CLI 指令 ---

@cli_app.command()
def query(
    question: str = typer.Argument(..., help="The question to ask the RAG system."),
):
    """
    Send a query to the RAG API and print the answer.
    """
    typer.echo(f"❓ Querying: {question}")
    try:
        response = requests.post(f"{API_BASE_URL}/query", json={"query": question})
        response.raise_for_status()
        
        data = response.json()
        typer.secho("\n✅ Answer:", fg=typer.colors.GREEN, bold=True)
        typer.echo(data['answer'])
        
        if data['sources']:
            typer.secho("\n📚 Sources:", fg=typer.colors.YELLOW)
            for i, source in enumerate(data['sources']):
                typer.echo(f"\n--- Source {i+1} ---")
                typer.echo(source['page_content'])
                typer.echo(f"Metadata: {source['metadata']}")

    except requests.exceptions.RequestException as e:
        typer.secho(f"Error connecting to API: {e}", fg=typer.colors.RED)
        typer.echo("Please make sure the RAG server is running. Use 'python -m rag_store serve'")

@cli_app.command()
def ingest(
    file_path: str = typer.Argument(..., help="Path to the file to ingest."),
):
    """
    Upload a file to the RAG API for ingestion.
    """
    if not os.path.exists(file_path):
        typer.secho(f"Error: File not found at '{file_path}'", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.echo(f"📦 Ingesting file: {file_path}")
    
    try:
        with open(file_path, "rb") as f:
            files = {'file': (os.path.basename(file_path), f)}
            response = requests.post(f"{API_BASE_URL}/upload", files=files)
            response.raise_for_status()
            
            data = response.json()
            typer.secho(f"✅ {data['message']}", fg=typer.colors.GREEN)
            typer.echo(f"   - Filename: {data['filename']}")
            typer.echo(f"   - Saved Path: {data['file_path']}")

    except requests.exceptions.RequestException as e:
        typer.secho(f"Error connecting to API: {e}", fg=typer.colors.RED)
        typer.echo("Please make sure the RAG server is running. Use 'python -m rag_store serve'")
    except Exception as e:
        typer.secho(f"An unexpected error occurred: {e}", fg=typer.colors.RED)


@cli_app.command(name="serve")
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind the server to."),
    port: int = typer.Option(8000, help="Port to listen on."),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reloading for development."),
):
    """
    Start the FastAPI web server.
    """
    typer.echo(f"🚀 Starting server at http://{host}:{port}")
    # 注意：這裡我們需要一種方式來引用 FastAPI app 物件。
    # 為了保持 CLI 和 Server 的分離，我們動態導入它。
    from .app.main import app
    if reload:
        uvicorn.run(
            "rag_store.app.main:app",
            host=host,
            port=port,
            reload=reload,
        )
    else:
        uvicorn.run(
            app,
            host=host,
            port=port,
        )

def main():
    # 為了讓 `python -m rag_store` 能運作，我們需要一個進入點。
    # Typer 的 app 物件本身就是一個可呼叫的物件。
    cli_app()

if __name__ == "__main__":
    main()