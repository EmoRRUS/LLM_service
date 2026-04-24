
import requests
import json

def check_ollama():
    print("="*60)
    print("DIAGNOSTIC: Checking Ollama Connection")
    print("="*60)
    
    base_url = "http://localhost:11434"
    
    # 1. Check if Server is UP
    try:
        print(f"\n[1] Pinging {base_url}...")
        response = requests.get(base_url)
        if response.status_code == 200:
            print("    ✅ SUCCESS: Ollama is running.")
        else:
            print(f"    ❌ FAILURE: Server responded with {response.status_code}")
    except Exception as e:
        print(f"    ❌ FAILURE: Could not connect. Is the Ollama app open? ({e})")
        return

    # 2. Check installed models
    try:
        print(f"\n[2] Checking for 'phi3' model...")
        response = requests.get(f"{base_url}/api/tags")
        models = response.json().get('models', [])
        
        found = False
        print("    Installed models:")
        for m in models:
            name = m.get('name', 'unknown')
            print(f"    - {name}")
            if 'phi3' in name:
                found = True
        
        if found:
            print("\n    ✅ SUCCESS: 'phi3' model found.")
        else:
            print("\n    ❌ FAILURE: 'phi3' model NOT found.")
            print("       Run this in terminal: ollama pull phi3")
            return

    except Exception as e:
        print(f"    ❌ FAILURE: Error checking models: {e}")

    # 3. Test Generation (Raw)
    try:
        print(f"\n[3] Testing simple generation...")
        payload = {
            "model": "phi3",
            "prompt": "Say hello!",
            "stream": False
        }
        response = requests.post(f"{base_url}/api/generate", json=payload)
        result = response.json()
        print(f"    Response: {result.get('response', 'No response')}")
        print("\n    ✅ SUCCESS: Full system is working.")
        
    except Exception as e:
        print(f"    ❌ FAILURE: Generation error: {e}")

if __name__ == "__main__":
    check_ollama()
