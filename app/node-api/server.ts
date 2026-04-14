import "dotenv/config";
import http from "http";
import express from "express";
import cors from "cors";
import chatRouter from "./routes/chat.js";
import { createSocket } from "./socket.js";
import { limiter, securityHeaders } from "./security.js";
import { logger } from "./logger.js";

const app = express();
app.use(cors());
app.use(express.json({ limit: "2mb" }));
app.use(securityHeaders);
app.use(limiter);

app.get("/health", (_req, res) => {
  res.json({ ok: true, service: "svansai-backend-gateway" });
});

app.use("/api/chat", chatRouter);

const server = http.createServer(app);
createSocket(server);

const port = Number(process.env.PORT || 3001);
server.listen(port, () => {
  logger.info(`SVANSAI backend running on ${port}`);
});
