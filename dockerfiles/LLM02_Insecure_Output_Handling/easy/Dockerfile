FROM llm-labs-base:latest

WORKDIR /app

# Copy only the lab-specific app code
COPY labs/LLM02/lab01_insecure_output/app /app

ENV LAB_ID=LLM02_lab01_insecure_output
ENV PORT=8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
