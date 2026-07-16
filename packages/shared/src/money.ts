/** Utilidades de dinero en COP (enteros, sin centavos fraccionarios). */
export function assertCopInteger(amount: number, field = 'amount'): number {
  if (!Number.isInteger(amount) || amount < 0) {
    throw new Error(`${field} debe ser un entero COP >= 0`);
  }
  return amount;
}

export function percentOf(subtotal: number, percent: number): number {
  return Math.round((subtotal * percent) / 100);
}

export function formatCop(amount: number): string {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  }).format(amount);
}
