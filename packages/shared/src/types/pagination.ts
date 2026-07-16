export type PaginationQuery = {
  page?: number;
  pageSize?: number;
};

export type PaginatedResult<T> = {
  items: T[];
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
};

export function normalizePagination(
  query: PaginationQuery,
  defaults = { page: 1, pageSize: 20, maxPageSize: 100 },
): { page: number; pageSize: number; skip: number } {
  const page = Math.max(1, query.page ?? defaults.page);
  const pageSize = Math.min(
    defaults.maxPageSize,
    Math.max(1, query.pageSize ?? defaults.pageSize),
  );
  return { page, pageSize, skip: (page - 1) * pageSize };
}

export function toPaginatedResult<T>(
  items: T[],
  total: number,
  page: number,
  pageSize: number,
): PaginatedResult<T> {
  return {
    items,
    page,
    pageSize,
    total,
    totalPages: Math.max(1, Math.ceil(total / pageSize)),
  };
}
