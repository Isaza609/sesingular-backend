import {
  ConflictException,
  Injectable,
  UnauthorizedException,
} from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { ConfigService } from '@nestjs/config';
import * as bcrypt from 'bcryptjs';
import { createHash, randomBytes } from 'crypto';
import { UsersRepository } from '../users/repositories/users.repository';
import { RefreshTokenRepository } from './repositories/refresh-token.repository';
import { RegisterDto } from './schemas/register.schema';
import { LoginDto } from './schemas/login.schema';
import { toAuthUserModel } from './mappers/auth.mapper';

@Injectable()
export class AuthService {
  constructor(
    private readonly users: UsersRepository,
    private readonly refreshTokens: RefreshTokenRepository,
    private readonly jwt: JwtService,
    private readonly config: ConfigService,
  ) {}

  async register(dto: RegisterDto) {
    const existing = await this.users.findByEmail(dto.email);
    if (existing) throw new ConflictException('El email ya está registrado');

    const passwordHash = await bcrypt.hash(dto.password, 10);
    const user = await this.users.create({
      email: dto.email.toLowerCase(),
      name: dto.name,
      phone: dto.phone,
      passwordHash,
    });

    return this.issueTokens(user.id, user.email, user.role);
  }

  async login(dto: LoginDto) {
    const user = await this.users.findByEmail(dto.email.toLowerCase());
    if (!user?.passwordHash) throw new UnauthorizedException('Credenciales inválidas');

    const ok = await bcrypt.compare(dto.password, user.passwordHash);
    if (!ok) throw new UnauthorizedException('Credenciales inválidas');

    return this.issueTokens(user.id, user.email, user.role);
  }

  async refresh(refreshToken: string) {
    const tokenHash = hashToken(refreshToken);
    const stored = await this.refreshTokens.findValid(tokenHash);
    if (!stored) throw new UnauthorizedException('Refresh token inválido');

    await this.refreshTokens.revoke(stored.id);
    return this.issueTokens(stored.user.id, stored.user.email, stored.user.role);
  }

  private async issueTokens(userId: string, email: string, role: string) {
    const accessToken = await this.jwt.signAsync({ sub: userId, email, role });
    const refreshToken = randomBytes(48).toString('hex');
    const days = 7;
    const expiresAt = new Date(Date.now() + days * 24 * 60 * 60 * 1000);

    await this.refreshTokens.create({
      userId,
      tokenHash: hashToken(refreshToken),
      expiresAt,
    });

    const user = await this.users.findById(userId);
    return {
      accessToken,
      refreshToken,
      tokenType: 'Bearer',
      user: user ? toAuthUserModel(user) : null,
    };
  }
}

function hashToken(token: string) {
  return createHash('sha256').update(token).digest('hex');
}
