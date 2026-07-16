import { Injectable } from '@nestjs/common';
import { OrdersRepository } from './repositories/orders.repository';

@Injectable()
export class OrdersService {
  constructor(private readonly repo: OrdersRepository) {}

  listByUser(userId: string) { return this.repo.findByUser(userId); }
  getById(userId: string, id: string) { return this.repo.findByIdForUser(userId, id); }
}
