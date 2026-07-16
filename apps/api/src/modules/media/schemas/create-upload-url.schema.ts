import { IsString, MinLength } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

export class CreateUploadUrlDto {
  @ApiProperty({ example: 'producto.jpg' })
  @IsString()
  @MinLength(3)
  filename!: string;

  @ApiProperty({ example: 'image/jpeg' })
  @IsString()
  contentType!: string;
}
