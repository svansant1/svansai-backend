import helmet from "helmet";
import rateLimit from "express-rate-limit";

export const securityHeaders = helmet();

export const limiter = rateLimit({
  windowMs: 60_000,
  max: 120
});
