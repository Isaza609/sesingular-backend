import 'dotenv/config';

/**
 * Worker Singular — jobs asíncronos (BullMQ en fases siguientes).
 * Por ahora: proceso stub listo para encolar emails y liberar reservas.
 */
async function bootstrap() {
  console.log(`[worker] Singular worker arrancado (${process.env.NODE_ENV ?? 'development'})`);
  console.log('[worker] Jobs pendientes: release-reservations, send-order-email');
}

bootstrap().catch((err) => {
  console.error(err);
  process.exit(1);
});
