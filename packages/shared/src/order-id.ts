/** Genera IDs de pedido tipo SG-10429 */
export function formatOrderId(sequence: number): string {
  const padded = String(sequence).padStart(5, '0');
  return `SG-${padded}`;
}

export function parseOrderSequence(orderId: string): number | null {
  const match = /^SG-(\d+)$/.exec(orderId);
  return match ? Number(match[1]) : null;
}
