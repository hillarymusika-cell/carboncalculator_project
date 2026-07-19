FROM python:3.13-slim
WORKDIR /usr/local/app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
EXPOSE 5000
CMD ["python", "src/app.py"]