import Redis from "ioredis";

const redis = new Redis(process.env.REDIS_URL || "redis://localhost:6379");

export async function getCachedAnswer(question: string) {
  return redis.get(`qa:${question.toLowerCase().trim()}`);
}

export async function setCachedAnswer(question: string, answer: string) {
  await redis.set(`qa:${question.toLowerCase().trim()}`, answer, "EX", 60 * 60 * 24);
}
