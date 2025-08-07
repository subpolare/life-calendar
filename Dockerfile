FROM node:18-bookworm-slim AS js-build
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 build-essential libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY package*.json ./
RUN npm install --omit=dev
COPY . .

FROM python:3.11-slim-bookworm AS py-build
WORKDIR /app
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

FROM python:3.11-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 libpango-1.0-0 libjpeg62-turbo libgif7 librsvg2-2 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=py-build /install /usr/local
COPY --from=js-build /usr/local/bin/node /usr/local/bin/
COPY --from=js-build /usr/local/bin/npm /usr/local/bin/
COPY --from=js-build /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=js-build /app /app
WORKDIR /app
ENV PATH=/usr/local/bin:$PATH NODE_PATH=/usr/local/lib/node_modules
CMD ["python", "bot.py"]
