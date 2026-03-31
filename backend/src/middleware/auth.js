import User from '../models/User.js';
import { verifyAccessToken } from '../utils/tokens.js';

export async function requireAuth(req, res, next) {
  const authHeader = req.headers.authorization || '';
  const [scheme, token] = authHeader.split(' ');

  if (scheme !== 'Bearer' || !token) {
    return res.status(401).json({ message: 'Missing or invalid Authorization header' });
  }

  try {
    const payload = verifyAccessToken(token);
    const user = await User.findById(payload.sub).lean();

    if (!user) {
      return res.status(401).json({ message: 'Invalid token user' });
    }

    req.user = {
      id: user._id.toString(),
      email: user.email,
      name: user.name
    };
    next();
  } catch (error) {
    return res.status(401).json({ message: 'Unauthorized' });
  }
}
