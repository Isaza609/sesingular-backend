/** Costos de envío por defecto (COP enteros). Sobreescribibles por env. */
export const DEFAULT_SHIPPING_COST = 12_900;
export const DEFAULT_FREE_SHIPPING_THRESHOLD = 120_000;

export function calcShippingCost(
  subtotal: number,
  shippingCost = DEFAULT_SHIPPING_COST,
  freeThreshold = DEFAULT_FREE_SHIPPING_THRESHOLD,
): number {
  return subtotal >= freeThreshold ? 0 : shippingCost;
}
