FROM llm-labs-base:latest

WORKDIR /app

# Copy only the lab-specific app code
COPY labs/LLM06/lab01_sensitive_disclosure/app /app

ENV LAB_ID=LLM06_lab01_sensitive_disclosure
ENV PORT=8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

