import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../../database/prisma.service';

@Injectable()
export class NotificationsRepository {
  constructor(private readonly prisma: PrismaService) {}

  enqueueOrderEmail(orderId: string) {
    return { queued: true, orderId, channel: 'email' };
  }
}
