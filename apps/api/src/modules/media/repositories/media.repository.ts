import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../../database/prisma.service';

@Injectable()
export class MediaRepository {
  constructor(private readonly prisma: PrismaService) {}

  signUpload(dto: { filename: string; contentType: string }) {
    return {
      uploadUrl: null,
      publicUrl: null,
      message: 'Configura S3_* en .env (fase 1)',
      filename: dto.filename,
      contentType: dto.contentType,
    };
  }
}
