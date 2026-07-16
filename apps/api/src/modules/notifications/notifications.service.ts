import { Injectable } from '@nestjs/common';
import { NotificationsRepository } from './repositories/notifications.repository';

@Injectable()
export class NotificationsService {
  constructor(private readonly repo: NotificationsRepository) {}

  sendOrderConfirmation(orderId: string) { return this.repo.enqueueOrderEmail(orderId); }
}
