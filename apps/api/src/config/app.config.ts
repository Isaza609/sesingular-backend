import { registerAs } from '@nestjs/config';

export default registerAs('app', () => ({
  name: process.env.APP_NAME ?? 'singular-api',
  port: Number(process.env.APP_PORT ?? 3001),
  prefix: process.env.API_PREFIX ?? 'api/v1',
  corsOrigins: process.env.CORS_ORIGINS ?? 'http://localhost:3000',
  shippingCost: Number(process.env.SHIPPING_COST ?? 12900),
  freeShippingThreshold: Number(process.env.FREE_SHIPPING_THRESHOLD ?? 120000),
  jwt: {
    accessSecret: process.env.JWT_ACCESS_SECRET,
    refreshSecret: process.env.JWT_REFRESH_SECRET,
    accessTtl: process.env.JWT_ACCESS_TTL ?? '15m',
    refreshTtl: process.env.JWT_REFRESH_TTL ?? '7d',
  },
  paymentProvider: process.env.PAYMENT_PROVIDER ?? 'wompi',
}));
