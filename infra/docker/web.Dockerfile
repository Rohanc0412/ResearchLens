FROM node:22-bookworm-slim

WORKDIR /workspace

RUN corepack enable

COPY . .

RUN pnpm install --frozen-lockfile=false

CMD ["pnpm", "--filter", "web", "dev", "--host", "0.0.0.0", "--port", "4273"]
