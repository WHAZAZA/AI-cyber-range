FROM llm-labs-base:latest

WORKDIR /app

# Copy only the lab-specific app code
COPY labs/LLM09/lab01_overreliance_decision/app /app

ENV LAB_ID=LLM09_lab01_overreliance_decision
ENV PORT=8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

