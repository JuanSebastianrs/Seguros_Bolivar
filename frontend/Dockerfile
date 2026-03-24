FROM node:22-alpine

WORKDIR /app

# Copiar package.json (sin el lockfile de Windows) para evitar fallos de binarios nativos en Linux (musl)
COPY package.json ./
RUN npm install

# Copiar el código fuente
COPY . .

# Exponer el puerto estándar de Vite
EXPOSE 5173

# Arrancar Vite permitiendo conexiones externas (--host)
CMD ["npm", "run", "dev", "--", "--host"]
