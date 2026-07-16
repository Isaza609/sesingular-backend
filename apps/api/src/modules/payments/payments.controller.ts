import { Body, Controller, Param, Post } from '@nestjs/common';
import { ApiTags } from '@nestjs/swagger';
import { PaymentsService } from './payments.service';
import { Public } from '../../common';

@ApiTags('payments')
@Controller('webhooks/payments')
export class PaymentsController {
  constructor(private readonly service: PaymentsService) {}

  @Public()
  @Post(':provider')
  handleWebhook(@Param('provider') provider: string, @Body() body: unknown) {
    return this.service.handleWebhook(provider, body);
  }
}
