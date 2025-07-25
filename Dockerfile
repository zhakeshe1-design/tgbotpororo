# Python 3.11 базалық образ
FROM python:3.11-slim

# ffmpeg тәуелділіктері мен құралдарын орнату
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    curl \
    git \
    && apt-get clean

# Жұмыс директориясы
WORKDIR /app

# Файлдарды көшіру
COPY . .

# Тәуелділіктерді орнату
RUN pip install --no-cache-dir -r requirements.txt

# Ботты іске қосу
CMD ["python", "project/bot.py"]
