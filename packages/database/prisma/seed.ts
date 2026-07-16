import { PrismaClient, ProductStatus, Role, CouponType } from '@prisma/client';
import * as bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  const adminEmail = process.env.ADMIN_EMAIL ?? 'admin@sesingular.com';
  const adminPassword = process.env.ADMIN_PASSWORD ?? 'ChangeMeAdmin123!';
  const passwordHash = await bcrypt.hash(adminPassword, 10);

  await prisma.user.upsert({
    where: { email: adminEmail },
    update: {},
    create: {
      email: adminEmail,
      name: 'Admin Singular',
      role: Role.admin,
      passwordHash,
      tier: 'Admin',
    },
  });

  await prisma.orderSequence.upsert({
    where: { id: 1 },
    update: {},
    create: { id: 1, value: 10400 },
  });

  const categories = [
    { slug: 'pulseras', name: 'Pulseras', tagline: 'Para cada día', accent: 'brand', sortOrder: 1 },
    { slug: 'collares', name: 'Collares', tagline: 'Capas y statement', accent: 'candy', sortOrder: 2 },
    { slug: 'aretes', name: 'Aretes', tagline: 'Ligeros y llamativos', accent: 'lime', sortOrder: 3 },
    { slug: 'anillos', name: 'Anillos', tagline: 'Detalles que brillan', accent: 'brand', sortOrder: 4 },
    { slug: 'tobilleras', name: 'Tobilleras', tagline: 'Verano todo el año', accent: 'candy', sortOrder: 5 },
    { slug: 'sets', name: 'Sets & Packs', tagline: 'Combos con descuento', accent: 'lime', sortOrder: 6 },
  ];

  for (const cat of categories) {
    await prisma.category.upsert({
      where: { slug: cat.slug },
      update: cat,
      create: cat,
    });
  }

  await prisma.coupon.upsert({
    where: { code: 'SINGULAR10' },
    update: {},
    create: {
      code: 'SINGULAR10',
      type: CouponType.percent,
      value: 10,
      active: true,
    },
  });

  const pulseras = await prisma.category.findUniqueOrThrow({ where: { slug: 'pulseras' } });

  const product = await prisma.product.upsert({
    where: { slug: 'pulsera-esencia-perla' },
    update: {},
    create: {
      slug: 'pulsera-esencia-perla',
      name: 'Pulsera Esencia Perla',
      categoryId: pulseras.id,
      shortDesc: 'Perlas de río con dijes de millefiori y baño de oro. Hecha a mano.',
      description:
        'Cada Esencia Perla se arma a mano combinando perlas de río con cuentas de vidrio millefiori.',
      type: 'Perlas naturales',
      price: 48900,
      compareAt: 62000,
      badge: 'nuevo',
      bestseller: true,
      status: ProductStatus.published,
      images: {
        create: [{ url: '/products/p1.jpg', sortOrder: 0 }],
      },
      variants: {
        create: [
          { color: 'Perla', sku: 'PUL-ESE-01-PER', stock: 24, reserved: 0, threshold: 10 },
          { color: 'Multicolor', sku: 'PUL-ESE-01-MUL', stock: 12, reserved: 0, threshold: 10 },
          { color: 'Lila', sku: 'PUL-ESE-01-LIL', stock: 8, reserved: 0, threshold: 10 },
        ],
      },
    },
  });

  console.log('Seed OK:', { adminEmail, product: product.slug });
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
