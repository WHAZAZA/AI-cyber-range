FROM llm-labs-base:latest

WORKDIR /app

# Copy only the lab-specific app code
COPY labs/LLM07/lab01_insecure_plugin/app /app

ENV LAB_ID=LLM07_lab01_insecure_plugin
ENV PORT=8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
