import mongoose from 'mongoose';

const alertSchema = new mongoose.Schema(
  {
    id: { type: String, required: true, unique: true, index: true },
    title: { type: String, required: true },
    description: { type: String, required: true },
    severity: { type: String, enum: ['critical', 'high', 'medium', 'low'], required: true },
    clusterId: { type: String, default: null },
    timestamp: { type: Date, required: true, default: Date.now },
    status: { type: String, enum: ['new', 'investigating', 'resolved'], default: 'new' },
    pattern: { type: String, enum: ['structuring', 'fragmentation', 'nesting', 'rapid-movement'], default: null },
    confidenceScore: { type: Number, min: 0, max: 1, default: null },
    sanctionsRelated: { type: Boolean, default: false }
  },
  { timestamps: true }
);

export default mongoose.model('Alert', alertSchema);
