import { Injectable } from '@nestjs/common';
import { CheckoutRepository } from './repositories/checkout.repository';
import { CreateCheckoutDto } from './schemas/create-checkout.schema';

@Injectable()
export class CheckoutService {
  constructor(private readonly repo: CheckoutRepository) {}

  create(dto: CreateCheckoutDto) {
    return this.repo.placeholder(dto);
  }
}
