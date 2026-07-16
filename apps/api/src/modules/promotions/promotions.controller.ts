import { Controller, Get, Param } from '@nestjs/common';
import { ApiTags } from '@nestjs/swagger';
import { PromotionsService } from './promotions.service';
import { Public } from '../../common';

@ApiTags('promotions')
@Controller('promotions')
export class PromotionsController {
  constructor(private readonly service: PromotionsService) {}

  @Public()
  @Get('coupons/:code')
  validate(@Param('code') code: string) {
    return this.service.validateCoupon(code);
  }
}
