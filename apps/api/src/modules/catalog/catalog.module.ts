import { Module } from '@nestjs/common';
import { CatalogController } from './catalog.controller';
import { CatalogService } from './catalog.service';
import { ProductsRepository } from './repositories/products.repository';
import { CategoriesRepository } from './repositories/categories.repository';

@Module({
  controllers: [CatalogController],
  providers: [CatalogService, ProductsRepository, CategoriesRepository],
  exports: [CatalogService, ProductsRepository, CategoriesRepository],
})
export class CatalogModule {}
