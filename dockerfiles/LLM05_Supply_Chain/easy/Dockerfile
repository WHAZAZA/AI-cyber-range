FROM llm-labs-base:latest

WORKDIR /app

# Copy only the lab-specific app code
COPY labs/LLM05/lab01_supply_chain_template/app /app

ENV LAB_ID=LLM05_lab01_supply_chain_template
ENV PORT=8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
