import mongoose from 'mongoose';

const clusterSchema = new mongoose.Schema(
  {
    id: { type: String, required: true, unique: true, index: true },
    name: { type: String, required: true },
    accountCount: { type: Number, required: true, min: 0 },
    totalAmount: { type: Number, required: true, min: 0 },
    riskScore: { type: Number, required: true, min: 0, max: 100 },
    detectedAt: { type: Date, required: true, default: Date.now },
    pattern: { type: String, enum: ['structuring', 'fragmentation', 'nesting', 'rapid-movement'], default: null },
    jurisdictions: [{ type: String }],
    confidenceScore: { type: Number, min: 0, max: 1, default: null }
  },
  { timestamps: true }
);

export default mongoose.model('Cluster', clusterSchema);
