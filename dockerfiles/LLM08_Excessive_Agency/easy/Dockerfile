FROM llm-labs-base:latest

WORKDIR /app

# Copy only the lab-specific app code
COPY labs/LLM08/lab01_excessive_agency/app /app

ENV LAB_ID=LLM08_lab01_excessive_agency
ENV PORT=8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
