import { Injectable } from '@nestjs/common';
import { PromotionsRepository } from './repositories/promotions.repository';

@Injectable()
export class PromotionsService {
  constructor(private readonly repo: PromotionsRepository) {}

  validateCoupon(code: string) { return this.repo.findActiveByCode(code); }
}
