import { Injectable } from '@nestjs/common';
import { PaymentsRepository } from './repositories/payments.repository';

@Injectable()
export class PaymentsService {
  constructor(private readonly repo: PaymentsRepository) {}

  handleWebhook(provider: string, body: unknown) { return this.repo.recordEvent(provider, body); }
}
