import { Injectable } from '@nestjs/common';
import { CartRepository } from './repositories/cart.repository';

@Injectable()
export class CartService {
  constructor(private readonly repo: CartRepository) {}

  getCart(userId?: string, sessionId?: string) { return this.repo.findOrCreate(userId, sessionId); }
}
