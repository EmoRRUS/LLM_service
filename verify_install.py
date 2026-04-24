
try:
    from langchain_ollama import ChatOllama
    with open("install_status.txt", "w") as f:
        f.write("SUCCESS: langchain-ollama is installed.")
except ImportError as e:
    with open("install_status.txt", "w") as f:
        f.write(f"FAILURE: {e}")
except Exception as e:
    with open("install_status.txt", "w") as f:
        f.write(f"ERROR: {e}")
