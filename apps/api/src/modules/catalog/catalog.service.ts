import { Injectable, NotFoundException } from '@nestjs/common';
import { ProductsRepository } from './repositories/products.repository';
import { CategoriesRepository } from './repositories/categories.repository';
import { ListProductsQueryDto } from './schemas/list-products.schema';
import { toProductCardModel, toProductDetailModel } from './mappers/product.mapper';
import { toCategoryModel } from './mappers/category.mapper';
import { normalizePagination, toPaginatedResult } from '@singular/shared';

@Injectable()
export class CatalogService {
  constructor(
    private readonly products: ProductsRepository,
    private readonly categories: CategoriesRepository,
  ) {}

  async listCategories() {
    const rows = await this.categories.findActive();
    return rows.map(toCategoryModel);
  }

  async listProducts(query: ListProductsQueryDto) {
    const { page, pageSize, skip } = normalizePagination(query);
    const { items, total } = await this.products.search({
      ...query,
      skip,
      take: pageSize,
    });
    return toPaginatedResult(items.map(toProductCardModel), total, page, pageSize);
  }

  async getBySlug(slug: string) {
    const product = await this.products.findBySlug(slug);
    if (!product || product.status !== 'published' || product.deletedAt) {
      throw new NotFoundException('Producto no encontrado');
    }
    return toProductDetailModel(product);
  }

  async getRelated(slug: string) {
    const product = await this.products.findBySlug(slug);
    if (!product) throw new NotFoundException('Producto no encontrado');
    const related = await this.products.findRelated(product.categoryId, product.id);
    return related.map(toProductCardModel);
  }
}
