FROM node:18-bullseye-slim

# Install Python 3 & build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/python3 /usr/bin/python

WORKDIR /app

# Copy dependency files
COPY requirements.txt ./
COPY backend/package.json ./backend/
COPY frontend/package.json ./frontend/

# Install python & node dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN cd backend && npm install --production
RUN cd frontend && npm install && npm run build

# Copy codebase
COPY . .

EXPOSE 3000 5001

CMD ["node", "backend/server.js"]
