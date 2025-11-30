FROM llm-labs-base:latest

WORKDIR /app

# Copy only the lab-specific app code
COPY labs/LLM03/lab01_poisoned_kb/app /app

ENV LAB_ID=LLM03_lab01_poisoned_kb
ENV PORT=8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
