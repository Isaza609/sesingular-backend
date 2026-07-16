import { Controller, Get, Param, Query } from '@nestjs/common';
import { ApiTags } from '@nestjs/swagger';
import { CatalogService } from './catalog.service';
import { ListProductsQueryDto } from './schemas/list-products.schema';
import { Public } from '../../common';

@ApiTags('catalog')
@Controller()
export class CatalogController {
  constructor(private readonly catalog: CatalogService) {}

  @Public()
  @Get('categories')
  categories() {
    return this.catalog.listCategories();
  }

  @Public()
  @Get('products')
  products(@Query() query: ListProductsQueryDto) {
    return this.catalog.listProducts(query);
  }

  @Public()
  @Get('products/:slug')
  product(@Param('slug') slug: string) {
    return this.catalog.getBySlug(slug);
  }

  @Public()
  @Get('products/:slug/related')
  related(@Param('slug') slug: string) {
    return this.catalog.getRelated(slug);
  }
}
