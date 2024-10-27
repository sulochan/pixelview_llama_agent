# pixelview_llama_agent

You will need to have a local llama3 running.
Here we just assume its local

CHATBOT = Agent("localhost", 5000)

To run the agent 

uvicorn main:app --host 0.0.0.0 --port 8080 --reload
