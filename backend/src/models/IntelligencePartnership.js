import mongoose from 'mongoose';

const intelligencePartnershipSchema = new mongoose.Schema(
  {
    id: { type: String, required: true, unique: true, index: true },
    partner: { type: String, required: true },
    clusterIds: [{ type: String, required: true }],
    accountsShared: { type: Number, required: true, min: 0 },
    confidenceScore: { type: Number, required: true, min: 0, max: 1 },
    status: { type: String, enum: ['active', 'pending', 'pending-review'], default: 'pending' },
    sharedAt: { type: Date, default: Date.now }
  },
  { timestamps: true }
);

export default mongoose.model('IntelligencePartnership', intelligencePartnershipSchema);
