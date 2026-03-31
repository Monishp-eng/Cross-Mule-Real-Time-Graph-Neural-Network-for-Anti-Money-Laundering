import mongoose from 'mongoose';
import { env } from './env.js';

export async function connectDatabase() {
  await mongoose.connect(env.MONGO_URI);
  console.log(`[db] Connected to MongoDB: ${mongoose.connection.name}`);
}
