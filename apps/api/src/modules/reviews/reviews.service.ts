import { Injectable } from '@nestjs/common';
import { ReviewsRepository } from './repositories/reviews.repository';

@Injectable()
export class ReviewsService {
  constructor(private readonly repo: ReviewsRepository) {}

  listByProduct(productId: string) { return this.repo.findApprovedByProduct(productId); }
}
