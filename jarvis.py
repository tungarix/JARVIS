import ollama

def jarvis():
    print("JARVIS hazır! Çıkmak için 'quit' yaz.\n")
    
    messages = []
    
    system_prompt = """Sen JARVIS adında bir yapay zeka asistanısın. 
    Kullanıcının kişisel asistanısın. Türkçe konuşuyorsun.
    Yardımsever, zeki ve samimi davranıyorsun."""
    
    while True:
        user_input = input("Sen: ")
        
        if user_input.lower() == "quit":
            print("JARVIS: Görüşürüz!")
            break
        
        messages.append({"role": "user", "content": user_input})
        
        response = ollama.chat(
            model="qwen2.5:3b",
            messages=[{"role": "system", "content": system_prompt}] + messages
        )
        
        reply = response["message"]["content"]
        messages.append({"role": "assistant", "content": reply})
        
        print(f"JARVIS: {reply}\n")

jarvis()
