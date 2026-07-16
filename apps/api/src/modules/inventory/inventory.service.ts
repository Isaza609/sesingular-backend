import { Injectable } from '@nestjs/common';
import { InventoryRepository } from './repositories/inventory.repository';

@Injectable()
export class InventoryService {
  constructor(private readonly repo: InventoryRepository) {}

  list() { return this.repo.list(); }
}
