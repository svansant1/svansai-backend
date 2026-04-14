import type { Server as HttpServer } from "http";
import { Server } from "socket.io";

let io: Server | null = null;

export function createSocket(server: HttpServer) {
  io = new Server(server, { cors: { origin: "*" } });
  return io;
}

export function emitStatus(sessionId: string | undefined, stage: string, detail?: string) {
  if (!io || !sessionId) return;
  io.emit("svansai:status", { sessionId, stage, detail, at: new Date().toISOString() });
}
