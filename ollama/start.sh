#!/bin/sh

# Start Ollama in the background
ollama serve &

# Wait for Ollama to start
sleep 5

ollama create marco/em_german_mistral_v01-coherent -f ./app/Modelfile

# Wait the model to be created
sleep 5

ollama run marco/em_german_mistral_v01-coherent