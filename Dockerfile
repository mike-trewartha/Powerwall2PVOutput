# Use a lightweight Python image
FROM python:slim

# Set Python environment variables for better Docker behavior
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file, and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all Python files into the container
COPY PW_Simple.py PW_Config.py PW_Helper.py /app/

# Run the script in an infinite loop
CMD ["python", "/app/PW_Simple.py"]
