# 1. Asosiy imaj - Python 3.11
FROM python:3.11-slim

# 2. Node.js va pnpm ni o'rnatish
RUN apt-get update && apt-get install -y curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g pnpm \
    && apt-get clean

# 3. Ishchi papkani belgilash
WORKDIR /app

# 4. Barcha fayllarni konteynerga nusxalash
COPY . /app

# 5. Python kutubxonalarini o'rnatish
RUN pip install --no-cache-dir -r requirements.txt

# 6. React (Next.js) ni build qilish
RUN cd frontend && pnpm install && pnpm build

# 7. Serverni ishga tushirish
CMD ["python", "main.py"]
