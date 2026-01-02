import typer

app = typer.Typer()

@app.command()
def scaffold(template_path: str):
    
    print(f"Lecture du template : {template_path}")
    # Logique à venir

if __name__ == "__main__":
    app()