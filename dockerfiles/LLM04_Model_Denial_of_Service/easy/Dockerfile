FROM llm-labs-base:latest

WORKDIR /app

# Copy only the lab-specific app code
COPY labs/LLM04/lab01_resource_exhaustion/app /app

ENV LAB_ID=LLM04_lab01_resource_exhaustion
ENV PORT=8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
