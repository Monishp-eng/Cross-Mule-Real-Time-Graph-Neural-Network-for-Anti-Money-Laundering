import app from './app.js';
import { env } from './config/env.js';
import { connectDatabase } from './config/db.js';
import { seedDatabase } from './services/seedData.js';

async function start() {
  try {
    await connectDatabase();
    await seedDatabase();

    app.listen(env.PORT, () => {
      console.log(`[server] listening on http://localhost:${env.PORT}`);
    });
  } catch (error) {
    console.error('[server] startup failed', error);
    process.exit(1);
  }
}

start();
