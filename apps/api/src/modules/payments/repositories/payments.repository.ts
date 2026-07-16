import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../../database/prisma.service';

@Injectable()
export class PaymentsRepository {
  constructor(private readonly prisma: PrismaService) {}

  async recordEvent(provider: string, body: unknown) {
    const payload = body as { id?: string; data?: { id?: string } };
    const externalId = payload?.id ?? payload?.data?.id ?? `evt-${Date.now()}`;

    return this.prisma.paymentEvent.upsert({
      where: { provider_externalId: { provider, externalId: String(externalId) } },
      update: {},
      create: {
        provider,
        externalId: String(externalId),
        type: 'webhook',
        payload: body as object,
      },
    });
  }
}
