FROM python:3.9-slim
RUN apt-get update && apt-get install -y nginx && apt-get clean && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY nginx.conf /etc/nginx/nginx.conf
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x start.sh
EXPOSE 80
ENV FLASK_ENV=production
CMD ["sh", "-c", "nginx -g 'daemon off;' & ./start.sh"]
