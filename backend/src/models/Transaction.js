import mongoose from 'mongoose';

const transactionSchema = new mongoose.Schema(
  {
    id: { type: String, required: true, unique: true, index: true },
    fromAccount: { type: String, required: true, index: true },
    toAccount: { type: String, required: true, index: true },
    amount: { type: Number, required: true, min: 0 },
    channel: { type: String, enum: ['UPI', 'ATM', 'Wallet', 'App', 'Web'], required: true },
    timestamp: { type: Date, required: true, default: Date.now },
    riskScore: { type: Number, required: true, min: 0, max: 100 },
    status: { type: String, enum: ['completed', 'pending', 'flagged'], default: 'completed' },
    pattern: { type: String, enum: ['structuring', 'fragmentation', 'nesting', 'rapid-movement'], default: null },
    complexity: { type: Number, min: 1, max: 10, default: null },
    sanctionsFlag: { type: Boolean, default: false }
  },
  { timestamps: true }
);

export default mongoose.model('Transaction', transactionSchema);
