FROM node:22-alpine

ARG FRONTEND_PORT=3000
ARG NODE_ENV=development

ENV FRONTEND_PORT=${FRONTEND_PORT}
ENV NODE_ENV=${NODE_ENV}

WORKDIR /app

RUN chown node:node /app

COPY --chown=node:node package.json package-lock.json ./

USER node

RUN npm install

COPY --chown=node:node . .

EXPOSE ${FRONTEND_PORT}

CMD ["sh", "-c", "npm run dev -- --host 0.0.0.0 --port $FRONTEND_PORT"]
