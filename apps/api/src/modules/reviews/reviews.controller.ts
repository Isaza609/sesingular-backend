import { Controller, Get, Param } from '@nestjs/common';
import { ApiTags } from '@nestjs/swagger';
import { ReviewsService } from './reviews.service';
import { Public } from '../../common';

@ApiTags('reviews')
@Controller()
export class ReviewsController {
  constructor(private readonly service: ReviewsService) {}

  @Public()
  @Get('products/:productId/reviews')
  list(@Param('productId') productId: string) {
    return this.service.listByProduct(productId);
  }
}
