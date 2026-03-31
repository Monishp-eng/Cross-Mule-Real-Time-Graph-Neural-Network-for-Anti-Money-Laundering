import mongoose from 'mongoose';

const accountSchema = new mongoose.Schema(
  {
    id: { type: String, required: true, unique: true, index: true },
    name: { type: String, required: true },
    riskScore: { type: Number, required: true, min: 0, max: 100 },
    type: { type: String, enum: ['suspicious', 'normal', 'high-risk'], required: true },
    channels: [{ type: String, required: true }],
    balance: { type: Number, required: true, min: 0 },
    clusterId: { type: String, default: null },
    jurisdiction: { type: String, default: 'Unknown' },
    owner: { type: String, default: 'Unknown' },
    confidenceScore: { type: Number, min: 0, max: 1, default: null },
    sanctionsMatch: { type: Boolean, default: false }
  },
  { timestamps: true }
);

export default mongoose.model('Account', accountSchema);
