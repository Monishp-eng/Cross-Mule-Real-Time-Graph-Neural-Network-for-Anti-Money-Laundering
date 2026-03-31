import express from 'express';
import bcrypt from 'bcryptjs';
import { body } from 'express-validator';
import User from '../models/User.js';
import RefreshToken from '../models/RefreshToken.js';
import { validateRequest } from '../middleware/validate.js';
import { signAccessToken, signRefreshToken, verifyRefreshToken } from '../utils/tokens.js';

const router = express.Router();

router.post(
  '/signup',
  body('email').isEmail(),
  body('password').isLength({ min: 6 }),
  validateRequest,
  async (req, res, next) => {
    try {
      const { email, password, name, fullName, organization } = req.body;
      const existing = await User.findOne({ email: email.toLowerCase() }).lean();

      if (existing) {
        return res.status(409).json({ message: 'User already exists' });
      }

      const passwordHash = await bcrypt.hash(password, 10);
      const user = await User.create({
        email: email.toLowerCase(),
        passwordHash,
        name: name || fullName || email.split('@')[0],
        organization: organization || ''
      });

      const token = signAccessToken({ sub: user._id.toString(), email: user.email });
      const refreshToken = signRefreshToken({ sub: user._id.toString(), email: user.email });

      await RefreshToken.create({
        userId: user._id,
        token: refreshToken,
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
      });

      return res.status(201).json({
        token,
        refreshToken,
        user: {
          id: user._id.toString(),
          email: user.email,
          name: user.name,
          organization: user.organization
        }
      });
    } catch (error) {
      return next(error);
    }
  }
);

router.post(
  '/login',
  body('email').isEmail(),
  body('password').isString().notEmpty(),
  validateRequest,
  async (req, res, next) => {
    try {
      const { email, password } = req.body;
      const user = await User.findOne({ email: email.toLowerCase() });

      if (!user) {
        return res.status(401).json({ message: 'Invalid credentials' });
      }

      const matches = await bcrypt.compare(password, user.passwordHash);
      if (!matches) {
        return res.status(401).json({ message: 'Invalid credentials' });
      }

      const token = signAccessToken({ sub: user._id.toString(), email: user.email });
      const refreshToken = signRefreshToken({ sub: user._id.toString(), email: user.email });

      await RefreshToken.create({
        userId: user._id,
        token: refreshToken,
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
      });

      return res.json({
        token,
        refreshToken,
        user: {
          id: user._id.toString(),
          email: user.email,
          name: user.name,
          organization: user.organization
        }
      });
    } catch (error) {
      return next(error);
    }
  }
);

router.post('/refresh', async (req, res, next) => {
  try {
    const incoming = req.body.refresh_token || req.body.refreshToken;
    if (!incoming) {
      return res.status(400).json({ message: 'refresh_token is required' });
    }

    const stored = await RefreshToken.findOne({ token: incoming });
    if (!stored) {
      return res.status(401).json({ message: 'Invalid refresh token' });
    }

    const payload = verifyRefreshToken(incoming);
    const token = signAccessToken({ sub: payload.sub, email: payload.email });

    return res.json({ token });
  } catch (error) {
    return res.status(401).json({ message: 'Invalid or expired refresh token' });
  }
});

router.post('/logout', async (req, res, next) => {
  try {
    const incoming = req.body.refresh_token || req.body.refreshToken;
    if (incoming) {
      await RefreshToken.deleteOne({ token: incoming });
    }
    return res.json({ message: 'Logged out successfully' });
  } catch (error) {
    return next(error);
  }
});

export default router;
