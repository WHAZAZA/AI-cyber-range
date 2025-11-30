FROM llm-labs-base:latest

WORKDIR /app

# Copy only the lab-specific app code
COPY labs/LLM01/lab01_basic_direct/app /app

ENV LAB_ID=LLM01_lab01_basic_direct
ENV PORT=8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
